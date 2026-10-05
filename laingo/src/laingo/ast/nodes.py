"""AST nodes LAINGO v0.1 — tsotra, tsy misy dépendance ivelany."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple


@dataclass
class Node:
    """Fototra ho an'ny nœuds rehetra. `line` = laharana (1-based)."""
    line: int = 0


# ----------------------------- Statements ---------------------------------
@dataclass
class Program(Node):
    statements: List[Node] = field(default_factory=list)


@dataclass
class Assign(Node):
    """x = expr (réaffectation/inférence) | x: T = expr (déclaration)."""
    name: str = ""
    type_name: Optional[str] = None
    value: Optional[Node] = None


@dataclass
class Print(Node):
    value: Optional[Node] = None


@dataclass
class Return(Node):
    value: Optional[Node] = None


@dataclass
class If(Node):
    """raha cond: ... (raha_tsy_izany …: ...)*. cond=None => else."""
    cond: Optional[Node] = None
    body: List[Node] = field(default_factory=list)
    elifs: List[Tuple[Optional[Node], List[Node]]] = field(default_factory=list)


@dataclass
class While(Node):
    cond: Optional[Node] = None
    body: List[Node] = field(default_factory=list)


@dataclass
class FuncDef(Node):
    name: str = ""
    params: List[Tuple[str, str]] = field(default_factory=list)
    ret_type: str = ""
    body: List[Node] = field(default_factory=list)


# ----------------------------- Expressions --------------------------------
@dataclass
class Number(Node):
    value: Any = 0
    kind: str = "Isa"   # "Isa" | "Desimaly"


@dataclass
class String(Node):
    value: str = ""


@dataclass
class Bool(Node):
    value: bool = False


@dataclass
class Name(Node):
    id: str = ""


@dataclass
class BinOp(Node):
    op: str = ""        # + - * /
    left: Optional[Node] = None
    right: Optional[Node] = None


@dataclass
class Compare(Node):
    op: str = ""        # == != < > <= >=
    left: Optional[Node] = None
    right: Optional[Node] = None


@dataclass
class UnaryOp(Node):
    op: str = "-"
    operand: Optional[Node] = None


@dataclass
class LogicalOp(Node):
    """« ary » (and) | « na » (or). Court-circuit. Deux opérandes Marina."""
    op: str = ""        # "ary" | "na"
    left: Optional[Node] = None
    right: Optional[Node] = None


@dataclass
class NotOp(Node):
    """« tsy » (not) — Marina ihany ny opérande, miverina Marina."""
    operand: Optional[Node] = None


@dataclass
class Call(Node):
    func: str = ""
    args: List[Node] = field(default_factory=list)


__all__ = [
    "Node", "Program", "Assign", "Print", "Return", "If", "While", "FuncDef",
    "Number", "String", "Bool", "Name", "BinOp", "Compare", "UnaryOp",
    "LogicalOp", "NotOp", "Call",
]