from __future__ import annotations

from typing import Dict

from .facts import fuzzy_lookup, save_fact
from .index import get_index
from .nlu import get_nlu
from .ontology import get_ontology
from .rules import match_rule
from .search import ddg_search, fetch_many
from .store import log_event
from .summarize import summarize_texts


def handle_message(message: str, allow_web: bool) -> Dict[str, object]:
    ontology = get_ontology()
    nlu = get_nlu()
    response: Dict[str, object] = {
        "answer": "",
        "sources": [],
        "learned": False,
        "intent": "UNKNOWN",
        "topic": None,
    }

    alias_candidate = ontology.extract(message)
    if alias_candidate:
        source, target, confidence = alias_candidate
        if confidence >= 0.9:
            response["answer"] = f"Je retiens : {source.strip()} → {target.strip()}"
            response["intent"] = "ALIAS_LEARN"
            response["topic"] = source.strip().lower()
            log_event("alias_learned", {"source": source, "target": target, "confidence": confidence})
            return response
        else:
            response["answer"] = f"Je pense que {source} signifie {target}, confirme-moi."
            response["intent"] = "ALIAS_LEARN"
            response["topic"] = source.strip().lower()
            return response

    intent, score = nlu.detect_intent(message)
    response["intent"] = intent
    slots = nlu.infer_slots(message)
    topic = slots.get("topic") or message
    response["topic"] = topic

    rule = match_rule(message)
    if rule:
        response["answer"] = str(rule.get("reply", ""))
        log_event("rule_match", {"if": rule.get("if"), "reply": rule.get("reply")})
        return response

    normalized = ontology.normalize(message)
    fact = fuzzy_lookup(normalized)
    if fact:
        response["answer"] = str(fact.get("summary", ""))
        response["sources"] = fact.get("sources", [])
        response["intent"] = intent if intent != "UNKNOWN" else "FACT_RESPONSE"
        return response

    if not allow_web:
        response["answer"] = "Je ne sais pas encore. Voulez-vous que je cherche ?"
        return response

    log_event("web_search", {"query": message})
    results = ddg_search(message)
    urls = [item["href"] for item in results]
    pages = fetch_many(urls)
    if not pages:
        response["answer"] = "Je n'ai rien trouvé de fiable."
        return response
    summary = summarize_texts(pages, question=message)
    sources = [page.get("url") for page in pages if page.get("url")] [:3]
    saved = save_fact(topic or message, summary, sources)
    get_index().add(saved["topic"], summary)
    response["topic"] = saved["topic"]
    response["answer"] = summary or "Je n'ai pas pu résumer les résultats."
    response["sources"] = sources
    response["learned"] = True
    response["intent"] = intent if intent != "UNKNOWN" else "WEB_LEARN"
    return response

