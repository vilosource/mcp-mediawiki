import os
import sys
from dotenv import load_dotenv
import mwclient
from mcp.server.fastmcp import FastMCP
import uvicorn

# Add debug logging
print("Starting MCP MediaWiki server")
print(f"Python version: {sys.version}")

# Load environment variables from .env file
print("Loading .env file")
load_dotenv()

HOST = os.getenv("MW_API_HOST", "wiki.example.com")
PATH = os.getenv("MW_API_PATH", "/wiki/")
USE_HTTPS = os.getenv("MW_USE_HTTPS", "true").lower() == "true"
BOT_USER = os.getenv("MW_BOT_USER")
BOT_PASS = os.getenv("MW_BOT_PASS")

print(f"Configuration: HOST={HOST}, PATH={PATH}, HTTPS={USE_HTTPS}")
print(f"Bot user: {BOT_USER}")

SCHEME = "https" if USE_HTTPS else "http"


def get_site() -> mwclient.Site:
    site = mwclient.Site(host=HOST, path=PATH, scheme=SCHEME)
    if BOT_USER and BOT_PASS:
        site.login(BOT_USER, BOT_PASS)
    return site


site = get_site()

# Mount the Streamable HTTP server at the root path so VS Code can
# communicate with the server without additional configuration.
mcp = FastMCP("mcp_mediawiki", streamable_http_path="/")


@mcp.resource("wiki://{title}")
def get_page(title: str):
    page = site.pages[title]
    if not page.exists:
        return {"error": f"Page '{title}' not found"}
    return {
        "@id": f"wiki://{title}",
        "@type": "Document",
        "name": title,
        "content": page.text(),
        "metadata": {
            "url": f"{SCHEME}://{HOST}{PATH}index.php/{title}",
            "last_modified": next(page.revisions())['timestamp'],
            "namespace": page.namespace,
        },
    }


@mcp.tool(description="Create or edit a page with the provided content")
def update_page(title: str, content: str, summary: str):
    """Create or update a wiki page."""
    page = site.pages[title]
    page.save(text=content, summary=summary)
    return {
        "status": "success",
        "title": title,
        "url": f"{SCHEME}://{HOST}/wiki/{title}",
    }


app = mcp.streamable_http_app()


if __name__ == "__main__":
    print("Starting MCP server with uvicorn...")
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        print(f"Error running MCP server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
