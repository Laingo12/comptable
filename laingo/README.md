# LAINGO

Langage de programmation malgache transpilé vers **C11**, optimisé CPU-first.

- Pipeline cible : `.mg` → Lark → AST → Type Checker → Codegen C11 → `gcc -O3 -march=native` → binaire.
- Compilateur écrit en Python (Lark).
- Extension : `.mg` / `.laingo`.

## État actuel — **v0.1, Étape 1**

Uniquement : **grammaire + AST + parser + CLI `parse`**.

- Types : `Isa` → int64_t, `Desimaly` → double, `Marina`/`Diso` → bool, `Teksta` → const char* (littéraux).
- Sous-ensemble supporté : variables (typées/inférées), `+ - * /`, comparaisons,
  `raha` / `raha_tsy_izany`, `rehefa` (while), `asa … -> Type`, `avereno`, `mamoaka`, `//`.

## Installation (dev)

    python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
    pip install -e ".[dev]"

## Utilisation

    laingo parse examples/hello.mg       # affiche l'AST indenté
    python -m laingo.cli parse examples/fonction.mg

## Tests

    pytest -q 