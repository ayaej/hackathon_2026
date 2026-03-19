import json
import random as rn
from random import random as rnd
from random import randint as rni
from random import choice as rnc
import os
import shutil

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, TA_LEFT, TA_CENTER, TA_RIGHT
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

    seed = rni(1,int(1e9))

    for doctype in ["facture","devis"] :

        # Récupération des données

        document = data[i]

        perturbateur = rni(0, len(data)-1)
        for key in document :
            if rnd() > .995 :
                document[key] = data[perturbateur][key]

        facture_id = document["facture_id"]
        devis_id = document["devis_id"]
        dateFacturation = document["dateFacturation"]
        datePrestation = document["datePrestation"]
        dateEmission = document["dateEmission"]
        dateExpiration = document["dateExpiration"]
        dateEcheance = document["dateEcheance"]
        montantHT = document["montantHT"]
        tva_montant = document["tva_montant"]
        tva = document["tva"]
        montantTTC = document["montantTTC"]

        articles = document["articles"]

        client = document["client"]
        nom_client = f"{client['prenom']} {client['prenom_2']} {client['prenom_3']} {client['nom']}"
        adresse_client_1 = f"{client['adresse']}"
        adresse_client_2 = f"{client['code_postal']} {client['commune']}"
        siren_client = f"{client['siren']}"
        n_tva_client = f"{client['n_tva']}"
        iban_client = f"{client['iban']}"
        bic_client = f"{client['bic']}"

        creancier = document["creancier"]
        nom_creancier = f"{creancier['prenom']} {creancier['prenom_2']} {creancier['prenom_3']} {creancier['nom']}"
        adresse_creancier_1 = f"{creancier['adresse']}"
        adresse_creancier_2 = f"{creancier['code_postal']} {creancier['commune']}"
        siren_creancier = f"{creancier['siren']}"
        iban_creancier = f"{creancier['iban']}"
        bic_creancier = f"{creancier['bic']}"

        if rnd()>.05 : rn.seed(seed)


        # Génération du PDF
        
        sideMargin = rni(30,50)
        doc = SimpleDocTemplate(f"pdf/{doctype}_{i}.pdf",
                                pagesize=A4,
                                rightMargin=sideMargin,
                                leftMargin=sideMargin,
                                topMargin=rni(30,60),
                                bottomMargin=rni(12,24))
        styles = getSampleStyleSheet()
        story = []

        wordWrap = ParagraphStyle(name="wordWrap", wordWrap='LTR')

        largeur_page = rni(160,200)

        ## Header

        bold_1, bold_2 = ("<b>", "</b>") if rnd() > 0.5 else ("", "")

        reference_document = f"{rnc(['Numéro :', 'N°', ''])} {facture_id if doctype=='facture' else devis_id}"
        if rnd() > .5 :
            titleStyle = ParagraphStyle(name="doc_title", fontSize=rni(10,20),
                                        alignment=rnc([TA_LEFT, TA_CENTER, TA_CENTER]),
                                        fontName=rnc(['Helvetica','Helvetica-Bold']))
            story.append(Paragraph(f"{doctype.upper()}", style=titleStyle))
            story.append(Spacer(1, rni(6,18)))
        else :
            reference_document = f"{doctype.capitalize()} {reference_document}"
        story.append(Paragraph(f"{bold_1}{reference_document}{bold_2}"))
        if doctype == "facture" :
            story.append(Paragraph(f"{bold_1}Date{' de facturation' if rnd()>.5 else ''} :{bold_2} {dateFacturation}", styles["Normal"]))
        elif doctype == "devis" :
            story.append(Paragraph(f"{bold_1}{rnc(['Émission', 'Date d’émission', 'Émis le'])} :{bold_2} {dateEmission}", styles["Normal"]))
        story.append(Spacer(1, rni(12,24)))

        bold_1, bold_2 = ("<b>", "</b>") if rnd() > 0.5 else ("", "")

        objet = Paragraph(f"{bold_1}{rnc(['Objet : ', ''])}{articles[rni(0,len(articles)-1)]['nom']}{bold_2}")
        objet_haut = True if rnd()>.25 else False
        if rnd()>.75 and objet_haut :
            story.append(objet)
            story.append(Spacer(1, rni(6,18)))

        header_client = f"{nom_client}<br/>{adresse_client_1}<br/>{adresse_client_2}"
        header_creancier = f"{nom_creancier}<br/>{adresse_creancier_1}<br/>{adresse_creancier_2}"

        if rnd() > .25 : header_client = bold_1 + rnc(["Client : ",
                                                                   "Nom du client : "]) + rnc(["<br/>", ""]) + bold_2 + header_client
        if rnd() > .25 : header_creancier = bold_1 + rnc(["À : ",
                                                                      "Créancier : ",
                                                                      "Vendeur : ",
                                                                      "Expéditeur : ",
                                                                      "Émetteur : "]) + rnc(["<br/>", ""]) + bold_2 + header_creancier

        if rnd() > .9 :
            header_client += f"<br/>N° SIREN : {siren_client}"
            header_creancier += f"<br/>N° SIREN : {siren_creancier}"

        if rnd() > .5 :
            header_client += f"<br/>IBAN : {iban_client}"
        if rnd() > .5 :
            header_client += f"<br/>BIC : {bic_client}"
        if rnd() > .5 :
            header_creancier += f"<br/>IBAN : {iban_creancier}"
        if rnd() > .5 :
            header_creancier += f"<br/>BIC : {bic_creancier}"

        if rnd() > .5 :
            header_client += f"<br/>N° TVA : {n_tva_client}"

        header_client = Paragraph(header_client, styles["Normal"])
        header_creancier = Paragraph(header_creancier, styles["Normal"])

        largeur_box = rnd()
        couleur_box = colors.white if rnd()>.75 else rnc([colors.black, colors.gray])
        creancier_visible = True if rnd()>.25 or doctype=="devis" else False
        deux_colonnes = True if rnd()>.25 else False
        if deux_colonnes :
            taille_col = rni(70,90)
            espace_droite = 0 if rnd()>.5 else rni(0,30)
            table_header = Table([[header_client, '', header_creancier, '']] if creancier_visible else [[header_client, '', Paragraph(""), '']], colWidths=[taille_col*mm, max((largeur_page-2*taille_col-espace_droite)*mm,0), taille_col*mm, espace_droite*mm])
            table_header.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                              ('BOX', (0,0), (0,0), largeur_box, couleur_box),
                                              ('BOX', (2,0), (2,0), largeur_box, couleur_box if creancier_visible else colors.white),]))
            story.append(table_header)
        else :
            story.append(header_client)
            if creancier_visible :
                story.append(Spacer(1, rni(6,18)))
                story.append(header_creancier)

        if rnd()>.75 and not objet_haut :
            story.append(Spacer(1, rni(6,18)))
            story.append(objet)

        story.append(Spacer(1, rni(12,36)))

        ## Tableau d'articles

        couleur_header = rnc([colors.gray, colors.skyblue, colors.lightblue, colors.lightcoral, colors.lightpink, colors.white, colors.white])
        couleur_footer = rnc([colors.beige, colors.lightcyan, colors.white, colors.white, colors.white])
        couleur_grille = rnc([colors.black, colors.black, colors.lightslategray, colors.gray])
        couleur_grille_int = rnc([couleur_grille, couleur_grille, colors.lightslategray, colors.gray, colors.whitesmoke, colors.white])

        tableau = [[f"{rnc(['Description','Produits','Désignation','Libellé'])}",
                    f"{rnc(['Quantité', 'Qté', 'Compte'])}",
                    f"Prix {rnc(['unitaire', 'unité', 'à l’unité'])}",
                    f"{rnc(['Total', 'Montant', 'Montant total'])}{rnc([' HT', ''])}"]]

        ddot = rnc([' :',''])

        for article in articles :
            tableau.append([article["nom"], str(article["quantite"]), f"{article['prix']:.2f} €", f"{(article['quantite']*article['prix']):.2f} €"])

        tableau.append(["", "", Paragraph(f"{rnc(['Total ', 'Montant total '])}{rnc(['HT', '(HT)', ''])}{ddot}", style=wordWrap), f"{montantHT:.2f} €"])
        tableau.append(["", "", Paragraph(f"{rnc(['TVA ', 'Montant TVA ', 'Montant de la TVA '])}{'('+str(int(tva*100))+' %) ' if rnd()>.5 else ''}{ddot}", style=wordWrap), f"{tva_montant:.2f} €"])
        tableau.append(["", "", Paragraph(f"{rnc(['Total ', 'Montant total '])}{rnc(['TTC', '(TTC)'])}{ddot}", style=wordWrap), f"{montantTTC:.2f} €"])

        taille_col = [100, rni(20,30), rni(30,40)]
        taille_col[0] = largeur_page - taille_col[1] - 2*taille_col[2]
        top_padding = rni(9,15)
        padding = rni(2,9)
        extension_grille = rnc([-1,-3])
        align_1 = rnc(['LEFT', 'CENTER'])
        align_2 = rnc([align_1, 'RIGHT'])

        table = Table(tableau, colWidths=[taille_col[0]*mm, taille_col[1]*mm, taille_col[2]*mm, taille_col[2]*mm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), couleur_header),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke if rnd()>.25 and couleur_header not in [colors.white] else colors.black),
            ('ALIGN', (0, 0), (-1, -1), align_1),
            ('VALIGN', (0, 0), (-1, -1), rnc(['TOP','MIDDLE','BOTTOM'])),
            ('ALIGN', (-2, 1), (-1, -1), align_2),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), rni(10,12)),
            ('FONTSIZE', (0, 1), (-1, -1), rni(8,10)),
            ('BOTTOMPADDING', (0, 0), (-1, 0), top_padding),
            ('TOPPADDING', (0, 0), (-1, 0), top_padding),
            ('BOTTOMPADDING', (0, 1), (-1, -1), padding),
            ('TOPPADDING', (0, 1), (-1, -1), padding),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('BACKGROUND', (rnc([0,-2]), -3), (-1, -1), couleur_footer),
            ('GRID', (0, 1), (-1, extension_grille), 1, couleur_grille_int),
            (rnc(['BOX','GRID']), (0, 0), (-1, extension_grille), 1, couleur_grille),
            ('BOX', (0, 0), (-1, 0), 1, couleur_grille),
            ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold' if rnd()>.5 else 'Helvetica'),
        ]))

        table_apres_footer = True if rnd()>.8 else False

        if not table_apres_footer :
            story.append(table)
            story.append(Spacer(1, rni(6,18)))

        ## Footer

        story.append(Paragraph(f"Date de {rnc(['prestation', 'livraison', 'résolution'])}{' prévue' if doctype=='devis' and rnd()>.5 else ''} : {datePrestation}", styles["Normal"]))

        if doctype == "facture" :
            story.append(Paragraph(f"{rnc(['Date d’échéance', 'Échéance'])}{rnc([' du paiement', ''])} : {dateEcheance}", styles["Normal"]))
        elif doctype == "devis" :
            story.append(Paragraph(f"{rnc(['Date d’expiration', 'Expiration', 'Date de limite de validité'])} : {dateExpiration}", styles["Normal"]))
        
        if table_apres_footer :
            story.append(Spacer(1, rni(6,18)))
            story.append(table)
            story.append(Spacer(1, rni(6,18)))

        story.append(Spacer(1, rni(12,96)))

        if doctype == "devis" :

            signatures = [['', '', '', '', '']]
            signatures[0][1] = Paragraph(f"Signature du client{' précédée de la mention ' + rnc(['« Lu et approuvé »','« Bon pour commande »','« Bon pour accord »']) if rnd()>.5 else ''}{ddot}", style=wordWrap)
            signatures[0][3] = Paragraph(f"Signature {rnc(['et cachet ',''])}{rnc(['du créancier','de l’entreprise','du vendeur','du prestataire'])}{ddot}", style=wordWrap)

            aligne_a_gauche = True if rnd() > .5 else False
            taille_col = [rni(40,60), rni(5,20), 0]
            taille_col[2] = largeur_page - 2*taille_col[0] - taille_col[1]
            couleur_box = rnc([colors.black, colors.gray, colors.white])
            largeur_box = rnd()
            table_signatures = Table(signatures, colWidths=[taille_col[2]*mm if not aligne_a_gauche else 0, taille_col[0]*mm, taille_col[1]*mm, taille_col[0]*mm, taille_col[2]*mm if aligne_a_gauche else 0])
            table_signatures.setStyle(TableStyle([
                ('BOX', (1,0), (1,0), largeur_box, couleur_box),
                ('BOX', (3,0), (3,0), largeur_box, couleur_box),
                ('BOTTOMPADDING', (0, 0), (-1, 0), taille_col[0]*mm*(rnd()*.4 + .4)),
                ('FONTSIZE', (0, 0), (-1, 0), rni(6,10)),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEADING', (0, 0), (-1, -1), rni(9,11)),
            ]))

            story.append(table_signatures)


        # Enregistrement

        doc.build(story)

        image = convert_from_path(f"pdf/{doctype}_{i}.pdf", dpi = rni(50,200))
        format = rnc(['jpeg','png','pdf'])
        image[0].save(f"pdf/{doctype}_image_{i}.{format}", format.upper())
