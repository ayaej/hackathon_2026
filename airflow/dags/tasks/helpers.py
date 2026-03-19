"""fonctions utilitaires partagees par toutes les taches du pipeline.
contient : configuration reseau, appels http, conversions date/montant."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any
from urllib import error, request

from airflow.models import Variable


# ---------- constantes de configuration reseau ----------

# url de base du backend node/express (ETUDIANT 3)
DEFAULT_BACKEND_BASE_URL = "http://backend:5000"

# chemin ou les fichiers uploades du backend sont montes dans le conteneur airflow
BACKEND_UPLOADS_PATH = "/opt/airflow/backend_uploads"

# url de base de l'api data-lake (ETUDIANT 4)
DEFAULT_DATALAKE_BASE_URL = "http://datalake:3000"


# ---------- resolution des urls ----------

def get_backend_base_url() -> str:
    """airflow variable pour eviter de modifier le code selon les environnements."""
    return Variable.get("backend_base_url", default_var=DEFAULT_BACKEND_BASE_URL).rstrip("/")


def get_datalake_base_url() -> str:
    """airflow variable pour l'url du data-lake."""
    return Variable.get("datalake_base_url", default_var=DEFAULT_DATALAKE_BASE_URL).rstrip("/")


# ---------- appel http generique ----------

def http_json(method: str, url: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
    """appel http generique qui envoie/recoit du json."""
    body: bytes | None = None
    headers = {"Accept": "application/json"}

    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(url=url, data=body, headers=headers, method=method)

    try:
        with request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"erreur HTTP {exc.code} sur {url}: {details}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"erreur reseau sur {url}: {exc.reason}") from exc


# ---------- conversions ----------

def to_float(value: Any) -> float | None:
    """conversion robuste en float, supporte str avec euro/virgule."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        normalized = value.replace(" ", "").replace("€", "").replace("EUR", "").replace(",", ".")
        try:
            return float(normalized)
        except ValueError:
            return None
    return None


def normaliser_date_iso(value: Any) -> str | None:
    """normalise une date (str) vers le format ISO 8601 UTC."""
    if value is None:
        return None

    texte = str(value).strip()
    if not texte:
        return None

    # tente d'abord les formats ISO natifs
    try:
        dt = datetime.fromisoformat(texte.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).isoformat(timespec="seconds")
    except ValueError:
        pass

    # yyyy-mm-dd ou yyyy/mm/dd
    iso_match = re.match(r"^(\d{4})[\-\/.](\d{1,2})[\-\/.](\d{1,2})$", texte)
    if iso_match:
        annee, mois, jour = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
        try:
            return datetime(annee, mois, jour, tzinfo=timezone.utc).isoformat(timespec="seconds")
        except ValueError:
            return None

    # dd-mm-yy ou dd/mm/yyyy
    fr_match = re.match(r"^(\d{1,2})[\-\/.](\d{1,2})[\-\/.](\d{2,4})$", texte)
    if fr_match:
        jour, mois, annee = int(fr_match.group(1)), int(fr_match.group(2)), int(fr_match.group(3))
        if annee < 100:
            annee += 2000
        try:
            return datetime(annee, mois, jour, tzinfo=timezone.utc).isoformat(timespec="seconds")
        except ValueError:
            return None

    return None
