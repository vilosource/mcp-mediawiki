import os
from dotenv import load_dotenv
import mwclient
from mcp.server.fastmcp import FastMCP

load_dotenv()

HOST = os.getenv("MW_API_HOST", "wiki.example.com")
PATH = os.getenv("MW_API_PATH", "/wiki/")
USE_HTTPS = os.getenv("MW_USE_HTTPS", "true").lower() == "true"
BOT_USER = os.getenv("MW_BOT_USER")
BOT_PASS = os.getenv("MW_BOT_PASS")
WRITE_TOKEN = os.getenv("MW_WRITE_TOKEN")

SCHEME = "https" if USE_HTTPS else "http"


def get_site() -> mwclient.Site:
    site = mwclient.Site(host=HOST, path=PATH, scheme=SCHEME)
    if BOT_USER and BOT_PASS:
        site.login(BOT_USER, BOT_PASS)
    return site


site = get_site()

mcp = FastMCP("mcp_mediawiki")


@mcp.resource("wiki://{title}")
def get_page(title: str):
    page = site.pages[title]
    if not page.exists:
        return {"error": f"Page '{title}' not found"}
    return {
        "id": f"wiki:{title}",
        "name": title,
        "content": page.text(),
        "metadata": {
            "url": f"{SCHEME}://{HOST}{PATH}index.php/{title}",
            "last_modified": next(page.revisions())['timestamp'],
            "namespace": page.namespace,
        },
    }


@mcp.tool()
def update_page(title: str, content: str, summary: str, token: str):
    if WRITE_TOKEN and token != WRITE_TOKEN:
        raise PermissionError("Invalid write token")
    page = site.pages[title]
    page.save(text=content, summary=summary)
    return {
        "status": "success",
        "title": title,
        "url": f"{SCHEME}://{HOST}/wiki/{title}",
    }


if __name__ == "__main__":
    mcp.run()
