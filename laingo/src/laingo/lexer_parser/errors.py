"""Erreurs LAINGO amin'ny teny malagasy."""
from __future__ import annotations


class LaingoError(Exception):
    """Fototra ho an'ny erreurs LAINGO rehetra."""

    def __init__(self, message: str, line: int = 0, column: int = 0):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(self.format())

    def format(self) -> str:
        loc = f"and. {self.line}" if self.line else "?"
        col = f", ts. {self.column}" if self.column else ""
        return f"[LAINGO] Fahadisoana tamin'ny {loc}{col}: {self.message}"


class LaingoSyntaxError(LaingoError):
    """Erreur syntaxique (parser)."""

    @classmethod
    def from_lark(cls, exc, source: str) -> "LaingoSyntaxError":
        line = getattr(exc, "line", 0) or 0
        col = getattr(exc, "column", 0) or 0
        tok = getattr(exc, "token", None)
        char = getattr(exc, "char", None)
        if tok is not None:
            msg = f"tsy nampoizina ny teny « {tok} »"
        elif char is not None:
            msg = f"tsy nampoizina ny tarehintsoratra « {char} »"
        else:
            msg = "tsy azoko ny fehezanteny"
        return cls(msg, line=line, column=col)


class LaingoTypeError(LaingoError):
    """Erreur de type (ampiasain'ny Étape 2)."""