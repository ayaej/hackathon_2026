from faker import Faker
import random as rn
import datetime
import json


faker = Faker('fr_FR')

ARTICLE_DESCRIPTIONS = [
    "Service de conseil",
    "Formation",
    "Abonnement",
    "Licence logiciel",
    "Maintenance",
    "Support technique",
    "Développement",
    "Audit",
    "Intervention",
    "Assistance"
]
ARTICLE_CONNECTEURS = [" en"," de"," pour","",""]
ARTICLE_DOMAINES = [
    " informatique", " marketing", " comptabilité",
    " RH", " communication", " administration",
    " sécurité", " cloud", " data", " réseau"
]


class Facture :
    def __init__(self) :
        self._dictkeys = ("facture_id",
                          "devis_id",
                          "date_facturation",
                          "date_echeance",
                          "date_prestation",
                          "date_emission",
                          "date_expiration",
                          "montant_ttc",
                          "tva_montant",
                          "tva_taux",
                          "montant_ht",
                          "creancier",
                          "client",
                          "articles")

    def __iter__(self):
        for key in self._dictkeys :
            yield key, getattr(self, key)

    def generateRandom(self) :
        min_date = datetime.date(year=2015, month=1, day=1)
        max_date = datetime.date(year=2035, month=1, day=1)
        self.date_facturation = faker.date_between(start_date = min_date, end_date = max_date)
        self.date_echeance = faker.date_between(start_date = self.date_facturation, end_date = max_date)
        self.date_prestation = self.date_facturation if rn.random()>.5 else faker.date_between(start_date = self.date_facturation, end_date = max_date)
        self.date_emission = faker.date_between(start_date = min_date, end_date = self.date_prestation)
        self.date_expiration = faker.date_between(start_date = self.date_prestation, end_date = max_date)
        
        self.facture_id = f"FA-{str(self.date_facturation)[:4]}-{rn.randint(0, 9999):04d}"
        self.devis_id = f"D-{str(self.date_emission)[:4]}-{rn.randint(0,999):03d}"
        date_format = rn.choice(["%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y", "%d / %m / %Y", "%d - %m - %Y", "%d / %m / %y", "%d - %m - %y"])
        self.date_facturation = self.date_facturation.strftime(date_format)
        self.date_echeance = self.date_echeance.strftime(date_format)
        self.date_prestation = self.date_prestation.strftime(date_format)
        self.date_emission = self.date_emission.strftime(date_format)
        self.date_expiration = self.date_expiration.strftime(date_format)
        

        self.articles = []
        for _ in range(rn.randint(1,10)) :
            article = rn.choice(ARTICLE_DESCRIPTIONS)
            if rn.random()>.2 :
                article += rn.choice(ARTICLE_CONNECTEURS) + rn.choice(ARTICLE_DOMAINES)
            prix = round(1/(rn.random()*200+1)*1000, 2)
            quantite = rn.randint(1,10)
            self.articles.append({"nom":article, "prix":prix, "quantite":quantite})

        self.montant_ht = sum(article["prix"] * article["quantite"] for article in self.articles)
        self.montant_ht = round(self.montant_ht,2) if rn.random()<.95 else round(self.montant_ht*(1+rn.random()/10),2)
        self.tva_taux = round(rn.random()/5, 2)
        self.tva_montant = round(self.tva_taux * self.montant_ht, 2) if rn.random()<.95 else round(self.tva_taux*(1+rn.random()/10) * self.montant_ht, 2)
        self.montant_ttc = round(self.montant_ht + self.tva_montant, 2) if rn.random()<.95 else round((self.montant_ht + self.tva_montant)*(1+rn.random()/10),2)

        creancier = Personne()
        creancier.generateRandom()
        self.obj_creancier = creancier
        self.creancier = dict(creancier)
        client = Personne()
        client.generateRandom()
        self.obj_client = client
        self.client = dict(client)

    
    def display(self) :
        print(f"""
# FACTURE
              
    ID : {self.facture_id}
              
    DATE FACTURATION : {self.date_facturation}
    DATE PRESTATION  : {self.date_prestation}
    DATE ECHEANCE    : {self.date_echeance}

    MONTANT HT  : {self.montant_ht} €
    TVA         : {self.tva_montant} €
    MONTANT TTC : {self.montant_ttc} €
    """)
        print("# CREANCIER :")
        self.obj_creancier.display()
        print("# CLIENT :")
        self.obj_client.display()
        print("# ARTICLES :")
        for article in self.articles :
            print(f"    - {article['quantite']} {article['nom']} ({article['prix']} €) : {(article['quantite']*article['prix']):.2f} €")


class Personne :
    def __init__(self) :
        self._dictkeys = ("siren","nic","siret","n_tva","nom","prenom","prenom_2","prenom_3","sexe","adresse","code_postal","commune","ape")

    def __iter__(self):
        for key in self._dictkeys :
            yield key, getattr(self, key)

    def generateRandom(self) :

        siret = rn.randint(0, 10**14 - 1)
        siret = f"{siret:014d}"
        self.siret = siret
        self.siren = siret[:9]
        self.nic = siret[9:]
        self.n_tva = 'FR' + str(round(rn.random()*100)) + ' ' + self.siren

        self.prenom = faker.first_name()
        self.prenom_2 = '' if rn.random() < .75 else faker.first_name()
        self.prenom_3 = '' if rn.random() < .9 or self.prenom_2 == '' else faker.first_name()
        self.nom = faker.last_name()
        self.sexe = rn.choice(['M','F',''])

        self.adresse = faker.street_address()
        if self.adresse[0] not in ['1','2','3','4','5','6','7','8','9'] :
            self.adresse = str(rn.randint(1,9)) + ', ' + self.adresse
        self.code_postal = faker.postcode()
        self.commune = faker.city()

        self.ape = f"{int(rn.random()*5700):04d}" + ['A','B','C','D','Z'][int(rn.random()*5)]

    def display(self) :
        print(f"""
    SIREN : {self.siren}
    NIC   : {self.nic}
    SIRET : {self.siret}
    N TVA : {self.n_tva}

    NOM      : {self.nom}
    PRENOM 1 : {self.prenom}
    PRENOM 2 : {self.prenom_2}
    PRENOM 3 : {self.prenom_3}
    SEXE     : {self.sexe}

    ADRESSE     : {self.adresse}
    CODE POSTAL : {self.code_postal}
    COMMUNE     : {self.commune}

    APE / NAF : {self.ape}
    """)


def generateDataset() :
    liste = []
    for _ in range(100) :
        facture = Facture()
        facture.generateRandom()
        liste.append(dict(facture))

    with open("dataset.json", "w", encoding="utf-8") as f:
        json.dump(liste, f, ensure_ascii=False, indent=4)

if __name__ == "__main__" :
    generateDataset()