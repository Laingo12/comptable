"""Registre des modèles — un import unique suffit pour Alembic autogenerate."""

from app.models.base import Base, Timestamped, Versioned  # noqa: F401
from app.models.user import User, RefreshToken  # noqa: F401
from app.models.audit import AuditLog  # noqa: F401
from app.models.referentiel import (  # noqa: F401
    MoisScolaire,
    ModePaiement,
    Niveau,
    TypePaiement,
)
from app.models.parametres import (  # noqa: F401
    AnneeScolaire,
    ChargeCatalogue,
    GrilleTarifaire,
    Parametre,
)
from app.models.eleves import Eleve, Famille, Inscription  # noqa: F401
from app.models.personnel import Employe, SalaireMensuel  # noqa: F401
from app.models.paiements import Paiement  # noqa: F401
from app.models.charges import Charge  # noqa: F401
from app.models.salaires import PaiementSalaire  # noqa: F401
from app.models.associes import Associe  # noqa: F401
from app.models.prelevements import Prelevement  # noqa: F401
from app.models.caisse_fg import CaisseFgMouvement  # noqa: F401
from app.models.imports import ImportLigne

__all__ = [
    "Base",
    "Timestamped",
    "Versioned",
    "User",
    "RefreshToken",
    "AuditLog",
    "Niveau",
    "MoisScolaire",
    "TypePaiement",
    "ModePaiement",
    "AnneeScolaire",
    "Parametre",
    "GrilleTarifaire",
    "ChargeCatalogue",
    "Famille",
    "Eleve",
    "Inscription",
    "Employe",
    "SalaireMensuel",
    "Paiement",
    "Charge",
    "PaiementSalaire",
    "Associe",
    "Prelevement",
    "CaisseFgMouvement",
    "ImportLigne",
]