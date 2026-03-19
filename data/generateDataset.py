from faker import Faker
import random as rn
import datetime
import json
import string


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


def rni_low(min, max) :
    x = rn.randint(1,int(max/min) if min>=1 else int(max))
    x = int(round(max/x))
    return x

class Facture :
    def __init__(self) :
        self._dictkeys = ("facture_id",
                          "devis_id",
                          "numero_document",
                          "dateFacturation",
                          "dateEcheance",
                          "datePrestation",
                          "dateEmission",
                          "dateExpiration",
                          "montantTTC",
                          "tva_montant",
                          "tva",
                          "montantHT",
                          "creancier",
                          "client",
                          "companyName",
                          "address",
                          "articles")

    def __iter__(self):
        for key in self._dictkeys :
            yield key, getattr(self, key)

    def generateRandom(self) :
        min_date = datetime.date(year=2015, month=1, day=1)
        max_date = datetime.date(year=2035, month=1, day=1)

        self.dateFacturation = faker.date_between(start_date = min_date, end_date = max_date)
        self.dateEcheance = faker.date_between(start_date = self.dateFacturation, end_date = max_date)
        self.datePrestation = self.dateFacturation if rn.random()>.5 else faker.date_between(start_date = self.dateFacturation, end_date = max_date)
        self.dateEmission = faker.date_between(start_date = min_date, end_date = self.datePrestation)
        self.dateExpiration = faker.date_between(start_date = self.datePrestation, end_date = max_date)

        self.facture_id = f"FA-{str(self.dateFacturation)[:4]}-{rn.randint(0, 9999):04d}"
        self.devis_id = f"D-{str(self.dateEmission)[:4]}-{rn.randint(0,999):03d}"
        self.numero_document = rn.choice([self.facture_id, self.devis_id]) # Pour correspondance avec les normes du datalake
        date_format = rn.choice(["%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y", "%d / %m / %Y", "%d - %m - %Y", "%d / %m / %y", "%d - %m - %y"])
        self.dateFacturation = self.dateFacturation.strftime(date_format)
        self.dateEcheance = self.dateEcheance.strftime(date_format)
        self.datePrestation = self.datePrestation.strftime(date_format)
        self.dateEmission = self.dateEmission.strftime(date_format)
        self.dateExpiration = self.dateExpiration.strftime(date_format)

        
        self.articles = []
        for _ in range(rn.randint(1,10)) :
            article = rn.choice(ARTICLE_DESCRIPTIONS)
            if rn.random()>.2 :
                article += rn.choice(ARTICLE_CONNECTEURS) + rn.choice(ARTICLE_DOMAINES)
            prix = round(1/(rn.random()*200+1)*1000, 2)
            quantite = rn.randint(1,10)
            self.articles.append({"nom":article, "prix":prix, "quantite":quantite})

        self.montantHT = sum(article["prix"] * article["quantite"] for article in self.articles)
        self.montantHT = round(self.montantHT,2) if rn.random()<.95 else round(self.montantHT*(1+rn.random()/10),2)
        self.tva = rn.choice([round(rn.random()/5, 2), .2, .2])
        self.tva_montant = round(self.tva * self.montantHT, 2) if rn.random()<.95 else round(self.tva*(1+rn.random()/10) * self.montantHT, 2)
        self.montantTTC = round(self.montantHT + self.tva_montant, 2) if rn.random()<.95 else round((self.montantHT + self.tva_montant)*(1+rn.random()/10),2)

        creancier = Personne()
        creancier.generateRandom()
        self.obj_creancier = creancier
        self.creancier = dict(creancier)
        client = Personne()
        client.generateRandom()
        self.obj_client = client
        self.client = dict(client)

        # Pour correspondance avec les normes du datalake
        self.companyName = self.creancier["companyName"]
        self.address = self.creancier["address"]

    
    def display(self) :
        print(f"""
# FACTURE
              
    ID : {self.facture_id}
              
    DATE FACTURATION : {self.dateFacturation}
    DATE PRESTATION  : {self.datePrestation}
    DATE ECHEANCE    : {self.dateEcheance}

    MONTANT HT  : {self.montantHT} €
    TVA         : {self.tva_montant} €
    MONTANT TTC : {self.montantTTC} €
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
        self._dictkeys = ("siren",
                          "nic",
                          "siret",
                          "n_tva",
                          "nom",
                          "prenom",
                          "prenom_2",
                          "prenom_3",
                          "sexe",
                          "companyName",
                          "adresse",
                          "code_postal",
                          "commune",
                          "address",
                          "ape",
                          "iban",
                          "bic")

    def __iter__(self):
        for key in self._dictkeys :
            yield key, getattr(self, key)

    def generateRandom(self) :

        siret = rn.randint(0, 10**14 - 1)
        siret = f"{siret:014d}"
        self.siret = siret
        self.siren = siret[:9]
        self.nic = siret[9:]
        self.n_tva = 'FR' + str(round(rn.random()*100)) + (' ' if rn.random()>.5 else '') + self.siren

        self.prenom = faker.first_name()
        self.prenom_2 = '' if rn.random() < .75 else faker.first_name()
        self.prenom_3 = '' if rn.random() < .9 or self.prenom_2 == '' else faker.first_name()
        self.nom = faker.last_name()
        self.sexe = rn.choice(['M','F',''])

        self.companyName = rn.choice(["{} et fils", "{} & cie", "Chez {}", "{} & associés", "Boutiques {}", "Industries {}", "{} Company"]).format(rn.choice([self.nom, self.nom, self.nom, self.prenom]))

        self.adresse = faker.street_address()
        if self.adresse[0] not in ['1','2','3','4','5','6','7','8','9'] :
            self.adresse = str(rn.randint(1,9)) + ', ' + self.adresse
        self.code_postal = faker.postcode()
        self.commune = faker.city()

        self.address = f"{self.adresse} - {self.code_postal} {self.commune}" # Pour correspondance avec les normes du datalake

        self.ape = f"{int(rn.random()*5700):04d}" + ['A','B','C','D','Z'][int(rn.random()*5)]
        self.iban = f"FR{rn.randint(0,99):02d} {rni_low(max=99999,min=1000):05d} {rni_low(max=99999,min=1000):05d} {rni_low(max=9999999,min=10000):07d}{rn.choice(string.ascii_letters).upper()}{rni_low(max=99,min=1):02d} {rni_low(max=999,min=1):03d}"
        self.bic = f"{''.join(rn.choice(string.ascii_letters) for _ in range(2)).upper()}FR {''.join(rn.choice(string.ascii_letters) for _ in range(4)).upper()}{' '+''.join(rn.choice(string.ascii_letters) for _ in range(3)).upper() if rn.random()>.5 else ''}"
        

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