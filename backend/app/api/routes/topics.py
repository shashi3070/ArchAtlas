"""Learning content API: topics, sections, quizzes, glossary, search."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.content import topics_loader

router = APIRouter(prefix="/api", tags=["learn"])


@router.get("/topics")
def list_topics() -> list[dict[str, Any]]:
    return topics_loader.list_topic_summaries()


@router.get("/topics/{topic_id}")
def get_topic(topic_id: str) -> dict[str, Any]:
    topic = topics_loader.get_topic(topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail=f"Unknown topic '{topic_id}'")
    related = [
        {"id": t["id"], "title": t["title"]}
        for t in topics_loader.list_topic_summaries()
        if t["id"] in (topic.get("prerequisites") or [])
    ]
    return {**topic, "prerequisite_topics": related}


@router.get("/glossary")
def glossary() -> list[dict[str, Any]]:
    return topics_loader.load_glossary()


@router.get("/search")
def search(
    q: str = Query(min_length=1, max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
) -> dict[str, Any]:
    return {"query": q, "results": topics_loader.search_content(q, limit)}
