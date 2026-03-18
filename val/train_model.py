import pandas as pd
from anomaly_model import AnomalyDetector

data = pd.DataFrame({
    "montant_ht":[100,200,300,500,800,1000,1500],
    "montant_ttc":[120,240,360,600,960,1200,1800]
})

model = AnomalyDetector()

model.train(data)

print("Model trained")