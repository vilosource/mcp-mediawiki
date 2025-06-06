import os
import sys
import logging
from typing import Annotated

from dotenv import load_dotenv
import mwclient
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Startup logs
logger.info("Starting MCP MediaWiki server")
logger.info(f"Python version: {sys.version}")

# Load environment variables from .env file
logger.info("Loading .env file")
load_dotenv()

HOST = os.getenv("MW_API_HOST", "wiki.example.com")
PATH = os.getenv("MW_API_PATH", "/wiki/")
USE_HTTPS = os.getenv("MW_USE_HTTPS", "true").lower() == "true"
BOT_USER = os.getenv("MW_BOT_USER")
BOT_PASS = os.getenv("MW_BOT_PASS")

logger.info(f"Configuration: HOST={HOST}, PATH={PATH}, HTTPS={USE_HTTPS}")
logger.info(f"Bot user: {BOT_USER}")

SCHEME = "https" if USE_HTTPS else "http"


def get_site() -> mwclient.Site:
    site = mwclient.Site(host=HOST, path=PATH, scheme=SCHEME)
    if BOT_USER and BOT_PASS:
        site.login(BOT_USER, BOT_PASS)
    return site


site = get_site()


class UpdatePageInput(BaseModel):
    """Input model for updating or creating a page."""

    title: Annotated[str, Field(min_length=1, description="Wiki page title")]
    content: Annotated[str, Field(description="Wikitext content to save")]
    summary: Annotated[str, Field(description="Edit summary")]
    dry_run: Annotated[bool, Field(False, description="Preview the edit without saving")]


class SearchPagesInput(BaseModel):
    query: Annotated[str, Field(min_length=1, description="Title keyword to search for")]


class PageHistoryInput(BaseModel):
    title: Annotated[str, Field(min_length=1, description="Page title")]
    limit: Annotated[int, Field(5, ge=1, le=50, description="Number of revisions to fetch")]

# Mount the Streamable HTTP server at /mcp so the root path can
# return a simple JSON health response for VS Code and other tools.
mcp = FastMCP("mcp_mediawiki", streamable_http_path="/mcp")


@mcp.resource("wiki://{title}")
def get_page(title: str):
    """Return the full wikitext and metadata for a page."""
    logger.info("get_page called", extra={"title": title})
    page = site.pages[title]
    if not page.exists:
        return {"error": f"Page '{title}' not found"}

    categories = [c.name for c in page.categories()]
    info = {
        "@id": f"wiki://{title}",
        "@type": "Document",
        "name": title,
        "content": page.text(),
        "metadata": {
            "url": f"{SCHEME}://{HOST}{PATH}index.php/{title}",
            "last_modified": next(page.revisions())["timestamp"],
            "namespace": page.namespace,
            "length": page.length,
            "protection": page.protection,
            "categories": categories,
        },
    }
    return info


@mcp.tool(description="Create or edit a page with the provided content")
def update_page(
    title: str,
    content: str,
    summary: str,
    dry_run: bool = False,
):
    """Create or update a wiki page."""
    params = UpdatePageInput(
        title=title, content=content, summary=summary, dry_run=dry_run
    )
    logger.info("update_page called", extra=params.model_dump())

    if params.dry_run:
        return {
            "status": "dry-run",
            "title": params.title,
            "content": params.content,
            "summary": params.summary,
        }

    page = site.pages[params.title]
    page.save(text=params.content, summary=params.summary)
    return {
        "status": "success",
        "title": params.title,
        "url": f"{SCHEME}://{HOST}/wiki/{params.title}",
    }


@mcp.tool(description="Search wiki pages by title keyword")
def search_pages(query: str, limit: int = 5):
    """Search pages by title."""
    params = SearchPagesInput(query=query)
    logger.info("search_pages called", extra=params.model_dump())
    results = site.search(params.query, limit=limit)
    return [
        {"title": r["title"], "snippet": r.get("snippet")}
        for r in results
    ]


@mcp.tool(description="Get basic server configuration and version info")
def server_status():
    """Return server configuration details."""
    logger.info("server_status called")
    version = site.site_info.get("generator")
    return {
        "host": HOST,
        "path": PATH,
        "scheme": SCHEME,
        "mediawiki_version": version,
    }


@mcp.tool(description="Get the last N revisions of a page")
def get_page_history(title: str, limit: int = 5):
    """Return recent revision history for a page."""
    params = PageHistoryInput(title=title, limit=limit)
    logger.info("get_page_history called", extra=params.model_dump())
    page = site.pages[params.title]
    if not page.exists:
        return {"error": f"Page '{params.title}' not found"}
    revisions = [
        {
            "revid": rev.get("revid"),
            "user": rev.get("user"),
            "timestamp": rev.get("timestamp"),
            "comment": rev.get("comment"),
        }
        for rev in page.revisions(limit=params.limit)
    ]
    return revisions


app = mcp.streamable_http_app()


@app.route("/", methods=["GET"])
async def root(request) -> JSONResponse:
    """Return server health information."""
    logger.info("root endpoint called")
    return JSONResponse(
        {
            "status": "ok",
            "server": "mcp-mediawiki",
            "streamable_http_path": "/mcp",
        }
    )


if __name__ == "__main__":
    logger.info("Starting MCP server with uvicorn...")
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        logger.exception(f"Error running MCP server: {e}")
        sys.exit(1)
