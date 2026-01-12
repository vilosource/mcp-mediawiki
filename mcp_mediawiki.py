"""MCP MediaWiki Server - Model Context Protocol server for MediaWiki integration.

Supports multiple transport modes: stdio, sse, streamable-http
"""

import asyncio
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List

import click
import mwclient
from dotenv import load_dotenv
from fastmcp import FastMCP
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp-mediawiki")


# =============================================================================
# Configuration
# =============================================================================

class WikiConfig:
    """MediaWiki configuration from environment variables."""

    def __init__(self):
        self.host = os.getenv("MW_API_HOST", "wiki.example.com")
        self.path = os.getenv("MW_API_PATH", "/wiki/")
        self.use_https = os.getenv("MW_USE_HTTPS", "true").lower() == "true"
        self.bot_user = os.getenv("MW_BOT_USER")
        self.bot_pass = os.getenv("MW_BOT_PASS")
        self.scheme = "https" if self.use_https else "http"

    def is_auth_configured(self) -> bool:
        """Check if bot authentication is configured."""
        return bool(self.bot_user and self.bot_pass)

    def __repr__(self) -> str:
        return f"WikiConfig(host={self.host}, path={self.path}, scheme={self.scheme}, auth={self.is_auth_configured()})"


# =============================================================================
# Wiki Client with Per-Request Connections
# =============================================================================

class WikiClient:
    """MediaWiki client that creates fresh connections per request.

    This ensures session reliability by avoiding stale authentication state.
    """

    def __init__(self, config: WikiConfig):
        self.config = config
        self._connection_count = 0

    def get_site(self) -> mwclient.Site:
        """Get a fresh, authenticated MediaWiki site connection.

        Returns:
            Authenticated mwclient.Site instance
        """
        self._connection_count += 1
        logger.debug(f"Creating MediaWiki connection #{self._connection_count}")

        site = mwclient.Site(
            host=self.config.host,
            path=self.config.path,
            scheme=self.config.scheme,
        )

        if self.config.is_auth_configured():
            try:
                site.login(self.config.bot_user, self.config.bot_pass)
                logger.debug(f"Logged in as: {site.username}")
            except Exception as e:
                logger.error(f"Login failed: {e}")
                raise

        return site

    def test_connection(self) -> dict:
        """Test the MediaWiki connection and return status."""
        try:
            site = self.get_site()
            version = None
            if hasattr(site, "site_info"):
                version = site.site_info.get("generator")
            elif hasattr(site, "site"):
                version = site.site.get("generator")

            return {
                "status": "ok",
                "host": self.config.host,
                "path": self.config.path,
                "scheme": self.config.scheme,
                "mediawiki_version": version,
                "logged_in": site.logged_in if hasattr(site, "logged_in") else None,
                "username": site.username if hasattr(site, "username") else None,
            }
        except Exception as e:
            return {
                "status": "error",
                "host": self.config.host,
                "error": str(e),
            }


# =============================================================================
# Pydantic Models
# =============================================================================

class PageMetadata(BaseModel):
    """Metadata for a wiki page."""
    url: str
    last_modified: str
    namespace: int
    length: int
    protection: Dict[str, List[str]]
    categories: List[str]


class PageInfo(BaseModel):
    """Full page information including content and metadata."""
    title: str
    content: str
    metadata: PageMetadata


class UpdatePageResponse(BaseModel):
    """Response from page update operation."""
    status: str
    title: str
    url: str | None = None
    content: str | None = None
    summary: str | None = None


# =============================================================================
# FastMCP Server Setup
# =============================================================================

# Initialize configuration and client
config = WikiConfig()
wiki_client = WikiClient(config)

# Create FastMCP server
mcp = FastMCP(
    "mcp-mediawiki",
    instructions="MediaWiki MCP server for searching and retrieving wiki content.",
)


class WikiPageNotFoundError(Exception):
    """Raised when a wiki page is not found."""
    pass


class WikiOperationError(Exception):
    """Raised when a wiki operation fails."""
    pass


