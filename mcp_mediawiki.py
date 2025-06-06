import os
import sys
import time
import logging
from typing import Annotated, List, Dict
from datetime import datetime

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
    title: Annotated[str, Field(min_length=1, description="Wiki page title")]
    content: Annotated[str, Field(description="Wikitext content to save")]
    summary: Annotated[str, Field(description="Edit summary")]
    dry_run: Annotated[bool, Field(False, description="Preview the edit without saving")]


class SearchPagesInput(BaseModel):
    query: Annotated[str, Field(min_length=1, description="Title keyword to search for")]


class PageHistoryInput(BaseModel):
    title: Annotated[str, Field(min_length=1, description="Page title")]
    limit: Annotated[int, Field(5, ge=1, le=50, description="Number of revisions to fetch")]


class PageMetadata(BaseModel):
    url: str
    last_modified: str  # ISO 8601
    namespace: int
    length: int
    protection: Dict[str, List[str]]
    categories: List[str]


class PageInfo(BaseModel):
    title: str
    content: str
    metadata: PageMetadata


# Mount the Streamable HTTP server at /mcp
mcp = FastMCP("mcp_mediawiki", streamable_http_path="/mcp")


@mcp.tool(description="Retrieve the full content and metadata of a MediaWiki page.")
def get_page(title: str) -> PageInfo:
    logger.info("get_page tool called", extra={"title": title})
    page = site.pages[title]
    if not page.exists:
        raise ValueError(f"Page '{title}' not found")

    first_rev = next(page.revisions())
    categories = [c.name for c in page.categories()]
    last_modified = first_rev["timestamp"]
    if isinstance(last_modified, time.struct_time):
        last_modified = datetime(*last_modified[:6]).isoformat()

    return PageInfo(
        title=title,
        content=page.text(),
        metadata=PageMetadata(
            url=f"{SCHEME}://{HOST}{PATH}index.php/{title}",
            last_modified=last_modified,
            namespace=page.namespace,
            length=page.length,
            protection=page.protection,
            categories=categories,
        )
    )


@mcp.tool(description="Create or edit a page with the provided content. \u26a0\ufe0f Use ONLY when explicitly asked to save new content.")
def update_page(
    title: str,
    content: str,
    summary: str,
    dry_run: bool = False,
):
    logger.info("update_page called", extra={"title": title, "summary": summary})
    params = UpdatePageInput(
        title=title, content=content, summary=summary, dry_run=dry_run
    )

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
    params = SearchPagesInput(query=query)
    logger.info("search_pages called", extra=params.model_dump())
    results = site.search(params.query, limit=limit)
    return [
        {"title": r["title"], "snippet": r.get("snippet")}
        for r in results
    ]


@mcp.tool(description="Get basic server configuration and version info")
def server_status():
    logger.info("server_status called")
    version = site.site_info.get("generator")
    return {
        "host": HOST,
        "path": PATH,
        "scheme": SCHEME,
        "mediawiki_version": version,
    }


@mcp.tool(description="Get the wiki page revision history")
def get_page_history(title: str, limit: int = 5):
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
