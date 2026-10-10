"""Contrat de pagination/tri standard."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


def parse_sort(sort: str | None, whitelist: dict[str, object], default: str) -> list:
    """Retourne une liste de clauses ORDER BY à partir d'un tri 'champ:asc,champ2:desc'."""
    if not sort:
        return [whitelist[default].asc()]
    clauses = []
    for token in sort.split(","):
        token = token.strip()
        if not token:
            continue
        field, _, direction = token.partition(":")
        field = field.strip()
        if field not in whitelist:
            continue
        col = whitelist[field]
        clauses.append(col.desc() if direction.lower() == "desc" else col.asc())
    return clauses or [whitelist[default].asc()]