@mcp.tool(description="Retrieve the full content and metadata of a MediaWiki page.")
def get_page(title: str) -> PageInfo:
    """Get a wiki page by title.

    Args:
        title: The exact title of the wiki page

    Returns:
        PageInfo with content and metadata

    Raises:
        WikiPageNotFoundError: If the page doesn't exist
        WikiOperationError: If there's an error accessing the wiki
    """
    logger.info(f"get_page called: title={title}")

    try:
        site = wiki_client.get_site()
        page = site.pages[title]

        if not page.exists:
            logger.warning(f"Page not found: {title}")
            raise WikiPageNotFoundError(f"Page '{title}' not found")

        first_rev = next(page.revisions())
        categories = [c.name for c in page.categories()]
        last_modified = first_rev["timestamp"]

        if isinstance(last_modified, time.struct_time):
            last_modified = datetime(*last_modified[:6]).isoformat()

        return PageInfo(
            title=title,
            content=page.text(),
            metadata=PageMetadata(
                url=f"{config.scheme}://{config.host}{config.path}index.php/{title}",
                last_modified=last_modified,
                namespace=page.namespace,
                length=page.length,
                protection=page.protection,
                categories=categories,
            ),
        )
    except WikiPageNotFoundError:
        raise  # Re-raise our custom exception
    except Exception as e:
        logger.error(f"Error getting page '{title}': {e}")
        raise WikiOperationError(f"Failed to get page '{title}': {e}")


@mcp.tool(
    description="Create or edit a wiki page. Use ONLY when explicitly asked to save content."
)
def update_page(
    title: str,
    content: str,
    summary: str,
    dry_run: bool = False,
) -> UpdatePageResponse:
    """Save a new version of a MediaWiki page.

    Args:
        title: The exact name of the page to update
        content: Full wikitext content (must be MediaWiki format, not Markdown)
        summary: Edit summary shown in the page history
        dry_run: If true, preview the update without saving

    Returns:
        UpdatePageResponse with status

    Raises:
        WikiOperationError: If there's an error updating the page
    """
    logger.info(f"update_page called: title={title}, summary={summary}, dry_run={dry_run}")

    if dry_run:
        return UpdatePageResponse(
            status="dry-run",
            title=title,
            content=content,
            summary=summary,
        )

    try:
        site = wiki_client.get_site()
        page = site.pages[title]
        page.save(text=content, summary=summary)

        return UpdatePageResponse(
            status="success",
            title=title,
            url=f"{config.scheme}://{config.host}{config.path}index.php/{title}",
        )
    except Exception as e:
        logger.error(f"Error updating page '{title}': {e}")
        raise WikiOperationError(f"Failed to update page '{title}': {e}")


@mcp.tool(description="Search wiki pages by title keyword")
def search_pages(
    query: str = Field(description="Search query string"),
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results to return"),
) -> dict:
    """Search for wiki pages matching a query.

    Args:
        query: Search query string
        limit: Maximum number of results (1-50)

    Returns:
        Dict with 'results' list containing matching pages with title and snippet

    Raises:
        WikiOperationError: If there's an error searching the wiki
    """
    logger.info(f"search_pages called: query={query}, limit={limit}")

    try:
        site = wiki_client.get_site()
        results = site.search(query, limit=limit)

        pages = [{"title": r["title"], "snippet": r.get("snippet")} for r in results]
        return {
            "results": pages,
            "total": len(pages),
            "query": query,
        }
    except Exception as e:
        logger.error(f"Error searching for '{query}': {e}")
        raise WikiOperationError(f"Failed to search wiki: {e}")


@mcp.tool(description="Get the revision history of a wiki page")
def get_page_history(
    title: str = Field(description="Page title"),
    limit: int = Field(default=5, ge=1, le=50, description="Number of revisions to fetch"),
) -> list:
    """Get the revision history of a wiki page.

    Args:
        title: The exact title of the wiki page
        limit: Number of revisions to fetch (1-50)

    Returns:
        List of revisions with user, timestamp, and comment

    Raises:
        WikiPageNotFoundError: If the page doesn't exist
        WikiOperationError: If there's an error accessing the wiki
    """
    logger.info(f"get_page_history called: title={title}, limit={limit}")

    try:
        site = wiki_client.get_site()
        page = site.pages[title]

        if not page.exists:
            raise WikiPageNotFoundError(f"Page '{title}' not found")

        revisions = [
            {
                "revid": rev.get("revid"),
                "user": rev.get("user"),
                "timestamp": rev.get("timestamp"),
                "comment": rev.get("comment"),
            }
            for rev in page.revisions(limit=limit)
        ]
        return revisions
    except WikiPageNotFoundError:
        raise  # Re-raise our custom exception
    except Exception as e:
        logger.error(f"Error getting history for '{title}': {e}")
        raise WikiOperationError(f"Failed to get page history for '{title}': {e}")


