"""Lexer + Parser LAINGO v0.1 → AST."""
from __future__ import annotations
from pathlib import Path

from lark import Lark, Transformer
from lark.exceptions import LarkError, UnexpectedInput, VisitError
from lark.indenter import Indenter

from laingo.ast import nodes as A
from laingo.lexer_parser.errors import LaingoSyntaxError, LaingoError


class _LaingoIndenter(Indenter):
    NL_type = "_NL"
    OPEN_PAREN_types = []
    CLOSE_PAREN_types = []
    INDENT_type = "_INDENT"
    DEDENT_type = "_DEDENT"
    tab_len = 8


_GRAMMAR_FILE = Path(__file__).resolve().parents[3] / "grammar" / "laingo.lark"
if not _GRAMMAR_FILE.exists():  # pragma: no cover
    raise RuntimeError(
        f"Tsy hita ny grammar: {_GRAMMAR_FILE}\n"
        "Ataovy 'pip install -e .' avy amin'ny fakan'ny projet."
    )

_parser = Lark(
    _GRAMMAR_FILE.read_text(encoding="utf-8"),
    start="start",
    parser="lalr",
    postlex=_LaingoIndenter(),
    propagate_positions=True,
)


class _ToAST(Transformer):
    """Mamadika ny parse tree ho AST node (dataclasses)."""

    # ----- programme -----
    def start(self, children):
        return A.Program(statements=list(children), line=0)

    # ----- statements -----
    def assignment(self, children):
        name_tok = children[0]
        if len(children) == 2:
            return A.Assign(name=str(name_tok), type_name=None,
                            value=children[1], line=name_tok.line)
        return A.Assign(name=str(name_tok), type_name=str(children[1]),
                        value=children[2], line=name_tok.line)

    def print_stmt(self, children):
        (val,) = children
        return A.Print(value=val, line=val.line)

    def return_stmt(self, children):
        (val,) = children
        return A.Return(value=val, line=val.line)

    def if_stmt(self, children):
        cond = children[0]
        body = children[1]
        elifs = list(children[2:])
        return A.If(cond=cond, body=body, elifs=elifs, line=cond.line)

    def raha_tsy_izany_branch(self, children):
        if len(children) == 1:
            return (None, children[0])
        return (children[0], children[1])

    def while_stmt(self, children):
        cond, body = children
        return A.While(cond=cond, body=body, line=cond.line)

    def func_def(self, children):
        name_tok = children[0]
        rest = children[1:]
        if len(rest) == 3:
            params, ret_type, suite = rest[0], rest[1], rest[2]
        else:
            params, ret_type, suite = [], rest[0], rest[1]
        if params is None:
            params = []
        return A.FuncDef(name=str(name_tok), params=list(params),
                         ret_type=str(ret_type), body=suite,
                         line=name_tok.line)

    def params(self, children):
        return list(children)

    def param(self, children):
        name_tok, type_tok = children
        return (str(name_tok), str(type_tok))

    def suite(self, children):
        return list(children)

    def type_ref(self, children):
        return str(children[0])

    # ----- expressions -----
    def number(self, children):
        (tok,) = children
        text = str(tok)
        if "." in text:
            return A.Number(value=float(text), kind="Desimaly", line=tok.line)
        return A.Number(value=int(text), kind="Isa", line=tok.line)

    def string(self, children):
        (tok,) = children
        return A.String(value=str(tok)[1:-1], line=tok.line)

    def marina(self, children):
        line = children[0].line if children else 0
        return A.Bool(value=True, line=line)

    def diso(self, children):
        line = children[0].line if children else 0
        return A.Bool(value=False, line=line)

    def name(self, children):
        (tok,) = children
        return A.Name(id=str(tok), line=tok.line)

    def call(self, children):
        name_tok = children[0]
        args = children[1] if len(children) > 1 else None
        args = list(args) if args else []
        return A.Call(func=str(name_tok), args=args, line=name_tok.line)

    def args(self, children):
        return list(children)

    def add(self, c): return self._bin("+", c)
    def sub(self, c): return self._bin("-", c)
    def mul(self, c): return self._bin("*", c)
    def div(self, c): return self._bin("/", c)

    def neg(self, c):
        (operand,) = c
        return A.UnaryOp(op="-", operand=operand, line=operand.line)

    def or_(self, c):
        left, right = c
        return A.LogicalOp(op="na", left=left, right=right, line=left.line)

    def and_(self, c):
        left, right = c
        return A.LogicalOp(op="ary", left=left, right=right, line=left.line)

    def not_(self, c):
        (operand,) = c
        return A.NotOp(operand=operand, line=operand.line)

    def cmp_expr(self, children):
        # 1 enfant  : pas de comparaison (ne devrait pas arriver si ?cmp_expr).
        # 3 enfants : comparaison simple.
        # 5+        : comparaison en chaîne -> erreur syntaxique claire.
        if len(children) == 1:
            return children[0]
        if len(children) == 3:
            left, op_tok, right = children
            return A.Compare(op=str(op_tok), left=left, right=right,
                             line=left.line)
        first = children[0]
        raise LaingoSyntaxError(
            "tsy azo atao ny fampitahana mifamatotra (ohatra: a < b < c). "
            "Sokafy amin'ny « ary » na « na » : ohatra « a < b ary b < c »",
            line=first.line,
        )

    @staticmethod
    def _bin(op, c):
        left, right = c
        return A.BinOp(op=op, left=left, right=right, line=left.line)


def parse(source: str) -> A.Program:
    """Mamaky code LAINGO ho AST (Program).

    Raises:
        LaingoSyntaxError: raha misy erreur syntaxique (misy laharana).
    """
    if source:
        source = source.rstrip() + "\n"
    else:
        source = "\n"

    try:
        tree = _parser.parse(source)
    except UnexpectedInput as e:
        raise LaingoSyntaxError.from_lark(e, source) from e
    except LarkError as e:
        raise LaingoSyntaxError(str(e), line=0) from e

    try:
        return _ToAST().transform(tree)
    except VisitError as e:
        inner = getattr(e, "orig_exc", e)
        if isinstance(inner, LaingoError):
            raise inner from e
        raise LaingoSyntaxError(str(inner), line=0) from e