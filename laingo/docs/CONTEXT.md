# CONTEXT LAINGO

Fichier à recoller dans une nouvelle conversation.

## Décisions fondamentales
- Pipeline : `.laingo` → Lark → AST → Type Checker → Codegen C11 → `gcc/clang -O3 -march=native` → binaire.
- Compilateur écrit en **Python + Lark** (Indenter pour l'indentation).
- **Extension officielle : `.laingo`.**
- Interdits pour l'instant : assembleur, JVM, LLVM, SIMD manuel, backend HTTP, GC, AGI.

## Mots-clés officiels
| LAINGO | International | Rôle |
|---|---|---|
| raha | if | Condition |
| raha_tsy_izany | elif / else | elif si condition, else sinon (doit être dernier) |
| rehefa | while (v0.1) | Boucle |
| asa | function | Fonction |
| kilasy | class | (futur) |
| rafitra | struct | (futur) |
| avereno | return | Retour |
| ampidiro | import | (futur) |
| aoka | raise | (futur) |
| mamoaka | print | Affichage |
| amin'ny | as | (futur) |
| **ary** | and | ET logique (court-circuit) |
| **na**  | or  | OU logique (court-circuit) |
| **tsy** | not | NON logique (unaire) |

## Types
- `Isa` → `int64_t`
- `Desimaly` → `double`
- `Marina` / `Diso` → `bool`
- `Teksta` → `const char*` (littéraux seulement en v0.2)

## Règles de conception
- `x = 5` (inféré = Isa), `x: Isa = 5` (explicite), `x = 6` (réaffectation, type inchangé).
- Promotion : `Isa → Desimaly` (arithmétique, comparaison, arg).
- Pas de conversion automatique `Isa → Marina`.
- **Blocs** = portée locale (`raha`, `rehefa`, `asa`) ; une variable déclarée dans un bloc ne fuit pas.
- `mamoaka(x)` : une seule fonction visible ; le codegen choisira `mamoaka_isa/desimaly/bool/teksta`.
- Comparaisons chaînées (`a < b < c`) = **erreur syntaxique**.
- `tsy` (négation logique) ≠ `Diso` (littéral faux).
- Commentaires `//`.

## Précédence (plus bas → plus haut)
na < ary < tsy < comparaisons < + - < * / < -x < atomes
- `tsy x > 5` = `tsy (x > 5)` (Python-like).
- `a ary b na c` = `(a ary b) na c`.

## Étapes
- **Étape 1** : ✔ Parser + AST + CLI `parse` + tests.
- **Étape 2** : ✔ Type checker + opérateurs logiques `ary / na / tsy` + CLI `hamarino`.
- Étape 3 : Codegen C + runtime + CLI `mamorona` / `mihazakazaka` + 3 exemples + tests end-to-end + `-fsanitize=address,undefined`.
- Étape 4 : Erreurs pédagogiques, README (malgache d'abord), LICENSE MIT.
- Étape 5 : Listes/tableaux, for-range, Teksta dynamique (arène).
- Étape 6 : `rafitra`, `ampidiro`.
- Étape 7 : Tensor/autograd C, SIMD/GEMM après benchmark.
- Étape 8 : VS Code, REPL, playground.
- Étape 9 : Doc pédagogique.

## Limites connues (v0.2)
- `.laingo` doit se terminer par un retour à la ligne (parse() normalise).
- Pas de `Teksta` dynamique (littéraux uniquement ; pas de `==` sur Teksta).
- Pas d'échappement dans les chaînes (`\n` non interprété).
- Commentaires `//` sur une seule ligne.
- `mamoaka()` sans argument : erreur syntaxe (variadic à venir).
- `rehefa` = while ; for-range à l'Étape 5.