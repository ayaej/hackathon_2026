import json
import random as rn
import os
import shutil

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle

from pdf2image.pdf2image import convert_from_path


if not os.path.exists("dataset.json") :
    from generateDataset import generateDataset
    generateDataset()


with open("dataset.json", "r", encoding="utf-8") as f:
    data = json.load(f)

if os.path.isdir("pdf") :
    shutil.rmtree("pdf")
os.mkdir("pdf")


for i in range(5) :
# for i in range(len(data)) :

    seed = rn.randint(1,int(1e9))

    for doctype in ["facture","devis"] :

        # Récupération des données

        document = data[i]

        perturbateur = rn.randint(0, len(data)-1)
        for key in document :
            if rn.random() > .995 :
                document[key] = data[perturbateur][key]

        facture_id = document["facture_id"]
        devis_id = document["devis_id"]
        date_facturation = document["date_facturation"]
        date_prestation = document["date_prestation"]
        date_emission = document["date_emission"]
        date_expiration = document["date_expiration"]
        date_echeance = document["date_echeance"]
        montant_ht = document["montant_ht"]
        tva_montant = document["tva_montant"]
        tva_taux = document["tva_taux"]
        montant_ttc = document["montant_ttc"]

        articles = document["articles"]

        client = document["client"]
        nom_client = f"{client['prenom']} {client['prenom_2']} {client['prenom_3']} {client['nom']}"
        adresse_client_1 = f"{client['adresse']}"
        adresse_client_2 = f"{client['code_postal']} {client['commune']}"
        siren_client = f"{client['siren']}"
        n_tva_client = f"{client['n_tva']}"

        creancier = document["creancier"]
        nom_creancier = f"{creancier['prenom']} {creancier['prenom_2']} {creancier['prenom_3']} {creancier['nom']}"
        adresse_creancier_1 = f"{creancier['adresse']}"
        adresse_creancier_2 = f"{creancier['code_postal']} {creancier['commune']}"
        siren_creancier = f"{creancier['siren']}"

        rn.seed(seed)


        # Génération du PDF
        
        sideMargin = rn.randint(30,50)
        doc = SimpleDocTemplate(f"pdf/{doctype}_{i}.pdf",
                                pagesize=A4,
                                rightMargin=sideMargin,
                                leftMargin=sideMargin,
                                topMargin=rn.randint(30,60),
                                bottomMargin=rn.randint(12,24))
        styles = getSampleStyleSheet()
        story = []

        wordWrap = ParagraphStyle(name="wordWrap", wordWrap='LTR')

        largeur_page = rn.randint(160,200)

        ## Header

        bold_1, bold_2 = ("<b>", "</b>") if rn.random() > 0.5 else ("", "")

        story.append(Paragraph(f"{doctype.upper()}", styles["Title"]))
        story.append(Spacer(1, rn.randint(6,18)))
        story.append(Paragraph(f"{bold_1}{rn.choice(['Numéro :', 'N°', ''])} {facture_id if doctype=='facture' else devis_id}{bold_2}"))
        if doctype == "facture" :
            story.append(Paragraph(f"{bold_1}Date{' de facturation' if rn.random()>.5 else ''} :{bold_2} {date_facturation}", styles["Normal"]))
        elif doctype == "devis" :
            story.append(Paragraph(f"{bold_1}{rn.choice(['Émission', 'Date d\'émission', 'Émis le'])} :{bold_2} {date_emission}", styles["Normal"]))
        story.append(Spacer(1, rn.randint(12,24)))

        bold_1, bold_2 = ("<b>", "</b>") if rn.random() > 0.5 else ("", "")

        header_client = f"{nom_client}<br/>{adresse_client_1}<br/>{adresse_client_2}"
        header_creancier = f"{nom_creancier}<br/>{adresse_creancier_1}<br/>{adresse_creancier_2}"

        if rn.random() > .25 : header_client = bold_1 + rn.choice(["Client : ",
                                                                   "Nom du client : "]) + rn.choice(["<br/>", ""]) + bold_2 + header_client
        if rn.random() > .25 : header_creancier = bold_1 + rn.choice(["À : ",
                                                                      "Créancier : ",
                                                                      "Vendeur : ",
                                                                      "Expéditeur : ",
                                                                      "Émetteur : "]) + rn.choice(["<br/>", ""]) + bold_2 + header_creancier

        if rn.random() > .9 :
            header_client += f"<br/>N° SIREN : {siren_client}"
            header_creancier += f"<br/>N° SIREN : {siren_creancier}"

        if rn.random() > .5 :
            header_client += f"<br/>N° TVA : {n_tva_client}"

        header_client = Paragraph(header_client, styles["Normal"])
        header_creancier = Paragraph(header_creancier, styles["Normal"])

        largeur_box = rn.random()
        couleur_box = colors.white if rn.random()>.75 else rn.choice([colors.black, colors.gray])
        creancier_visible = True if rn.random()>.25 or doctype=="devis" else False
        deux_colonnes = True if rn.random()>.25 else False
        if deux_colonnes :
            taille_col = rn.randint(70,90)
            espace_droite = 0 if rn.random()>.5 else rn.randint(0,30)
            table_header = Table([[header_client, '', header_creancier, '']] if creancier_visible else [[header_client, '', Paragraph(""), '']], colWidths=[taille_col*mm, max((largeur_page-2*taille_col-espace_droite)*mm,0), taille_col*mm, espace_droite*mm])
            table_header.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                              ('BOX', (0,0), (0,0), largeur_box, couleur_box),
                                              ('BOX', (2,0), (2,0), largeur_box, couleur_box if creancier_visible else colors.white),]))
            story.append(table_header)
        else :
            story.append(header_client)
            if creancier_visible :
                story.append(Spacer(1, rn.randint(6,18)))
                story.append(header_creancier)

        story.append(Spacer(1, rn.randint(12,36)))

        ## Tableau d'articles

        couleur_header = rn.choice([colors.gray, colors.skyblue, colors.lightblue, colors.lightcoral, colors.lightpink, colors.white, colors.white])
        couleur_footer = rn.choice([colors.beige, colors.lightcyan, colors.white, colors.white, colors.white])
        couleur_grille = rn.choice([colors.black, colors.black, colors.lightslategray, colors.gray])
        couleur_grille_int = rn.choice([couleur_grille, couleur_grille, colors.lightslategray, colors.gray, colors.whitesmoke, colors.white])

        tableau = [["Description", "Quantité", "Prix unitaire", "Total"]]

        ddot = rn.choice([' :',''])

        for article in articles :
            tableau.append([article["nom"], str(article["quantite"]), f"{article['prix']:.2f} €", f"{(article['quantite']*article['prix']):.2f} €"])

        tableau.append(["", "", Paragraph(f"{rn.choice(['Total ', 'Montant total '])}{rn.choice(['HT', '(HT)', ''])}{ddot}", style=wordWrap), f"{montant_ht:.2f} €"])
        tableau.append(["", "", Paragraph(f"{rn.choice(['TVA ', 'Montant TVA ', 'Montant de la TVA '])}{'('+str(int(tva_taux*100))+' %) ' if rn.random()>.5 else ''}{ddot}", style=wordWrap), f"{tva_montant:.2f} €"])
        tableau.append(["", "", Paragraph(f"{rn.choice(['Total ', 'Montant total '])}{rn.choice(['TTC', '(TTC)'])}{ddot}", style=wordWrap), f"{montant_ttc:.2f} €"])

        taille_col = [100, rn.randint(20,30), rn.randint(30,40)]
        taille_col[0] = largeur_page - taille_col[1] - 2*taille_col[2]
        top_padding = rn.randint(9,15)
        padding = rn.randint(2,9)
        extension_grille = rn.choice([-1,-3])
        align_1 = rn.choice(['LEFT', 'CENTER'])
        align_2 = rn.choice([align_1, 'RIGHT'])

        table = Table(tableau, colWidths=[taille_col[0]*mm, taille_col[1]*mm, taille_col[2]*mm, taille_col[2]*mm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), couleur_header),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke if rn.random()>.25 and couleur_header not in [colors.white] else colors.black),
            ('ALIGN', (0, 0), (-1, -1), align_1),
            ('VALIGN', (0, 0), (-1, -1), rn.choice(['TOP','MIDDLE','BOTTOM'])),
            ('ALIGN', (-2, 1), (-1, -1), align_2),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), rn.randint(10,12)),
            ('FONTSIZE', (0, 1), (-1, -1), rn.randint(8,10)),
            ('BOTTOMPADDING', (0, 0), (-1, 0), top_padding),
            ('TOPPADDING', (0, 0), (-1, 0), top_padding),
            ('BOTTOMPADDING', (0, 1), (-1, -1), padding),
            ('TOPPADDING', (0, 1), (-1, -1), padding),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('BACKGROUND', (0, -3), (-1, -1), couleur_footer),
            ('GRID', (0, 1), (-1, extension_grille), 1, couleur_grille_int),
            (rn.choice(['BOX','GRID']), (0, 0), (-1, extension_grille), 1, couleur_grille),
            ('BOX', (0, 0), (-1, 0), 1, couleur_grille),
            ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold' if rn.random()>.5 else 'Helvetica'),
        ]))

        story.append(table)

        ## Footer

        story.append(Spacer(1, rn.randint(6,18)))
        story.append(Paragraph(f"Date de {rn.choice(['prestation', 'livraison', 'résolution'])}{' prévue' if doctype=='devis' and rn.random()>.5 else ''} : {date_prestation}", styles["Normal"]))

        if doctype == "facture" :
            story.append(Paragraph(f"{rn.choice(['Date d\'échéance', 'Échéance'])}{rn.choice([' du paiement', ''])} : {date_echeance}", styles["Normal"]))
        elif doctype == "devis" :
            story.append(Paragraph(f"{rn.choice(['Date d\'expiration', 'Expiration', 'Date de limite de validité'])} : {date_expiration}", styles["Normal"]))
        
        story.append(Spacer(1, rn.randint(12,96)))

        if doctype == "devis" :

            signatures = [['', '', '', '', '']]
            signatures[0][1] = Paragraph(f"Signature du client{' précédée de la mention ' + rn.choice(['«\xA0Lu et approuvé\xA0»','«\xA0Bon pour commande\xA0»','«\xA0Bon pour accord\xA0»']) if rn.random()>.5 else ''}{ddot}", style=wordWrap)
            signatures[0][3] = Paragraph(f"Signature {rn.choice(['et cachet ',''])}{rn.choice(['du créancier','de l\'entreprise','du vendeur','du prestataire'])}{ddot}", style=wordWrap)

            aligne_a_gauche = True if rn.random() > .5 else False
            taille_col = [rn.randint(40,60), rn.randint(5,20), 0]
            taille_col[2] = largeur_page - 2*taille_col[0] - taille_col[1]
            couleur_box = rn.choice([colors.black, colors.gray, colors.white])
            largeur_box = rn.random()
            table_signatures = Table(signatures, colWidths=[taille_col[2]*mm if not aligne_a_gauche else 0, taille_col[0]*mm, taille_col[1]*mm, taille_col[0]*mm, taille_col[2]*mm if aligne_a_gauche else 0])
            table_signatures.setStyle(TableStyle([
                ('BOX', (1,0), (1,0), largeur_box, couleur_box),
                ('BOX', (3,0), (3,0), largeur_box, couleur_box),
                ('BOTTOMPADDING', (0, 0), (-1, 0), taille_col[0]*mm*(rn.random()*.4 + .4)),
                ('FONTSIZE', (0, 0), (-1, 0), rn.randint(6,10)),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEADING', (0, 0), (-1, -1), rn.randint(9,11)),
            ]))

            story.append(table_signatures)


        # Enregistrement

        doc.build(story)

        image = convert_from_path(f"pdf/{doctype}_{i}.pdf", dpi = rn.randint(50,200))
        format = rn.choice(['jpeg','png','pdf'])
        image[0].save(f"pdf/{doctype}_image_{i}.{format}", format.upper())
