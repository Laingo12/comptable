"""Tests parser LAINGO v0.1 (Étape 1)."""
import pytest
from laingo.ast import nodes as A
from laingo.lexer_parser.errors import LaingoSyntaxError
from laingo.lexer_parser.parser import parse


def test_print_basic():
    p = parse('mamoaka("Salama")')
    (s,) = p.statements
    assert isinstance(s, A.Print)
    assert isinstance(s.value, A.String) and s.value.value == "Salama"


def test_assign_untyped():
    p = parse("x = 42")
    (s,) = p.statements
    assert isinstance(s, A.Assign)
    assert s.name == "x" and s.type_name is None
    assert s.value.value == 42 and s.value.kind == "Isa"


def test_assign_typed():
    p = parse("x: Isa = 42")
    (s,) = p.statements
    assert s.name == "x" and s.type_name == "Isa"
    assert s.value.kind == "Isa"


def test_desimaly():
    p = parse("pi: Desimaly = 3.14")
    (s,) = p.statements
    assert s.value.kind == "Desimaly" and s.value.value == 3.14


def test_bool_literals():
    p = parse("a = Marina\nb = Diso")
    a, b = p.statements
    assert a.value.value is True and b.value.value is False


def test_binop_precedence():
    p = parse("y = 1 + 2 * 3")
    (s,) = p.statements
    top = s.value
    assert isinstance(top, A.BinOp) and top.op == "+"
    assert isinstance(top.right, A.BinOp) and top.right.op == "*"


def test_unary_minus():
    p = parse("x = -5")
    (s,) = p.statements
    assert isinstance(s.value, A.UnaryOp) and s.value.op == "-"


def test_compare():
    p = parse("b = 3 >= 2")
    (s,) = p.statements
    assert isinstance(s.value, A.Compare) and s.value.op == ">="


def test_if_elif_else():
    src = (
        "raha Marina:\n"
        "    mamoaka(1)\n"
        "raha_tsy_izany Marina:\n"
        "    mamoaka(2)\n"
        "raha_tsy_izany:\n"
        "    mamoaka(3)\n"
    )
    p = parse(src)
    (s,) = p.statements
    assert isinstance(s, A.If)
    assert len(s.elifs) == 2
    assert s.elifs[0][0] is not None       # elif
    assert s.elifs[1][0] is None           # else


def test_while():
    src = "rehefa Marina:\n    mamoaka(1)\n"
    p = parse(src)
    (s,) = p.statements
    assert isinstance(s, A.While)


def test_func_def_with_params():
    src = "asa f(a: Isa, b: Isa) -> Isa:\n    avereno a + b\n"
    p = parse(src)
    (s,) = p.statements
    assert isinstance(s, A.FuncDef)
    assert s.name == "f" and s.ret_type == "Isa"
    assert s.params == [("a", "Isa"), ("b", "Isa")]


def test_func_def_no_params():
    src = "asa g() -> Isa:\n    avereno 1\n"
    p = parse(src)
    (s,) = p.statements
    assert s.params == []


def test_call_zero_one_two_args():
    p = parse("a = f()\nb = f(1)\nc = f(1, 2)")
    a, b, c = p.statements
    assert len(a.value.args) == 0
    assert len(b.value.args) == 1
    assert len(c.value.args) == 2


def test_nested_call():
    src = 'mamoaka(ampiana(katroa(2), 10))\n'
    p = parse(src)
    (s,) = p.statements
    outer = s.value
    assert isinstance(outer, A.Call) and outer.func == "ampiana"
    assert isinstance(outer.args[0], A.Call) and outer.args[0].func == "katroa"


def test_comment_ignored():
    p = parse('mamoaka("Salama") // fiarahaba\n')
    assert len(p.statements) == 1


def test_syntax_error_has_line():
    with pytest.raises(LaingoSyntaxError) as ei:
        parse('mamoaka("Salama"\nx = 1\n')
    assert ei.value.line >= 1
    assert "LAINGO" in str(ei.value)


def test_print_requires_argument():
    # mamoaka() tsy misy argument → erreur syntaxe amin'ity étape ity.
    with pytest.raises(LaingoSyntaxError):
        parse("mamoaka()\n")