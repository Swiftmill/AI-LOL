from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.facts import find_fact, load_facts, save_fact
from core.ontology import get_ontology
from core.pipeline import handle_message
from core.rules import add_rule, load_rules
from core.index import get_index
from core.search import ddg_search, fetch_many
from core.store import DATA_DIR, log_event, read_json, write_json
from core.summarize import summarize_texts

app = FastAPI(title="AI Local")

origins = [
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path(__file__).resolve().parent / "ui"
app.mount("/", StaticFiles(directory=static_dir, html=True), name="ui")


@app.get("/health")
def health() -> Dict[str, bool]:
    return {"ok": True}


@app.post("/chat")
def chat(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    message = payload.get("message")
    if not message:
        raise HTTPException(status_code=400, detail="message requis")
    allow_web = bool(payload.get("allow_web", False))
    result = handle_message(str(message), allow_web)
    log_event("chat", {"message": message, "allow_web": allow_web, "intent": result.get("intent")})
    return result


@app.post("/rules")
def create_rule(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    if_text = payload.get("if_text")
    reply_text = payload.get("reply_text")
    if not if_text or not reply_text:
        raise HTTPException(status_code=400, detail="if_text et reply_text requis")
    record = add_rule(str(if_text), str(reply_text))
    log_event("rule_created", record)
    return record


@app.get("/rules")
def list_rules() -> Dict[str, Any]:
    return {"items": load_rules()}


@app.get("/aliases")
def list_aliases() -> Dict[str, Any]:
    return {"items": get_ontology().aliases}


@app.post("/search")
def forced_search(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    query = payload.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="query requis")
    log_event("forced_search", {"query": query})
    results = ddg_search(query)
    pages = fetch_many([item["href"] for item in results])
    summary = summarize_texts(pages, question=query)
    sources = [page.get("url") for page in pages if page.get("url")] [:3]
    saved = save_fact(str(query), summary, sources)
    get_index().add(saved["topic"], summary)
    return {"summary": summary, "sources": sources, "topic": saved.get("topic"), "learned": True}


@app.get("/facts")
def get_fact(topic: Optional[str] = None) -> Dict[str, Any]:
    if topic:
        fact = find_fact(topic)
        if not fact:
            raise HTTPException(status_code=404, detail="Fact inconnue")
        return fact
    return {"items": load_facts()}


MEMORY_PATH = DATA_DIR / "memory" / "profile.json"


@app.get("/memory")
def get_memory() -> Dict[str, Any]:
    return read_json(MEMORY_PATH, {"name": "Invité", "preferences": {}})


@app.post("/memory")
def set_memory(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    write_json(MEMORY_PATH, payload)
    log_event("memory_updated", payload)
    return payload


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)

