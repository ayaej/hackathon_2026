from rules import (
    check_siret,
    check_tva,
    check_expiration,
    check_amount_limits,
    check_siret_format
)

from consistency_checker import ConsistencyChecker
from risk_scoring import compute_risk, severity_level

from datetime import datetime
import logging
from src import config


logging.basicConfig(
    filename=config.VALIDATION_LOG,
    level=logging.INFO
)


class DocumentValidator:

    def __init__(self):
        self.consistency = ConsistencyChecker()
        self.consistency.load()

    def validate(self, facture, attestation):

        logging.info("Validation started")

        errors = []

        if not check_siret_format(facture["siret"]):
            errors.append("Format SIRET invalide")

        if not check_siret(facture["siret"], attestation["siret"]):
            errors.append("SIRET mismatch")

        if not check_tva(
            facture["montant_ht"],
            facture["montant_ttc"]
        ):
            errors.append("TVA incoherente")

        if not check_expiration(
            attestation["date_expiration"]
        ):
            errors.append("Attestation expirée")

        amount_issue = check_amount_limits(
            facture["montant_ht"]
        )

        if amount_issue:
            errors.append(amount_issue)

        if self.consistency:
            incoherent_amount = self.consistency.predict(
                facture["montant_ht"],
                facture["montant_ttc"]
            )

            if incoherent_amount:
                errors.append("Montants incohérents détectés")

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
