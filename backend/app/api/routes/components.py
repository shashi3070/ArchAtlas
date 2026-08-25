"""Component catalog API.

Serves the seeded, schema-validated component catalog from content/.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.content import loader

router = APIRouter(prefix="/api", tags=["components"])


@router.get("/components")
async def list_components() -> list[dict[str, Any]]:
    return loader.list_components()


@router.get("/components/{ctype}")
async def get_component(ctype: str) -> dict[str, Any]:
    entry = loader.get_component(ctype)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown component type '{ctype}'",
        )
    return entry


@router.get("/components/{ctype}/guide")
async def get_component_guide(ctype: str) -> dict[str, Any]:
    guide = loader.get_guide(ctype)
    if guide is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No guide available for component type '{ctype}'",
        )
    return guide
