class AnomalyDetector:
    """Détecteur d'anomalies basé sur des seuils métier."""

    def train(self, data):
        """Aucun entraînement requis, détection par seuils."""
        pass

    def load(self):
        """Aucune persistance requise."""
        pass

    def predict(self, ht, ttc):
        """Retourne True si le document présente une anomalie."""
        try:
            ht = float(ht)
            ttc = float(ttc)
        except (TypeError, ValueError):
            return False

        if ht <= 0 or ttc <= 0:
            return True

        if ht > 100000 or ttc > 120000:
            return True

        taux_tva = (ttc - ht) / ht
        if taux_tva < 0 or taux_tva > 0.5:
            return True

        return False
