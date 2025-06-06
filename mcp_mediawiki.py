import os
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from dotenv import load_dotenv
import mwclient

load_dotenv()

HOST = os.getenv("MW_API_HOST", "wiki.example.com")
PATH = os.getenv("MW_API_PATH", "/wiki/")
USE_HTTPS = os.getenv("MW_USE_HTTPS", "true").lower() == "true"
BOT_USER = os.getenv("MW_BOT_USER")
BOT_PASS = os.getenv("MW_BOT_PASS")
WRITE_TOKEN = os.getenv("MW_WRITE_TOKEN", "secret-token")

SCHEME = "https" if USE_HTTPS else "http"


def get_site() -> mwclient.Site:
    site = mwclient.Site((SCHEME, HOST), path=PATH)
    if BOT_USER and BOT_PASS:
        site.login(BOT_USER, BOT_PASS)
    return site

site = get_site()

app = FastAPI(title="MCP MediaWiki Server")


class WritePayload(BaseModel):
    title: str
    content: str
    summary: str


@app.get("/v1/context")
def get_page(title: str):
    page = site.pages[title]
    if not page.exists:
        raise HTTPException(status_code=404, detail="Page not found")
    text = page.text()
    return [
        {
            "id": f"wiki:{page.page_title}",
            "name": page.page_title,
            "content": text,
            "metadata": {
                "source": HOST,
                "url": f"{SCHEME}://{HOST}{PATH}{page.page_title}",
                "last_modified": page.last_edit[0] if page.last_edit else None,
                "namespace": page.namespace,
            },
        }
    ]


@app.get("/v1/search")
def search(query: str):
    results = site.search(query)
    return [
        {"title": r["title"], "snippet": r.get("snippet")}
        for r in results
    ]


@app.post("/v1/write")
def write_page(payload: WritePayload, Authorization: str = Header(None)):
    if Authorization != f"Bearer {WRITE_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    page = site.pages[payload.title]
    page.save(text=payload.content, summary=payload.summary)
    return {
        "status": "success",
        "revision_id": page.revision,
        "url": f"{SCHEME}://{HOST}{PATH}{page.page_title}",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
