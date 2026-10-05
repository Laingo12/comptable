# CHANGELOG LAINGO

## [v0.2.1] — Extension `.laingo`

### Modifié
- **Extension officielle des fichiers LAINGO : `.laingo`** (auparavant `.mg`).
  - CLI : aide et messages mis à jour (`parse`, `hamarino`).
  - Exemples renommés : `examples/*.mg` → `examples/*.laingo`.
  - `README.md`, `docs/CONTEXT.md` mis à jour.
  - Aucun changement de syntaxe ni de comportement du compilateur.

## [v0.2] — Étape 2 (Type Checker + logique)

### Ajouté
- Opérateurs logiques : `ary` (and), `na` (or), `tsy` (not).
- Précédence Python-like : `na < ary < tsy < comparaisons < + - < * / < -x < atomes`.
- AST : `LogicalOp`, `NotOp`.
- Type checker (`src/laingo/checker/`) : inférence, promotion, bloc-scope, appels.
- Erreurs de type en malgache avec la ligne.
- Détection des comparaisons chaînées (`a < b < c`) → erreur syntaxique explicite.
- CLI : `laingo hamarino <file.laingo>` (check only).
- Exemple `examples/lojika.laingo`.
- Tests : `tests/test_parser_logical.py`, `tests/test_typechecker.py`.

### Modifié
- Grammar : lookahead `(?!\w)` sur tous les mots-clés (évite `rahavavy` = `raha`+`vavy`).
- `parse()` : déballage des erreurs lancées dans le Transformer (chained comparison).

### Non encore implémenté
- Codegen C11.
- Runtime C (`laingo_rt.{h,c}`).
- CLI `mamorona` / `mihazakazaka`.

## [v0.1] — Étape 1 (parser + AST)
- Grammar `laingo.lark` (Lark/LALR + Indenter).
- AST dataclasses.
- Parser + erreurs malgaches.
- CLI `laingo parse`.
- 3 exemples, 17 tests.