import pandas as pd
import json
from anomaly_model import AnomalyDetector

print("Chargement du dataset...")
with open("../data/dataset.json", "r", encoding="utf-8") as f:
    dataset = json.load(f)

print(f"Nombre d'enregistrements: {len(dataset)}")

# Créer les paires de comparaison depuis chaque enregistrement
data_list = []

for record in dataset:
    if not record.get("creancier") or not record.get("client"):
        continue
    
    # Extraire les SIRET
    siret_creancier = record.get("creancier", {}).get("siret", "")
    siret_client = record.get("client", {}).get("siret", "")
    
    # Pour simuler une comparaison, on considère que chaque enregistrement
    # représente à la fois la facture et son devis associé
    # Les SIRET devraient être identiques (diff = 0) dans un cas normal
    diff_siret_creancier = 0  # Normalement identiques
    diff_siret_client = 0  # Normalement identiques
    
    # Comparer les montants (dans un vrai cas, il pourrait y avoir des différences)
    montant_ht = record.get("montantHT", 0)
    montant_ttc = record.get("montantTTC", 0)
    
    # Simuler une différence de montant (0 si pas d'erreur)
    diff_montant = 0
    
    # Calculer ratio TVA
    ratio_tva = (montant_ttc - montant_ht) / montant_ht if montant_ht > 0 else 0.2
    
    # Labels d'erreur du dataset
    erreur_date = 1 if record.get("erreur_date", False) else 0
    erreur_montant = 1 if record.get("erreur_montant", False) else 0
    
    data_list.append({
        "diff_siret_creancier": diff_siret_creancier,
        "diff_siret_client": diff_siret_client,
        "diff_montant": diff_montant,
        "ratio_tva": ratio_tva,
        "erreur_date": erreur_date,
        "erreur_montant": erreur_montant
    })

df = pd.DataFrame(data_list)

print(f"\nDonnees utilisees pour l'entrainement: {len(df)} enregistrements")
print("\nStatistiques des features:")
print(df.describe())

print(f"\nNombre d'erreurs de date: {df['erreur_date'].sum()}")
print(f"Nombre d'erreurs de montant: {df['erreur_montant'].sum()}")

print("\nEntrainement du modele d'anomalie...")
model = AnomalyDetector()
model.train(df)

print("Modele entraine et sauvegarde dans anomaly_model.pkl")
print("Le modele detecte les incoherences basees sur erreur_date et erreur_montant")