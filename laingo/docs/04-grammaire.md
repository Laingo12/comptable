# 04 — Grammaire LAINGO

## Mots-clés

| LAINGO              | International       | Rôle                                     |
|---------------------|---------------------|------------------------------------------|
| `raha`              | if                  | Condition                                |
| `raha_tsy_izany`    | elif / else         | elif si condition, else sinon (doit être dernier) |
| `rehefa`            | while (v0.1)        | Boucle (for-range viendra plus tard)     |
| `asa`               | function            | Fonction                                 |
| `kilasy`            | class               | Classe (v. future)                       |
| `rafitra`           | struct              | Structure (v. future)                    |
| `avereno`           | return              | Retour                                   |
| `ampidiro`          | import              | Import (v. future)                       |
| `aoka`              | raise               | Exception (v. future)                    |
| `mamoaka`           | print               | Affichage                                |
| `amin'ny`           | as                  | Alias d'import (v. future)               |
| `ary`               | and                 | ET logique (court-circuit)               |
| `na`                | or                  | OU logique (court-circuit)               |
| `tsy`               | not                 | NON logique (unaire)                     |

## Types de base
- `Isa` → `int64_t`
- `Desimaly` → `double`
- `Marina` / `Diso` → `bool` (respectivement vrai / faux)
- `Teksta` → `const char*` (littéraux seulement en v0.1)

## Précédence des opérateurs (plus bas → plus haut)

1. `na`         (OU logique)
2. `ary`        (ET logique)
3. `tsy`        (NON logique, préfixe)
4. `==` `!=` `<` `<=` `>` `>=`  (comparaisons, NON chaînables)
5. `+` `-`
6. `*` `/`
7. `-x`         (moins unaire)
8. Atomes : littéraux, identifiants, `f(...)`, `( … )`

### Conséquences
- `tsy x > 5`  se lit `tsy (x > 5)` — comme en Python.
- `a > 0 ary b > 0` se lit `(a > 0) ary (b > 0)`.
- `a ary b na c` se lit `(a ary b) na c`.

### Comparaisons chaînées : **interdites**
`a < b < c` est une **erreur syntaxique**. Il faut écrire
`a < b ary b < c`. Message :
> Tsy azo atao ny fampitahana mifamatotra (ohatra: a < b < c).
> Sokafy amin'ny « ary » na « na » : ohatra « a < b ary b < c ».

## Court-circuit
`ary` et `na` utilisent le **court-circuit** (comme `&&` / `||` en C) :
- `a ary b` : `b` n'est évalué que si `a` est `Marina`.
- `a na b`  : `b` n'est évalué que si `a` est `Diso`.
Ce comportement sera respecté par le codegen C à l'Étape 3.

## Logique : `Marina` / `Diso` uniquement, pas de conversion
- `ary`, `na`, `tsy` n'acceptent que des `Marina`/`Diso`.
- Pas de conversion implicite `Isa → Marina` : `raha 1:` est **une erreur de type**.
- ⚠️ **`tsy` (négation logique) ≠ `Diso` (littéral faux)** :
  `tsy x` inverse un booléen ; `x = Diso` affecte `false`.

## Commentaires
`// ...` (jusqu'à la fin de la ligne).