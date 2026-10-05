"""Type checker LAINGO v0.2 (Étape 2).

Types : Isa (int64_t), Desimaly (double), Marina (bool), Teksta (const char*).
- Isa / Desimaly : arithmétique + comparaisons.
- Marina / Diso   : opérateurs logiques (ary / na / tsy) + == !=.
- Teksta          : == !=  (pas de < > ; pas de concaténation en v0.1).
- Promotion Isa -> Desimaly (arithmétique + comparaison + arg).
- Pas de conversion automatique Isa -> Marina.
- Blocs (raha / rehefa / asa) = portée locale. Réaffectation autorisée
  sur variable d'une portée extérieure, mais une nouvelle déclaration
  dans un bloc ne fuit pas hors du bloc.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from laingo.ast import nodes as A
from laingo.lexer_parser.errors import LaingoTypeError


NUMERIC = {"Isa", "Desimaly"}
ALL_TYPES = {"Isa", "Desimaly", "Marina", "Teksta"}


@dataclass
class FuncSig:
    params: List[Tuple[str, str]]
    ret: str
    line: int = 0


@dataclass
class AssignInfo:
    ctype: str          # type C (Isa/Desimaly/Marina/Teksta)
    declaration: bool   # True = nouvelle variable (à déclarer en C)


@dataclass
class TypeInfo:
    """Infos sémantiques pour le codegen (Étape 3)."""
    types: Dict[int, str] = field(default_factory=dict)          # id(expr) -> type
    functions: Dict[str, FuncSig] = field(default_factory=dict)
    assigns: Dict[int, AssignInfo] = field(default_factory=dict) # id(Assign) -> info


class _TC:
    def __init__(self):
        self.info = TypeInfo()
        self.scopes: List[Dict[str, str]] = [{}]
        self.cur_ret: Optional[str] = None

    # ------------------------------ helpers ------------------------------
    def lookup(self, name: str) -> Optional[str]:
        for s in reversed(self.scopes):
            if name in s:
                return s[name]
        return None

    def lookup_outer(self, name: str) -> Optional[str]:
        """Cherche dans les portées extérieures (pour réaffectation)."""
        # Comme lookup, mais on ne crée jamais. Sert juste à documenter.
        return self.lookup(name)

    def _t(self, expr) -> str:
        return self.info.types[id(expr)]

    @staticmethod
    def _promote(a: str, b: str) -> Optional[str]:
        if a == b:
            return a
        if {a, b} <= NUMERIC:
            return "Desimaly"
        return None

    @staticmethod
    def _assignable(target: str, src: str) -> bool:
        if target == src:
            return True
        if target == "Desimaly" and src == "Isa":
            return True
        return False

    # ------------------------------ entry ------------------------------
    def run(self, prog: A.Program):
        # 1. Collecte signatures
        for s in prog.statements:
            if isinstance(s, A.FuncDef):
                if s.name in self.info.functions:
                    raise LaingoTypeError(
                        f"efa misy ny asa « {s.name} »", line=s.line)
                seen = set()
                for pname, ptype in s.params:
                    if pname in seen:
                        raise LaingoTypeError(
                            f"miverina ny parametra « {pname} »", line=s.line)
                    seen.add(pname)
                    if ptype not in ALL_TYPES:
                        raise LaingoTypeError(
                            f"type tsy fantatra: « {ptype} »", line=s.line)
                if s.ret_type not in ALL_TYPES:
                    raise LaingoTypeError(
                        f"type de retour tsy fantatra: « {s.ret_type} »",
                        line=s.line)
                self.info.functions[s.name] = FuncSig(
                    list(s.params), s.ret_type, s.line)
        # 2. Vérification
        for s in prog.statements:
            self.stmt(s)

    # ------------------------------ statements ------------------------------
    def stmt(self, s):
        m = getattr(self, "_st_" + type(s).__name__, None)
        if m is None:
            raise LaingoTypeError(
                f"tsy fantatra ny statement: {type(s).__name__}",
                line=getattr(s, "line", 0))
        m(s)

    def _st_Assign(self, s: A.Assign):
        vt = self.expr(s.value)
        if s.type_name is None:
            cur = self.lookup(s.name)
            if cur is None:
                # Première affectation => déclaration inférée
                self.scopes[-1][s.name] = vt
                self.info.assigns[id(s)] = AssignInfo(vt, declaration=True)
            else:
                if not self._assignable(cur, vt):
                    raise LaingoTypeError(
                        f"tsy mifanaraka ny type: « {s.name} » dia {cur}, fa {vt}",
                        line=s.line)
                self.info.assigns[id(s)] = AssignInfo(cur, declaration=False)
        else:
            if s.type_name not in ALL_TYPES:
                raise LaingoTypeError(
                    f"type tsy fantatra: « {s.type_name} »", line=s.line)
            if self.lookup(s.name) is not None:
                raise LaingoTypeError(
                    f"efa voambara ny « {s.name} »", line=s.line)
            if not self._assignable(s.type_name, vt):
                raise LaingoTypeError(
                    f"tsy mifanaraka ny type: andrasana {s.type_name}, "
                    f"nahazo {vt}",
                    line=s.line)
            self.scopes[-1][s.name] = s.type_name
            self.info.assigns[id(s)] = AssignInfo(s.type_name, declaration=True)

    def _st_Print(self, s: A.Print):
        self.expr(s.value)

    def _st_Return(self, s: A.Return):
        if self.cur_ret is None:
            raise LaingoTypeError(
                "tsy azo atao ny « avereno » ivelan'ny asa", line=s.line)
        vt = self.expr(s.value)
        if not self._assignable(self.cur_ret, vt):
            raise LaingoTypeError(
                f"tsy mifanaraka amin'ny type de retour ({self.cur_ret}): "
                f"nahazo {vt}",
                line=s.line)

    def _st_If(self, s: A.If):
        self._check_cond(s.cond, s.line)
        self.scopes.append({})
        for x in s.body:
            self.stmt(x)
        self.scopes.pop()
        for i, (cond, body) in enumerate(s.elifs):
            is_last = (i == len(s.elifs) - 1)
            if cond is None and not is_last:
                raise LaingoTypeError(
                    "tsy maintsy farany ny « raha_tsy_izany » (else) — "
                    "tsy azo atao ny manisy « raha_tsy_izany » aorian'ny else",
                    line=s.line)
            if cond is not None:
                self._check_cond(cond, s.line)
            self.scopes.append({})
            for x in body:
                self.stmt(x)
            self.scopes.pop()

    def _st_While(self, s: A.While):
        self._check_cond(s.cond, s.line)
        self.scopes.append({})
        for x in s.body:
            self.stmt(x)
        self.scopes.pop()

    def _st_FuncDef(self, s: A.FuncDef):
        sig = self.info.functions[s.name]
        saved = self.cur_ret
        self.cur_ret = sig.ret
        self.scopes.append({p: t for p, t in sig.params})
        for x in s.body:
            self.stmt(x)
        if not self._has_return(s.body):
            raise LaingoTypeError(
                f"tsy misy « avereno » ao amin'ny asa « {s.name} »",
                line=s.line)
        self.scopes.pop()
        self.cur_ret = saved

    def _check_cond(self, cond, line: int):
        ct = self.expr(cond)
        if ct != "Marina":
            raise LaingoTypeError(
                f"tsy Marina ny fepetra (nahazo {ct})", line=line)

    @staticmethod
    def _has_return(body) -> bool:
        for x in body:
            if isinstance(x, A.Return):
                return True
            if isinstance(x, A.If):
                if _TC._has_return(x.body): return True
                for _, b in x.elifs:
                    if _TC._has_return(b): return True
            if isinstance(x, A.While):
                if _TC._has_return(x.body): return True
        return False

    # ------------------------------ expressions ------------------------------
    def expr(self, e) -> str:
        t = self._expr(e)
        self.info.types[id(e)] = t
        return t

    def _expr(self, e) -> str:
        if isinstance(e, A.Number):
            return e.kind
        if isinstance(e, A.String):
            return "Teksta"
        if isinstance(e, A.Bool):
            return "Marina"
        if isinstance(e, A.Name):
            t = self.lookup(e.id)
            if t is None:
                raise LaingoTypeError(f"tsy voambara ny « {e.id} »", line=e.line)
            return t
        if isinstance(e, A.UnaryOp):  # "-"
            t = self.expr(e.operand)
            if t not in NUMERIC:
                raise LaingoTypeError(
                    f"tsy azo atao ny « - » amin'ny {t}", line=e.line)
            return t
        if isinstance(e, A.BinOp):
            lt = self.expr(e.left)
            rt = self.expr(e.right)
            if lt not in NUMERIC or rt not in NUMERIC:
                raise LaingoTypeError(
                    f"tsy azo atao ny « {e.op} » amin'ny {lt} sy {rt}",
                    line=e.line)
            p = self._promote(lt, rt)
            assert p is not None
            return p
        if isinstance(e, A.Compare):
            return self._compare(e)
        if isinstance(e, A.LogicalOp):
            lt = self.expr(e.left)
            rt = self.expr(e.right)
            if lt != "Marina" or rt != "Marina":
                raise LaingoTypeError(
                    f"tsy azo atao ny « {e.op} » amin'ny {lt} sy {rt} "
                    f"(Marina/Diso ihany)",
                    line=e.line)
            return "Marina"
        if isinstance(e, A.NotOp):
            t = self.expr(e.operand)
            if t != "Marina":
                raise LaingoTypeError(
                    f"tsy azo atao ny « tsy » amin'ny {t} "
                    f"(Marina/Diso ihany)",
                    line=e.line)
            return "Marina"
        if isinstance(e, A.Call):
            return self._call(e)
        raise LaingoTypeError(
            f"expression tsy fantatra: {type(e).__name__}",
            line=getattr(e, "line", 0))

    def _compare(self, e: A.Compare) -> str:
        lt = self.expr(e.left)
        rt = self.expr(e.right)
        if e.op in ("==", "!="):
            if lt == rt and lt in {"Isa", "Desimaly", "Marina"}:
                return "Marina"
            if lt in NUMERIC and rt in NUMERIC:
                return "Marina"
            raise LaingoTypeError(
                f"tsy azo ampitahaina ny {lt} sy {rt} amin'ny « {e.op} »",
                line=e.line)
        # < <= > >= : numeric ihany
        if lt not in NUMERIC or rt not in NUMERIC:
            raise LaingoTypeError(
                f"tsy azo atao ny « {e.op} » amin'ny {lt} sy {rt}",
                line=e.line)
        return "Marina"

    def _call(self, e: A.Call) -> str:
        sig = self.info.functions.get(e.func)
        if sig is None:
            raise LaingoTypeError(
                f"tsy misy ny asa « {e.func} »", line=e.line)
        if len(e.args) != len(sig.params):
            raise LaingoTypeError(
                f"diso isa ny arg: andrasana {len(sig.params)}, "
                f"nahazo {len(e.args)}",
                line=e.line)
        for i, (arg, (_, ptype)) in enumerate(zip(e.args, sig.params)):
            at = self.expr(arg)
            if not self._assignable(ptype, at):
                raise LaingoTypeError(
                    f"arg {i+1} amin'ny « {e.func} »: andrasana {ptype}, "
                    f"nahazo {at}",
                    line=e.line)
        return sig.ret


def check(prog: A.Program) -> TypeInfo:
    tc = _TC()
    tc.run(prog)
    return tc.info