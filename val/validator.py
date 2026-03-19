from rules import (
    check_siret_format,
    check_tva,
    check_expiration,
    check_amount_limits,
)

from anomaly_model import AnomalyDetector
from risk_scoring import compute_risk, severity_level

from datetime import datetime
import logging


logging.basicConfig(
    filename="validation.log",
    level=logging.INFO
)


class DocumentValidator:

    def __init__(self):
        self.anomaly = AnomalyDetector()

        try:
            self.anomaly.load()
        except Exception:
            logging.warning("modele anomaly non disponible, detection desactivee")
            self.anomaly = None

    def validate(self, facture, attestation=None):
        """valide un document unique (facture) et eventuellement un second document (attestation/devis).
        accepte les cles dag: siret, montant_ht, montant_ttc, date_expiration"""
        logging.info("validation demarree")

        errors = []

        siret = facture.get("siret") or ""
        montant_ht = facture.get("montant_ht")
        montant_ttc = facture.get("montant_ttc")

        # conversion en float si necessaire
        try:
            montant_ht = float(montant_ht) if montant_ht is not None else None
        except (ValueError, TypeError):
            montant_ht = None

        try:
            montant_ttc = float(montant_ttc) if montant_ttc is not None else None
        except (ValueError, TypeError):
            montant_ttc = None

        # verification format siret
        if not check_siret_format(siret):
            errors.append("format siret invalide")

        # verification coherence tva (ht * 1.20 ~ ttc)
        if montant_ht is not None and montant_ttc is not None and montant_ht > 0:
            if not check_tva(montant_ht, montant_ttc):
                errors.append("tva incoherente")

        # verification montant dans les limites
        if montant_ht is not None:
            amount_issue = check_amount_limits(montant_ht)
            if amount_issue:
                errors.append(amount_issue.lower())

        # verification date expiration (attestation)
        date_exp = None
        if attestation and isinstance(attestation, dict):
            date_exp = attestation.get("date_expiration")
        if date_exp:
            if not check_expiration(str(date_exp)):
                errors.append("document expire")

        # detection anomalies via ml (si modele disponible et montants presents)
        if self.anomaly and montant_ht is not None and montant_ttc is not None:
            try:
                anomaly = self.anomaly.predict_single(montant_ht, montant_ttc)
                if anomaly:
                    errors.append("anomalie detectee par le modele ml")
            except Exception as exc:
                logging.warning("erreur detection anomalie: %s", exc)

        risk_score = compute_risk(errors)
        severity = severity_level(risk_score)
        status = "valid" if len(errors) == 0 else "invalid"

        report = {
            "status": status,
            "risk_score": risk_score,
            "severity": severity,
            "errors": errors,
            "timestamp": str(datetime.now())
        }

        logging.info("resultat validation: %s", report)
        return report
