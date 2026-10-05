"""Tests type checker LAINGO v0.2 (Étape 2)."""
import pytest
from laingo.ast import nodes as A
from laingo.checker.typechecker import check, TypeInfo
from laingo.lexer_parser.errors import LaingoTypeError, LaingoSyntaxError
from laingo.lexer_parser.parser import parse


def tc(src):
    return check(parse(src))


# ----------------------- variables / inférence -----------------------
def test_inference_first_assign():
    info = tc("x = 5\n")
    assert any(True for _ in info.assigns.values())
    # assign 'x' Isa, declaration True
    assign = next(iter(info.assigns.values()))
    assert assign.ctype == "Isa" and assign.declaration is True


def test_reassign_same_type_ok():
    tc("x = 5\nx = 6\n")


def test_reassign_promote_isa_to_desimaly():
    # x: Desimaly ; x = 5 (Isa) reste OK par promotion.
    tc("x: Desimaly = 1.0\nx = 5\n")


def test_reassign_downgrade_error():
    with pytest.raises(LaingoTypeError):
        tc("x: Desimaly = 1.0\nx = 5\nx: Isa = 5\n")  # redéclaration


def test_reassign_type_mismatch():
    with pytest.raises(LaingoTypeError):
        tc("x = 5\nx = 1.5\n")


def test_undeclared_variable():
    with pytest.raises(LaingoTypeError):
        tc("mamoaka(z)\n")


def test_typed_decl_mismatch():
    with pytest.raises(LaingoTypeError):
        tc('x: Isa = "abc"\n')


# ----------------------- arithmétique / promotion -----------------------
def test_promotion_in_binop():
    # 1 + 2.0 -> Desimaly. On vérifie que ça ne lève pas.
    tc("x = 1 + 2.0\n")


def test_binop_on_string_error():
    with pytest.raises(LaingoTypeError):
        tc('x = "a" + 1\n')


def test_unary_minus_on_string_error():
    with pytest.raises(LaingoTypeError):
        tc('x = -"a"\n')


# ----------------------- comparaisons -----------------------
def test_compare_numeric_ok():
    tc("r = 1 < 2\n")
    tc("r = 1.0 <= 2\n")


def test_compare_string_lt_error():
    with pytest.raises(LaingoTypeError):
        tc('r = "a" < "b"\n')


def test_compare_string_eq_error():
    # En v0.2 : == sur Teksta n'est pas autorisé (concat/strcmp plus tard).
    with pytest.raises(LaingoTypeError):
        tc('r = "a" == "b"\n')


def test_compare_bool_eq_ok():
    tc("r = Marina == Diso\n")


# ----------------------- logiques -----------------------
def test_logical_ok():
    tc("r = Marina ary Diso\n")
    tc("r = Marina na Diso\n")
    tc("r = tsy Marina\n")


def test_logical_on_int_error():
    with pytest.raises(LaingoTypeError):
        tc("r = 1 ary 2\n")


def test_not_on_int_error():
    with pytest.raises(LaingoTypeError):
        tc("r = tsy 1\n")


def test_no_implicit_int_to_bool():
    # « raha 1: » doit échouer (pas de conversion Isa -> Marina).
    with pytest.raises(LaingoTypeError):
        tc("raha 1:\n    mamoaka(1)\n")


# ----------------------- conditions -----------------------
def test_if_condition_must_be_bool():
    with pytest.raises(LaingoTypeError):
        tc('raha "x":\n    mamoaka(1)\n')


def test_while_condition_must_be_bool():
    with pytest.raises(LaingoTypeError):
        tc("rehefa 1:\n    mamoaka(1)\n")


# ----------------------- fonctions -----------------------
def test_function_call_ok():
    tc("asa f(a: Isa) -> Isa:\n    avereno a\nmamoaka(f(1))\n")


def test_function_wrong_arg_count():
    with pytest.raises(LaingoTypeError):
        tc("asa f(a: Isa) -> Isa:\n    avereno a\nmamoaka(f())\n")


def test_function_wrong_arg_type():
    with pytest.raises(LaingoTypeError):
        tc('asa f(a: Isa) -> Isa:\n    avereno a\nmamoaka(f("x"))\n')


def test_function_promote_arg_isa_to_desimaly():
    tc("asa f(a: Desimaly) -> Desimaly:\n    avereno a\nmamoaka(f(1))\n")


def test_function_no_return_error():
    with pytest.raises(LaingoTypeError):
        tc("asa f() -> Isa:\n    mamoaka(1)\n")


def test_function_return_type_mismatch():
    with pytest.raises(LaingoTypeError):
        tc('asa f() -> Isa:\n    avereno "x"\n')


def test_duplicate_function_error():
    with pytest.raises(LaingoTypeError):
        tc("asa f() -> Isa:\n    avereno 1\nasa f() -> Isa:\n    avereno 1\n")


# ----------------------- structure -----------------------
def test_else_not_last():
    src = ("raha Marina:\n    mamoaka(1)\n"
           "raha_tsy_izany:\n    mamoaka(2)\n"
           "raha_tsy_izany Marina:\n    mamoaka(3)\n")
    with pytest.raises(LaingoTypeError):
        tc(src)


def test_block_scoped_variable():
    # « x » déclaré dans le bloc if ne fuit pas à l'extérieur.
    src = "raha Marina:\n    x = 5\nmamoaka(x)\n"
    with pytest.raises(LaingoTypeError):
        tc(src)


def test_return_outside_function():
    with pytest.raises(LaingoTypeError):
        tc("avereno 1\n")