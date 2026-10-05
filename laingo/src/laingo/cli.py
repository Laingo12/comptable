"""CLI LAINGO v0.1 — parse + hamarino."""
from __future__ import annotations

import argparse
import sys
from dataclasses import is_dataclass
from pathlib import Path

from laingo.lexer_parser.errors import LaingoError
from laingo.lexer_parser.parser import parse
from laingo.checker.typechecker import check


def format_ast(node, indent: int = 0) -> str:
    """Manonta AST amin'ny endrika mora vakiana (indenté)."""
    pad = "  " * indent
    if isinstance(node, list):
        if not node:
            return "[]"
        items = ",\n".join(f"{pad}  {format_ast(x, indent + 1)}" for x in node)
        return "[\n" + items + f"\n{pad}]"
    if isinstance(node, tuple):
        return "(" + ", ".join(format_ast(x, indent) for x in node) + ")"
    if is_dataclass(node) and not isinstance(node, type):
        cls = type(node).__name__
        fields = []
        for f in node.__dataclass_fields__:
            v = getattr(node, f)
            if isinstance(v, (list, tuple)) or (
                is_dataclass(v) and not isinstance(v, type)
            ):
                sub = format_ast(v, indent + 1)
                fields.append(f"{pad}  {f}={sub.lstrip()}")
            else:
                fields.append(f"{pad}  {f}={v!r}")
        if not fields:
            return f"{cls}()"
        return f"{cls}(\n" + ",\n".join(fields) + f"\n{pad})"
    return repr(node)


def _read(path: Path) -> str:
    if not path.exists():
        print(f"[LAINGO] Tsy hita ny rakitra: {path}", file=sys.stderr)
        sys.exit(2)
    return path.read_text(encoding="utf-8")


def cmd_parse(args) -> int:
    src = _read(Path(args.file))
    try:
        prog = parse(src)
    except LaingoError as e:
        print(str(e), file=sys.stderr)
        return 1
    print(format_ast(prog))
    return 0


def cmd_hamarino(args) -> int:
    src = _read(Path(args.file))
    try:
        prog = parse(src)
        check(prog)
    except LaingoError as e:
        print(str(e), file=sys.stderr)
        return 1
    print(f"Tsara: {args.file}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="laingo", description="CLI LAINGO (v0.1)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("parse", help="Mamaky .laingo ary manonta ny AST")
    sp.add_argument("file", help="Rakitra .laingo")
    sp.set_defaults(func=cmd_parse)

    sp = sub.add_parser("hamarino",
                        help="Mamaky + manamarina ny type (Étape 2)")
    sp.add_argument("file", help="Rakitra .laingo")
    sp.set_defaults(func=cmd_hamarino)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())