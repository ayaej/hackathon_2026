from rules import (
    check_siret,
    check_tva,
    check_date_coherence,
    check_amount_limits,
    check_siret_format
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
        except FileNotFoundError:
            logging.warning("Could not load anomaly model. Anomaly detection disabled.")
            self.anomaly = None

    def validate(self, facture, devis):
        logging.info("Validation started: Facture vs Devis")

        errors = []

        # Vérification format SIRET
        if not check_siret_format(facture.get("siret_creancier", "")):
            errors.append("Format SIRET créancier invalide")

        # Vérification cohérence SIRET entre facture et devis
        if not check_siret(facture.get("siret_creancier"), devis.get("siret_creancier")):
            errors.append("SIRET créancier mismatch entre facture et devis")
        
        if not check_siret(facture.get("siret_client"), devis.get("siret_client")):
            errors.append("SIRET client mismatch entre facture et devis")

        # Vérification TVA
        if not check_tva(
            facture.get("montant_ht", 0),
            facture.get("montant_ttc", 0)
        ):
            errors.append("TVA incoherente")

        # Vérification cohérence des dates (devis avant facture)
        if not check_date_coherence(
            devis.get("date_emission"),
            facture.get("date_facturation")
        ):
            errors.append("Date devis posterieure a la facture")

        # Vérification des montants
        amount_issue = check_amount_limits(
            facture.get("montant_ht", 0)
        )

        if amount_issue:
            errors.append(amount_issue)

        # Détection d'anomalies via ML
        if self.anomaly:
            anomaly = self.anomaly.predict(facture, devis)

            if anomaly:
                errors.append("Incohérence détectée entre facture et devis")

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

        logging.info(f"Validation result: {report}")

        return report
