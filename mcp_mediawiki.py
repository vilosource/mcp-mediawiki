import os
import argparse
import sys
from dotenv import load_dotenv
import mwclient
from mcp.server.fastmcp import FastMCP

# Add debug logging
print("Starting MCP MediaWiki server")
print(f"Python version: {sys.version}")

# Parse command line arguments
parser = argparse.ArgumentParser(description='MediaWiki MCP Server')
parser.add_argument('--api-host', help='MediaWiki API host')
parser.add_argument('--api-path', help='MediaWiki API path')
parser.add_argument('--username', help='MediaWiki bot username')
parser.add_argument('--password', help='MediaWiki bot password')
parser.add_argument('--use-https', choices=['true', 'false'], help='Use HTTPS for connections')
args = parser.parse_args()

# Load environment variables from .env file
print("Loading .env file")
load_dotenv()

# Command line args override environment variables
HOST = args.api_host or os.getenv("MW_API_HOST", "wiki.example.com")
PATH = args.api_path or os.getenv("MW_API_PATH", "/wiki/")
USE_HTTPS = args.use_https if args.use_https else os.getenv("MW_USE_HTTPS", "true").lower() == "true"
BOT_USER = args.username or os.getenv("MW_BOT_USER")
BOT_PASS = args.password or os.getenv("MW_BOT_PASS")

print(f"Configuration: HOST={HOST}, PATH={PATH}, HTTPS={USE_HTTPS}")
print(f"Bot user: {BOT_USER}")

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


@mcp.tool()
def update_page(title: str, content: str, summary: str):
    page = site.pages[title]
    page.save(text=content, summary=summary)
    return {
        "status": "success",
        "title": title,
        "url": f"{SCHEME}://{HOST}/wiki/{title}",
    }


if __name__ == "__main__":
    print("Starting MCP server...")
    try:
        print("Running mcp.run()")
        # By default, FastMCP's run() method blocks, keeping the server running
        # Make sure to use host='0.0.0.0' so it's accessible from outside the container
        mcp.run(host='0.0.0.0', port=8000)
        # This should not be reached unless the server shuts down
        print("Server has shut down.")
    except Exception as e:
        print(f"Error running MCP server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
