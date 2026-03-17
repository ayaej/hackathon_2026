import json
import random
import os
import shutil

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import mm
from reportlab.lib import colors

from pdf2image import convert_from_path

with open("dataset.json", "r", encoding="utf-8") as f:
    data = json.load(f)

if os.path.isdir("pdf") :
    shutil.rmtree("pdf")
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
    adresse_creancier_2 = f"{creancier['code_postal']} {creancier['commune']}"
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

    bold_1 = ""
    bold_2 = ""
    if random.random()>.5 :
        bold_1 = "<b>"
        bold_2 = "</b>"

    story.append(Paragraph("FACTURE", styles["Title"]))
    story.append(Spacer(1, random.randint(6,18)))
    story.append(Paragraph(f"{bold_1}{random.choice(['Numéro :', 'N°', ''])} {document_id}{bold_2}"))
    story.append(Paragraph(f"{bold_1}Date{' de facturation' if random.random()>.5 else ''} :{bold_2} {date_facturation}", styles["Normal"]))
    story.append(Spacer(1, random.randint(6,18)))

    if random.random()>.5 :
        bold_1 = "<b>"
        bold_2 = "</b>"

    header_client = f"{nom_client}<br/>{adresse_client_1}<br/>{adresse_client_2}"
    header_creancier = f"{nom_creancier}<br/>{adresse_creancier_1}<br/>{adresse_creancier_2}"

    if(random.random()>.25) : header_client = bold_1 + random.choice(["Client : ",
                                                                      "Nom du client : "]) + random.choice(["<br/>", ""]) + bold_2 + header_client
    if(random.random()>.25) : header_creancier = bold_1 + random.choice(["A : ",
                                                                         "Créancier : ",
                                                                         "Vendeur : ",
                                                                         "Expéditeur : ",
                                                                         "Emetteur : "]) + random.choice(["<br/>", ""]) + bold_2 + header_creancier

    if(random.random()>.9) :
        header_client += f"<br/>N° SIREN : {siren_client}"
        header_creancier += f"<br/>N° SIREN : {siren_creancier}"

    if(random.random()>.5) :
        header_client += f"<br/>N° TVA : {n_tva_client}"

    header_client = Paragraph(header_client, styles["Normal"])
    header_creancier = Paragraph(header_creancier, styles["Normal"])

    taille_col = random.randint(80,100)
    table_header = Table([[header_client, header_creancier]] if random.random()>.25 else [[header_client, Paragraph("")]], colWidths=[taille_col*mm, taille_col*mm])
    table_header.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))

    story.append(table_header)

    story.append(Spacer(1, random.randint(12,36)))

    ## Tableau d'articles

    couleur_header = random.choice([colors.gray, colors.skyblue, colors.lightblue, colors.lightcoral, colors.lightpink, colors.khaki])
    couleur_footer = random.choice([colors.beige, colors.lightcyan, colors.white, colors.white, colors.white])
    couleur_grille = random.choice([colors.black, colors.black, colors.lightslategray, colors.gray])
    couleur_grille_int = random.choice([couleur_grille, couleur_grille, colors.lightslategray, colors.gray, colors.whitesmoke, colors.white])

    tableau = [["Description", "Quantité", "Prix unitaire", "Total"]]

    ddot = random.choice([' :',''])

    for article in articles :
        tableau.append([article["nom"], str(article["quantite"]), f"{article['prix']:.2f} €", f"{(article['quantite']*article['prix']):.2f} €"])

    tableau.append(["", "", f"{random.choice(['Total ', 'Montant total '])}{random.choice(['HT', '(HT)', ''])}{ddot}", f"{montant_ht:.2f} €"])
    tableau.append(["", "", f"{random.choice(['TVA ', 'Montant TVA ', 'Montant de la TVA '])}{ddot}", f"{tva:.2f} €"])
    tableau.append(["", "", f"{random.choice(['Total ', 'Montant total '])}{random.choice(['TTC', '(TTC)'])}{ddot}", f"{montant_ttc:.2f} €"])

    largeur_tableau = random.randint(160,200)
    taille_col = [100, random.randint(20,30), random.randint(30,40)]
    taille_col[0] = largeur_tableau - taille_col[1] - 2*taille_col[2]
    top_padding = random.randint(9,15)
    padding = random.randint(2,9)
    extension_grille = random.choice([-1,-3])
    align_1 = random.choice(['LEFT', 'CENTER'])
    align_2 = random.choice([align_1, 'RIGHT'])

    table = Table(tableau, colWidths=[taille_col[0]*mm, taille_col[1]*mm, taille_col[2]*mm, taille_col[2]*mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), couleur_header),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke if random.random()>.25 else colors.black),
        ('ALIGN', (0, 0), (-1, -1), align_1),
        ('ALIGN', (-2, 1), (-1, -1), align_2),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), random.randint(10,12)),
        ('FONTSIZE', (0, 1), (-1, -1), random.randint(8,10)),
        ('BOTTOMPADDING', (0, 0), (-1, 0), top_padding),
        ('TOPPADDING', (0, 0), (-1, 0), top_padding),
        ('BOTTOMPADDING', (0, 1), (-1, -1), padding),
        ('TOPPADDING', (0, 1), (-1, -1), padding),
        ('BACKGROUND', (0, -3), (-1, -1), couleur_footer),
        ('INNERGRID', (0, 1), (-1, extension_grille), 1, couleur_grille_int),
        (random.choice(['BOX','GRID']), (0, 0), (-1, extension_grille), 1, couleur_grille),
        ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold' if random.random()>.5 else 'Helvetica'),
    ]))

    story.append(table)

    ## Footer

    story.append(Spacer(1, random.randint(6,18)))
    story.append(Paragraph(f"Date de {random.choice(['prestation', 'livraison', 'résolution'])} : {date_prestation}", styles["Normal"]))
    story.append(Paragraph(f"{random.choice(['Date d\'échéance', 'Echéance'])}{random.choice(['du paiement', ''])} : {date_echeance}", styles["Normal"]))

    story.append(Spacer(1, random.randint(12,36)))


    # Enregistrement

    doc.build(story)

    image = convert_from_path(f"pdf/facture_{i}.pdf")
    format = random.choice(['jpeg','png','pdf'])
    image[0].save(f"pdf/facture_image_{i}.{format}", format.upper())