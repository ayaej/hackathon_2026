import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib


class AnomalyDetector:

    def __init__(self):

        self.model = IsolationForest(contamination=0.05)


    def train(self,data):

        features = data[["montant_ht","montant_ttc"]]

        self.model.fit(features)

        joblib.dump(self.model,"anomaly_model.pkl")


    def load(self):

        self.model = joblib.load("anomaly_model.pkl")


    def predict(self,ht,ttc):

        df = pd.DataFrame([[ht,ttc]],columns=["montant_ht","montant_ttc"])

        prediction = self.model.predict(df)

        return prediction[0] == -1