@mcp.tool(description="Get MediaWiki server status and configuration info")
def server_status() -> dict:
    """Get server configuration and connection status.

    Returns:
        Server status including host, version, and auth state
    """
    logger.info("server_status called")
    return wiki_client.test_connection()


# =============================================================================
# Custom HTTP Routes (for health checks)
# =============================================================================

@mcp.custom_route("/", methods=["GET"])
async def root_handler(request):
    """Root endpoint for health checks."""
    from starlette.responses import JSONResponse
    return JSONResponse({
        "status": "ok",
        "server": "mcp-mediawiki",
        "version": "0.2.0",
        "transport": "sse",
    })


@mcp.custom_route("/health", methods=["GET"])
async def health_handler(request):
    """Health check endpoint."""
    from starlette.responses import JSONResponse
    status = wiki_client.test_connection()
    return JSONResponse(status)


# =============================================================================
# CLI Entry Point
# =============================================================================

@click.command()
@click.option(
    "-v", "--verbose",
    count=True,
    help="Increase verbosity (can be used multiple times)",
)
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse", "streamable-http"]),
    default="stdio",
    help="Transport type (stdio, sse, or streamable-http)",
)
@click.option(
    "--port",
    default=8000,
    help="Port for SSE or Streamable HTTP transport",
)
@click.option(
    "--host",
    default="0.0.0.0",
    help="Host to bind to for SSE or Streamable HTTP transport",
)
@click.option(
    "--path",
    default=None,
    help="Path for Streamable HTTP transport (default: /mcp)",
)
@click.version_option(version="0.2.0", prog_name="mcp-mediawiki")
def main(
    verbose: int,
    transport: str,
    port: int,
    host: str,
    path: str | None,
):
    """MCP MediaWiki Server - Access MediaWiki via Model Context Protocol.

    Examples:

        # Run with stdio (default, for Claude Desktop)
        mcp-mediawiki

        # Run with SSE transport (for ATLAS)
        mcp-mediawiki --transport sse --port 8000

        # Run with Streamable HTTP
        mcp-mediawiki --transport streamable-http --port 8000 --path /mcp
    """
    # Configure logging level
    if verbose >= 2:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    elif verbose == 1:
        logging.getLogger().setLevel(logging.INFO)
        logger.setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)
        logger.setLevel(logging.INFO)

    # Log startup info
    logger.info("=" * 60)
    logger.info("MCP MediaWiki Server starting")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Configuration: {config}")
    logger.info(f"Transport: {transport}")
    logger.info("=" * 60)

    # Test connection on startup
    status = wiki_client.test_connection()
    if status["status"] == "ok":
        logger.info(f"Connected to MediaWiki: {status.get('mediawiki_version')}")
        if status.get("logged_in"):
            logger.info(f"Authenticated as: {status.get('username')}")
        else:
            logger.warning("Not authenticated - some operations may fail")
    else:
        logger.error(f"Connection test failed: {status.get('error')}")

    # Build run kwargs
    run_kwargs = {"transport": transport}

    if transport == "stdio":
        logger.info("Starting with stdio transport")
    elif transport in ("sse", "streamable-http"):
        run_kwargs["host"] = host
        run_kwargs["port"] = port

        if path is not None:
            run_kwargs["path"] = path

        # Determine display path
        if transport == "sse":
            display_path = "/sse"
        else:
            display_path = path or "/mcp"

        logger.info(f"Starting with {transport.upper()} transport on http://{host}:{port}{display_path}")

    # Run the server
    try:
        asyncio.run(mcp.run_async(**run_kwargs))
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.exception(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
