"""Tests des opérateurs logiques et de la précédence (Étape 2)."""
import pytest
from laingo.ast import nodes as A
from laingo.lexer_parser.errors import LaingoSyntaxError
from laingo.lexer_parser.parser import parse


def test_ary_na_tsy_ast():
    p = parse("a = Marina ary Marina na Diso\nb = tsy Marina\n")
    a, b = p.statements
    top = a.value
    assert isinstance(top, A.LogicalOp) and top.op == "na"
    assert isinstance(top.left, A.LogicalOp) and top.left.op == "ary"
    assert isinstance(b.value, A.NotOp)


def test_precedence_not_lower_than_compare():
    # « tsy x > 5 » doit être lu « tsy (x > 5) ».
    p = parse("r = tsy x > 5\n")
    (s,) = p.statements
    top = s.value
    assert isinstance(top, A.NotOp)
    assert isinstance(top.operand, A.Compare)
    assert top.operand.op == ">"


def test_precedence_and_over_or():
    # « a ary b na c » doit être lu « (a ary b) na c ».
    p = parse("r = a ary b na c\n")
    (s,) = p.statements
    top = s.value
    assert isinstance(top, A.LogicalOp) and top.op == "na"
    assert isinstance(top.left, A.LogicalOp) and top.left.op == "ary"


def test_precedence_compare_over_and():
    # « a > 0 ary b > 0 » = « (a > 0) ary (b > 0) ».
    p = parse("r = a > 0 ary b > 0\n")
    (s,) = p.statements
    top = s.value
    assert isinstance(top, A.LogicalOp) and top.op == "ary"
    assert isinstance(top.left, A.Compare)
    assert isinstance(top.right, A.Compare)


def test_double_not():
    p = parse("r = tsy tsy Marina\n")
    (s,) = p.statements
    top = s.value
    assert isinstance(top, A.NotOp)
    assert isinstance(top.operand, A.NotOp)


def test_left_associative_and():
    p = parse("r = a ary b ary c\n")
    (s,) = p.statements
    top = s.value
    # (a ary b) ary c
    assert isinstance(top, A.LogicalOp) and top.op == "ary"
    assert isinstance(top.left, A.LogicalOp) and top.left.op == "ary"


def test_chained_comparison_error():
    with pytest.raises(LaingoSyntaxError) as ei:
        parse("r = 1 < 2 < 3\n")
    msg = str(ei.value)
    assert "mifamatotra" in msg
    assert ei.value.line == 1


def test_chained_comparison_mixed_ops_error():
    with pytest.raises(LaingoSyntaxError):
        parse("r = a == b == c\n")


def test_keyword_not_identifier():
    # « rahavavy » doit être un NAME, pas raha + vavy.
    p = parse("rahavavy = 5\n")
    (s,) = p.statements
    assert s.name == "rahavavy"


def test_keyword_ary_not_prefix_of_identifier():
    # « aryX » doit être un NAME.
    p = parse("aryX = 1\n")
    (s,) = p.statements
    assert s.name == "aryX"