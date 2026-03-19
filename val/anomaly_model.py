import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib
import numpy as np
import os


MODEL_PATH = os.path.join(os.path.dirname(__file__), "anomaly_model.pkl")


class AnomalyDetector:

    def __init__(self, model_path=None):
        self.model_path = model_path or MODEL_PATH
        self.model = IsolationForest(contamination=0.2, random_state=42)
        self._loaded = False

    def train(self, data):
        features = data[["diff_siret_creancier", "diff_siret_client", "diff_montant", "ratio_tva", "erreur_date", "erreur_montant"]]
        self.model.fit(features)
        joblib.dump(self.model, self.model_path)
        self._loaded = True

    def train_baseline(self):
        """entraine un modele de base avec des donnees synthetiques normales"""
        rng = np.random.RandomState(42)
        n = 200
        data = pd.DataFrame({
            "diff_siret_creancier": rng.choice([0, 1], size=n, p=[0.95, 0.05]),
            "diff_siret_client": rng.choice([0, 1], size=n, p=[0.95, 0.05]),
            "diff_montant": rng.exponential(50, n),
            "ratio_tva": rng.normal(0.20, 0.02, n),
            "erreur_date": rng.choice([0, 1], size=n, p=[0.9, 0.1]),
            "erreur_montant": rng.choice([0, 1], size=n, p=[0.9, 0.1]),
        })
        self.train(data)

    def exists(self):
        return os.path.isfile(self.model_path)

    def load(self):
        if not self.exists():
            self.train_baseline()
        self.model = joblib.load(self.model_path)
        self._loaded = True

    def predict_single(self, montant_ht, montant_ttc):
        """prediction pour un seul document (sans paire facture/devis)"""
        if not self._loaded:
            return False

        ratio_tva = (montant_ttc - montant_ht) / montant_ht if montant_ht > 0 else 0
        erreur_montant = 1 if abs(ratio_tva - 0.20) > 0.05 else 0

        features = pd.DataFrame([[0, 0, 0, ratio_tva, 0, erreur_montant]],
                                columns=["diff_siret_creancier", "diff_siret_client", "diff_montant",
                                          "ratio_tva", "erreur_date", "erreur_montant"])
        prediction = self.model.predict(features)
        return prediction[0] == -1

    def predict(self, facture, devis):
        """prediction pour une paire facture/devis (compatibilite)"""
        if not self._loaded:
            return False

        diff_siret_creancier = 0 if facture.get("siret_creancier") == devis.get("siret_creancier") else 1
        diff_siret_client = 0 if facture.get("siret_client") == devis.get("siret_client") else 1

        montant_ht_facture = facture.get("montant_ht", 0) or 0
        montant_ht_devis = devis.get("montant_ht", 0) or 0
        diff_montant = abs(montant_ht_facture - montant_ht_devis) if montant_ht_devis > 0 else 0

        montant_ht = facture.get("montant_ht", 0) or 0
        montant_ttc = facture.get("montant_ttc", 1) or 1
        ratio_tva = (montant_ttc - montant_ht) / montant_ht if montant_ht > 0 else 0

        erreur_date = 0 if self._check_date_coherence(facture, devis) else 1
        erreur_montant = 1 if abs(ratio_tva - 0.2) > 0.05 else 0

        features = pd.DataFrame([[diff_siret_creancier, diff_siret_client, diff_montant, ratio_tva, erreur_date, erreur_montant]],
                                columns=["diff_siret_creancier", "diff_siret_client", "diff_montant", "ratio_tva", "erreur_date", "erreur_montant"])

        prediction = self.model.predict(features)
        return prediction[0] == -1

    def _check_date_coherence(self, facture, devis):
        from datetime import datetime
        try:
            date_facture_str = facture.get("date_facturation", "")
            date_devis_str = devis.get("date_emission", "")

            formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d / %m / %Y", "%d - %m - %Y"]

            date_facture = None
            date_devis = None

            for fmt in formats:
                if not date_facture:
                    try:
                        date_facture = datetime.strptime(date_facture_str, fmt)
                    except Exception:
                        pass
                if not date_devis:
                    try:
                        date_devis = datetime.strptime(date_devis_str, fmt)
                    except Exception:
                        pass

            if date_facture and date_devis:
                return date_devis <= date_facture

            return True
        except Exception:
            return True