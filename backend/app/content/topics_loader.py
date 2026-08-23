"""Learning-content loading for topics, sections, quizzes and glossary.

Topic packs live at ``content/topics/<topic_id>/topic.yaml`` plus a
``sections/`` folder of markdown files whose numeric filename prefix defines
reading order and whose first ``# `` heading is the section title.

Validation is loud: any malformed pack aborts startup with every violation
listed (same philosophy as the component catalog).
"""

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.core.config import default_content_dir


class TopicError(RuntimeError):
    """Raised when a topic pack or glossary fails validation."""


_TOPIC_REQUIRED = {"id", "title", "category", "order", "summary", "objectives"}
_QUIZ_ITEM_REQUIRED = {"q", "options", "answer"}
_SECTION_PREFIX_RE = re.compile(r"^(\d{2})-([a-z0-9-]+)\.md$")


def _load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _parse_section(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8").strip()
    match = _SECTION_PREFIX_RE.match(path.name)
    if not match:
        raise TopicError(f"  bad section filename '{path.name}' (expected NN-slug.md)")
    order = int(match.group(1))
    slug = f"{match.group(1)}-{match.group(2)}"
    lines = text.splitlines()
    title = None
    body_lines = list(lines)
    if lines and lines[0].startswith("# "):
        title = lines[0][2:].strip()
        body_lines = lines[1:]
    if not title:
        raise TopicError(f"  section '{path.name}' must start with a '# ' heading")
    return {
        "slug": slug,
        "title": title,
        "order": order,
        "content_md": "\n".join(body_lines).strip(),
    }


def scan_topics(content_dir: Path) -> dict[str, dict[str, Any]]:
    """Load and validate every topic pack. Returns topic_id -> assembled topic."""
    topics_dir = content_dir / "topics"
    if not topics_dir.is_dir():
        raise TopicError(f"missing topics directory: {topics_dir}")

    raw_by_id: dict[str, tuple[Path, dict[str, Any]]] = {}
    errors: list[str] = []

    for pack_dir in sorted(p for p in topics_dir.iterdir() if p.is_dir()):
        meta_path = pack_dir / "topic.yaml"
        if not meta_path.is_file():
            errors.append(f"  {pack_dir.name}: missing topic.yaml")
            continue
        meta = _load_yaml(meta_path)
        if not isinstance(meta, dict):
            errors.append(f"  {pack_dir.name}: topic.yaml must be a mapping")
            continue
        missing = [key for key in _TOPIC_REQUIRED if key not in meta]
        if missing:
            errors.append(f"  {meta_path}: missing fields {missing}")
            continue
        tid = str(meta["id"])
        if tid != pack_dir.name:
            errors.append(f"  {meta_path}: id '{tid}' does not match folder name '{pack_dir.name}'")
        if tid in raw_by_id:
            errors.append(f"  duplicate topic id '{tid}'")
        sections_dir = pack_dir / "sections"
        sections: list[dict[str, Any]] = []
        if not sections_dir.is_dir():
            errors.append(f"  {pack_dir.name}: missing sections/ directory")
        else:
            for path in sorted(sections_dir.glob("*.md")):
                try:
                    sections.append(_parse_section(path))
                except TopicError as exc:  # noqa: PERF203 - collect-all-errors loop
                    errors.append(str(exc))
        sections.sort(key=lambda s: int(s["order"]))
        meta["sections"] = sections
        meta["_dir"] = pack_dir
        quiz = meta.get("quiz") or []
        for idx, item in enumerate(quiz):
            item_missing = [k for k in _QUIZ_ITEM_REQUIRED if k not in item]
            if item_missing:
                errors.append(f"  {meta_path}: quiz[{idx}] missing fields {item_missing}")
            elif not isinstance(item.get("answer"), int) or not (
                0 <= item["answer"] < len(item.get("options") or [])
            ):
                errors.append(f"  {meta_path}: quiz[{idx}] answer index out of range")
        raw_by_id[tid] = (meta_path, meta)

    # Cross-topic checks: prerequisites and related challenges must resolve.
    known_ids = set(raw_by_id)
    challenges_dir = content_dir / "challenges"
    known_challenges: set[str] = set()
    if challenges_dir.is_dir():
        known_challenges = {
            p.stem.removesuffix(".solution") for p in challenges_dir.glob("*.yaml")
        }
    for tid, (_, meta) in raw_by_id.items():
        for prereq in meta.get("prerequisites") or []:
            if prereq not in known_ids:
                errors.append(f"  topic '{tid}': unknown prerequisite '{prereq}'")
        for chal in meta.get("related_challenges") or []:
            if known_challenges and chal not in known_challenges:
                errors.append(f"  topic '{tid}': unknown related challenge '{chal}'")

    if errors:
        raise TopicError("Invalid learning content:\n" + "\n".join(errors))

    topics: dict[str, dict[str, Any]] = {}
    for tid, (_, meta) in raw_by_id.items():
        meta.pop("_dir", None)
        topics[tid] = meta
    return topics


@lru_cache(maxsize=1)
def load_topics() -> dict[str, dict[str, Any]]:
    return scan_topics(default_content_dir())


def list_topic_summaries() -> list[dict[str, Any]]:
    out = []
    for topic in load_topics().values():
        out.append(
            {
                "id": topic["id"],
                "title": topic["title"],
                "category": topic["category"],
                "order": topic["order"],
                "summary": topic["summary"],
                "prerequisites": topic.get("prerequisites") or [],
                "related_challenges": topic.get("related_challenges") or [],
                "section_slugs": [s["slug"] for s in topic["sections"]],
                "section_titles": [s["title"] for s in topic["sections"]],
                "quiz_count": len(topic.get("quiz") or []),
            }
        )
    out.sort(key=lambda t: t["order"])
    return out


def get_topic(topic_id: str) -> dict[str, Any] | None:
    return load_topics().get(topic_id)


def search_content(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Case-insensitive substring search across topic titles, summaries, bodies."""
    needle = query.strip().lower()
    if not needle:
        return []
    results: list[dict[str, Any]] = []
    for topic in load_topics().values():
        haystacks: list[tuple[str, str, str]] = [
            ("title", topic["id"], str(topic["title"])),
            ("summary", topic["id"], str(topic["summary"])),
        ]
        for section in topic["sections"]:
            haystacks.append(("section", f"{topic['id']}#{section['slug']}", section["content_md"]))
        for kind, ref, text in haystacks:
            pos = text.lower().find(needle)
            if pos == -1:
                continue
            start = max(0, pos - 60)
            snippet = text[start : pos + 120].replace("\n", " ").strip()
            prefix = "…" if start > 0 else ""
            suffix = "…" if start + 180 < len(text) else ""
            results.append(
                {
                    "kind": kind,
                    "topic_id": topic["id"],
                    "ref": ref,
                    "snippet": f"{prefix}{snippet}{suffix}",
                }
            )
            if len(results) >= limit * 2:
                break
        if len(results) >= limit * 2:
            break
    return results[:limit]


def load_glossary() -> list[dict[str, Any]]:
    path = default_content_dir() / "glossary.yaml"
    data = _load_yaml(path)
    if not isinstance(data, list):
        raise TopicError(f"{path}: glossary.yaml must be a list of term entries")
    terms = []
    errors: list[str] = []
    for idx, entry in enumerate(data):
        if not isinstance(entry, dict) or not {"term", "definition"} <= set(entry):
            errors.append(f"  glossary[{idx}] requires 'term' and 'definition'")
            continue
        terms.append({"term": str(entry["term"]), "definition": str(entry["definition"])})
    if errors:
        raise TopicError("Invalid glossary:\n" + "\n".join(errors))
    terms.sort(key=lambda t: t["term"].lower())
    return terms
