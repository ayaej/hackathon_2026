import pandas as pd
import os
from src import config

_BASE_SIRENE = None
_CHEMIN_DEFAUT = config.SIRENE_CSV


def charger_base(chemin_csv=None):
    global _BASE_SIRENE
    chemin = chemin_csv or _CHEMIN_DEFAUT
    if not os.path.exists(chemin):
        raise FileNotFoundError(f"Base SIRENE introuvable : {chemin}")
    _BASE_SIRENE = pd.read_csv(chemin, dtype={"siren": str}, low_memory=False)
    return _BASE_SIRENE


def get_base():
    global _BASE_SIRENE
    if _BASE_SIRENE is None:
        charger_base()
    return _BASE_SIRENE


def verifier_siren(siren):
    siren = str(siren).strip().replace(" ", "")
    df = get_base()
    resultat = df[df["siren"] == siren]

    if resultat.empty:
        return None

    ligne = resultat.iloc[0]
    nom = (
        ligne.get("denominationUniteLegale")
        or f"{ligne.get('prenom1UniteLegale', '')} {ligne.get('nomUniteLegale', '')}".strip()
        or "Inconnu"
    )

    return {
        "siren": siren,
        "nom": nom,
        "etat": ligne.get("etatAdministratifUniteLegale"),
        "date_creation": ligne.get("dateCreationUniteLegale"),
        "activite_naf": ligne.get("activitePrincipaleUniteLegale"),
        "categorie": ligne.get("categorieEntreprise"),
        "nic_siege": str(ligne.get("nicSiegeUniteLegale", "")).zfill(5),
    }


def verifier_siret(siret):
    siret = str(siret).strip().replace(" ", "")
    if len(siret) != 14:
        return {"valide": False, "erreur": f"SIRET doit faire 14 chiffres, recu {len(siret)}"}

    siren = siret[:9]
    infos = verifier_siren(siren)

    if infos is None:
        return {"valide": False, "siren": siren, "erreur": "SIREN introuvable dans la base"}

    siret_siege = siren + infos.get("nic_siege", "")

    return {
        "valide": True,
        "siret_fourni": siret,
        "siret_siege_officiel": siret_siege,
        "correspond_au_siege": siret == siret_siege,
        **infos
    }


def detecter_incoherences(siret_extrait, nom_fournisseur_extrait):
    incoherences = []
    verification = verifier_siret(siret_extrait)

    if not verification.get("valide"):
        incoherences.append(f"SIRET invalide ou inconnu : {verification.get('erreur')}")
        return {"incoherences": incoherences, "verification_sirene": verification}

    if verification.get("etat") == "C":
        incoherences.append("Entreprise fermee")

    if nom_fournisseur_extrait:
        nom_officiel = (verification.get("nom") or "").lower().strip()
        nom_doc = nom_fournisseur_extrait.lower().strip()
        if nom_officiel and nom_doc not in nom_officiel and nom_officiel not in nom_doc:
            incoherences.append(
                f"Nom suspect : document='{nom_fournisseur_extrait}', SIRENE='{verification.get('nom')}'"
            )

    return {
        "incoherences": incoherences,
        "fraude_probable": len(incoherences) > 0,
        "verification_sirene": verification
    }
