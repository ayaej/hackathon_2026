from faker import Faker
import random
import datetime
import json


faker = Faker('fr_FR')

class Facture :
    def __init__(self) :
        self._dictkeys = ("document_id", "date_facturation","date_echeance","date_prestation","montant_ttc","tva","montant_ht","creancier","client")

    def __iter__(self):
        for key in self._dictkeys :
            yield key, getattr(self, key)

    def generateRandom(self) :

        # Génération des dates
        min_date = datetime.date(year=2015, month=1, day=1)
        max_date = datetime.date(year=2035, month=1, day=1)
        self.date_facturation = faker.date_between(start_date = min_date, end_date = max_date)
        self.date_echeance = faker.date_between(start_date = self.date_facturation, end_date = max_date)
        self.date_prestation = self.date_facturation if random.random()>.5 else faker.date_between(start_date = self.date_facturation, end_date = max_date)
        self.date_facturation = str(self.date_facturation)
        self.date_echeance = str(self.date_echeance)
        self.date_prestation = str(self.date_prestation)
        
        self.document_id = f"FA-{self.date_facturation[:4]}-{random.randint(0, 9999):04d}"

        # Génération des montants
        self.montant_ht = round(random.random()*10000, 2)
        self.tva = round(random.random()/10 * self.montant_ht, 2)
        self.montant_ttc = round(self.montant_ht + self.tva, 2)

        # Génération des parties prenantes
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
              
    ID : {self.document_id}
              
    DATE FACTURATION : {self.date_facturation}
    DATE PRESTATION  : {self.date_prestation}
    DATE ECHEANCE    : {self.date_echeance}

    MONTANT HT  : {self.montant_ht} €
    TVA         : {self.tva} €
    MONTANT TTC : {self.montant_ttc} €
    """)
        print("# CREANCIER :")
        self.obj_creancier.display()
        print("# CLIENT :")
        self.obj_client.display()


class Personne :
    def __init__(self) :
        self._dictkeys = ("siren","nic","siret","n_tva","nom","prenom","prenom_2","prenom_3","sexe","adresse","code_postal","commune","ape")

    def __iter__(self):
        for key in self._dictkeys :
            yield key, getattr(self, key)

    def generateRandom(self) :

        # Génération du SIRET (SIREN + NIC)
        siret = random.randint(0, 10**14 - 1)
        siret = f"{siret:014d}"
        self.siret = siret
        self.siren = siret[:9]
        self.nic = siret[9:]
        self.n_tva = 'FR' + str(round(random.random()*100)) + ' ' + self.siren

        # Génération de la personnes
        self.prenom = faker.first_name()
        self.prenom_2 = '' if random.random() < .75 else faker.first_name()
        self.prenom_3 = '' if random.random() < .9 or self.prenom_2 == '' else faker.first_name()
        self.nom = faker.last_name()
        self.sexe = random.choice(['M','F',''])

        # Génération de l'adresse
        self.adresse = faker.street_address()
        self.code_postal = faker.postcode()
        self.commune = faker.city()

        # Génération de l'activité
        self.ape = f"{int(random.random()*5700):04d}" + ['A','B','C','D','Z'][int(random.random()*5)]

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


# facture = Facture()
# facture.generateRandom()
# facture.display()

liste = []
for _ in range(100) :
    facture = Facture()
    facture.generateRandom()
    liste.append(dict(facture))

with open("dataset.json", "w", encoding="utf-8") as f:
    json.dump(liste, f, ensure_ascii=False, indent=4)
