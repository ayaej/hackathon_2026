# Validation Service

Un service Python léger de validation de factures et attestations.

## 📁 Structure du projet

- `validation_engine.py` : script principal qui lit `sample_data.json`, exécute la validation et affiche le rapport.
- `validator.py` : classe `DocumentValidator` qui applique les règles, le détecteur d'anomalies et calcule le score de risque.
- `rules.py` : règles de validation métier (SIRET, TVA, expiration, montants).
- `anomaly_model.py` : modèle de détection d'anomalies (chargement et prédiction).
- `risk_scoring.py` : calcul du score de risque et niveau de sévérité.
- `train_model.py` : script d'entraînement du modèle (si prévu).
- `sample_data.json` : exemple de données d'entrée.

## 🚀 Prérequis

- Python 3.8+
- Installer les dépendances si nécessaire depuis `requirements.txt`.

```bash
python -m pip install -r requirements.txt
```

## ▶️ Exécution

Dans le dossier du projet :

```bash
python validation_engine.py
```

Vous verrez un rapport similaire :

- `status` : `valid` ou `invalid`
- `risk_score`
- `severity`
- `errors`
- `timestamp`

## � Exemple JSON d'entrée

`sample_data.json` doit contenir :

```json
{
  "facture": {
    "siret": "55210055400013",
    "montant_ht": 1000,
    "montant_ttc": 1200
  },
  "attestation": {
    "siret": "55210055400013",
    "date_expiration": "2027-01-01"
  }
}
```

## 🧪 Exemple JSON de sortie

Le résultat renvoyé par `DocumentValidator.validate(...)` ressemble à :

```json
{
  "status": "valid",
  "risk_score": 0,
  "severity": "low",
  "errors": [],
  "timestamp": "2026-03-16 12:34:56.789123"
}
```

## �🧪 Tester avec d'autres données

Copiez `sample_data.json` dans un nouveau fichier ou éditez les valeurs, puis modifiez `validation_engine.py` pour charger un autre fichier.

## 🔧 Personnalisation

- Ajustez les règles dans `rules.py`.
- Améliorez ou ré-entraînez le modèle dans `anomaly_model.py` / `train_model.py`.
- Adaptez la logique de risque dans `risk_scoring.py`.

## 📝 Notes

- Les logs sont écrits dans `validation.log`.
- La validation est faite sur la base de règles simples (ex. même SIRET, TVA à 20%, date d'expiration).
