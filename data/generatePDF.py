import json
import random
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import mm
from reportlab.lib import colors

from pdf2image import convert_from_path

with open("dataset.json", "r", encoding="utf-8") as f:
    data = json.load(f)

if not os.path.isdir("pdf") :
    os.mkdir("pdf")


for i in range(5) :
# for i in range(len(data)) :

    # Récupération des données

    facture = data[i]
    document_id = facture["document_id"]
    date_facturation = facture["date_facturation"]
    date_prestation = facture["date_prestation"]
    date_echeance = facture["date_echeance"]
    montant_ht = facture["montant_ht"]
    tva = facture["tva"]
    montant_ttc = facture["montant_ttc"]

    articles = facture["articles"]

    client = facture["client"]
    nom_client = f"{client['prenom']} {client['prenom_2']} {client['prenom_3']} {client['nom']}"
    adresse_client_1 = f"{client['adresse']}"
    adresse_client_2 = f"{client['code_postal']} {client['commune']}"
    siren_client = f"{client['siren']}"
    n_tva_client = f"{client['n_tva']}"

    creancier = facture["creancier"]
    nom_creancier = f"{creancier['prenom']} {creancier['prenom_2']} {creancier['prenom_3']} {creancier['nom']}"
    adresse_creancier_1 = f"{creancier['adresse']}"
    adresse_creancier_2 = f"{creancier["code_postal"]} {creancier['commune']}"
    siren_creancier = f"{creancier['siren']}"


    # Génération du PDF
    doc = SimpleDocTemplate(f"pdf/facture_{i}.pdf",
                            pagesize=A4,
                            rightMargin=random.randint(20,40),
                            leftMargin=random.randint(20,40),
                            topMargin=random.randint(20,40),
                            bottomMargin=random.randint(12,24))
    styles = getSampleStyleSheet()
    story = []

    ## Header

    story.append(Paragraph("FACTURE", styles["Title"]))
    story.append(Spacer(1, random.randint(6,18)))
    story.append(Paragraph(f"Numéro : {document_id}<br/>Date de facturation : {date_facturation}", styles["Normal"]))
    story.append(Spacer(1, random.randint(6,18)))

    header_client = f"{nom_client}<br/>{adresse_client_1}<br/>{adresse_client_2}"
    header_creancier = f"{nom_creancier}<br/>{adresse_creancier_1}<br/>{adresse_creancier_2}"

    if(random.random()>.25) : header_client =random.choice(["Client : ",
                                                            "Nom du client : "]) + random.choice(["<br/>", ""]) + header_client
    if(random.random()>.25) : header_creancier = random.choice(["A : ",
                                                                "Créancier : ",
                                                                "Vendeur : ",
                                                                "Expéditeur : ",
                                                                "Emetteur : "]) + random.choice(["<br/>", ""]) + header_creancier

    if(random.random()>.9) :
        header_client += f"<br/>N° SIREN : {siren_client}"
        header_creancier += f"<br/>N° SIREN : {siren_creancier}"

    if(random.random()>.5) :
        header_client += f"<br/>N° TVA : {n_tva_client}"

    header_client = Paragraph(header_client, styles["Normal"])
    header_creancier = Paragraph(header_creancier, styles["Normal"])


    table_header = Table([[header_client, header_creancier]] if random.random()>.25 else [[header_client, Paragraph("")]], colWidths=[90*mm, 90*mm])
    table_header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(table_header)

    story.append(Spacer(1, random.randint(12,36)))

    ## Tableau d'articles

    couleur_header = random.choice([colors.gray, colors.skyblue, colors.lightblue, colors.lightcoral, colors.lightpink])
    couleur_footer = random.choice([colors.beige, colors.white, colors.white, colors.lightcyan])
    couleur_grille = random.choice([colors.black, colors.black, colors.lightslategray, colors.gray])
    couleur_grille_int = random.choice([couleur_grille, couleur_grille, colors.lightslategray, colors.gray, colors.whitesmoke])

    tableau = [["Description", "Quantité", "Prix unitaire", "Total"]]

    for article in articles :
        tableau.append([article["nom"], str(article["quantite"]), f"{article['prix']:.2f} €", f"{(article['quantite']*article['prix']):.2f} €"])

    tableau.append(["", "", "Total HT:", f"{montant_ht:.2f} €"])
    tableau.append(["", "", "TVA :", f"{tva:.2f} €"])
    tableau.append(["", "", "Total TTC:", f"{montant_ttc:.2f} €"])

    largeur_tableau = random.randint(150,200)
    taille_col = [100, random.randint(15,25), random.randint(25,35)]
    taille_col[0] = largeur_tableau - taille_col[1] - 2*taille_col[2]
    table = Table(tableau, colWidths=[taille_col[0]*mm, taille_col[1]*mm, taille_col[2]*mm, taille_col[2]*mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), couleur_header),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), random.choice(['LEFT', 'CENTER'])),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), random.randint(9,15)),
        ('BACKGROUND', (0, -3), (-1, -1), couleur_footer),
        ('INNERGRID', (0, 0), (-1, -3), 1, couleur_grille_int),
        ('GRID', (0, 0), (-1, -3), 1, couleur_grille),
    ]))

    story.append(table)

    story.append(Spacer(1, random.randint(6,18)))
    story.append(Paragraph(f"Date de prestation : {date_prestation}", styles["Normal"]))
    story.append(Paragraph(f"Date d'échéance du paiement : {date_echeance}", styles["Normal"]))

    story.append(Spacer(1, random.randint(12,36)))


    doc.build(story)

    image = convert_from_path(f"pdf/facture_{i}.pdf")
    image[0].save('pdf/facture_image_'+ str(i) +'.pdf', 'PDF')