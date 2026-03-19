import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib
import numpy as np


class AnomalyDetector:

    def __init__(self):
        self.model = IsolationForest(contamination=0.2, random_state=42)

    def train(self, data):
        features = data[["diff_siret_creancier", "diff_siret_client", "diff_montant", "ratio_tva", "erreur_date", "erreur_montant"]]
        self.model.fit(features)
        joblib.dump(self.model, "anomaly_model.pkl")

    def load(self):
        self.model = joblib.load("anomaly_model.pkl")

    def predict(self, facture, devis):
        # Comparaison SIRET créancier
        diff_siret_creancier = 0 if facture.get("siret_creancier") == devis.get("siret_creancier") else 1
        
        # Comparaison SIRET client
        diff_siret_client = 0 if facture.get("siret_client") == devis.get("siret_client") else 1
        
        # Comparaison montants
        montant_ht_facture = facture.get("montant_ht", 0)
        montant_ht_devis = devis.get("montant_ht", 0)
        diff_montant = abs(montant_ht_facture - montant_ht_devis) if montant_ht_devis > 0 else 0
        
        # Calcul ratio TVA
        montant_ht = facture.get("montant_ht", 0)
        montant_ttc = facture.get("montant_ttc", 1)
        ratio_tva = (montant_ttc - montant_ht) / montant_ht if montant_ht > 0 else 0
        
        # Vérification cohérence dates
        erreur_date = 0 if self._check_date_coherence(facture, devis) else 1
        
        # Vérification cohérence montant TVA
        tva_tolerance = 0.05
        erreur_montant = 1 if abs(ratio_tva - 0.2) > tva_tolerance else 0
        
        features = pd.DataFrame([[diff_siret_creancier, diff_siret_client, diff_montant, ratio_tva, erreur_date, erreur_montant]], 
                                columns=["diff_siret_creancier", "diff_siret_client", "diff_montant", "ratio_tva", "erreur_date", "erreur_montant"])
        
        prediction = self.model.predict(features)
        return prediction[0] == -1

    def _check_date_coherence(self, facture, devis):
        from datetime import datetime
        try:
            date_facture_str = facture.get("date_facturation", "")
            date_devis_str = devis.get("date_emission", "")
            
            # Plusieurs formats possibles
            formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d / %m / %Y", "%d - %m - %Y"]
            
            date_facture = None
            date_devis = None
            
            for fmt in formats:
                if not date_facture:
                    try:
                        date_facture = datetime.strptime(date_facture_str, fmt)
                    except:
                        pass
                if not date_devis:
                    try:
                        date_devis = datetime.strptime(date_devis_str, fmt)
                    except:
                        pass
            
            if date_facture and date_devis:
                return date_devis <= date_facture
            
            return True
        except:
            return True