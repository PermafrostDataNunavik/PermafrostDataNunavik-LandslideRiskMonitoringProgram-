# -*- coding: utf-8 -*-
"""
Created on Wed Sept 28  08:54:46 2021

@author: Sarah Gauthier et Michel Allard
sarah.gauthier.1@ulaval.ca
Centre d'études nordiques, Université Laval

Classe pour la création d'un rapport journalier avec le statut de transmission 
des stations (active ou inactive) et pour l'envoi du signal d'alerte au besoin 
à la personne contact choisi. 

# =============================================================================
#  CE MODULE EST EN DÉVELOPPEMENT ET DOIT ÊTRE ADAPTÉ EN FONCTION DE LA STATION 
#  DE SUIVI (CLIMATIQUE, THERMIQUE, ETC.) DONT LES DONNÉES DOIVENT ÊTRE 
#  RÉCUPÉRÉES ET AUSSI DU TYPE DE DONNÉES À TRAITER. 
# =============================================================================

"""

from fpdf import FPDF
import pandas as pd
import matplotlib.pyplot as plt
from pandas.plotting import table
import yagmail
import dataframe_image as dfi

class AlerteRisqueCourriel():
    
    def __init__(self, destinataire, repertoire):
        
        # Entrer le chemin absolue du répertoire
        self.repertoire = repertoire
        
        # Personne-ressource responsable du suivi du risque de glissement de terrain. À modifier si changement.
        self.responsable_projet = 'Sarah Gauthier, sarah.gauthier.1@ulaval.ca'
        
        # Personne à qui on envoie le courriel pour avertir du niveau de risque de glissement
        self.destinataire = destinataire
        self.date = pd.to_datetime('today').date()

# =============================================================================
#         degel = pd.read_csv(f'{self.repertoire}Station_Data/Max_Degel/Max_Degel_{station}_tsol.csv')
# =============================================================================
        
        # Emplacement des fichiers
        self.logo_cen = f'{self.repertoire}Rapport_PDF/logo_cen.png'

        # Fichers de données
        self.df_indices_clim = pd.read_csv(f'{self.repertoire}Station_Data/CEN_SILA/Synthese_saisons_programme.csv')
        self.df_sila = pd.read_csv(f'{self.repertoire}Station_Data/CEN_SILA/SILA_Salluit_AirTemp.csv')
        
        # Lecture du fichier avec le statut d'envoi de la préalerte
        self.fichier_statut_prealerte = f'{self.repertoire}Rapport_PDF/statut_courriel_prealerte.txt'
        lecture_prealerte = open(self.fichier_statut_prealerte, 'r')
        self.statut_prealerte = lecture_prealerte.readline()
        lecture_prealerte.close()  # Fermeture du fichier pour pouvoir réécrire le nouveau statut
        
        # Lecture du fichier avec le statut d'envoi de l'alerte
        self.fichier_statut_alerte = f'{self.repertoire}Rapport_PDF/statut_courriel_alerte.txt'
        lecture_alerte = open(self.fichier_statut_alerte, 'r')
        self.statut_alerte = lecture_alerte.readline()
        lecture_alerte.close()  # Fermeture du fichier pour pouvoir réécrire le nouveau statut
        
        # Rapports PDF
        self.rapport_niveau_risque = f'{self.repertoire}Rapport_PDF/risque_glissement_salluit.pdf'
    
        # Variable à publier dans le rapport
        self.date_sila = pd.to_datetime(self.df_sila['Date'].iloc[-1]).date()
        self.niveau_risque = self.df_indices_clim['NiveauRisque'].iloc[-1]
        self.date_degel = pd.to_datetime(self.df_indices_clim['DateDegel'].iloc[-1]).date()
        self.cumul_djd = self.df_indices_clim['TotalDegel'].iloc[-1]
        self.variation_cumul = round(self.df_indices_clim['VariationCumul'].iloc[-1], 2)
# =============================================================================
#         self.profondeur_degel = round(self.degel['MaxDegel'].iloc[-1], 2)
# =============================================================================
        
        # Lien URL vers du tableau de bord en ligne pour le suivi du niveau de risque et des indices climatiques        
        self.url = 'https://bit.ly/Suivi-risque-glissement-de-terrain_Salluit-Nunavik'

        # Création du PDF
        self.pdf = FPDF(format = 'Letter')
        
    def generer_rapports(self):
        """
        Méthode principale pour créer les deux rapports (statut de transmission et niveau de risque)
        pdf et envoyer par courriel s'il y a un risque de glissement de terrain. 
        """
        
        # Création des graphiques avec les données des 14 derniers jours
        self.graphiques(self.graphique_tair)
        self.graphiques(self.graphique_cumuldjd)
        
        # Rapport avec le niveau de risque, les indices climatiques et les graphiques
        self.rapport_risque_glissement()

        # Méthode pour évaluer le niveau de risque de glissement et envoyer une alerte au besoin
        self.alerte_risque_glissement()
        
    def titre(self, pdf, risque = False):
        """
        Création de l'entête du PDF avec la bonne police et la date du rapport. 
        """
        
        ### Titre ###
        pdf.set_font('Arial', 'B', 16)
        pdf.ln(20)
        if risque == True:
            pdf.write(5, 'Risque de glissement de terrain : Salluit, Nunavik')
    
        else:
            pdf.write(5, 'Statut pour la transmission de données : Salluit, Nunavik')
        
        pdf.ln(10)
        pdf.set_font('Arial', 'B', 16)
        pdf.write(4, f'Rapport produit le {self.date.day} {pd.to_datetime("today").month_name(locale = "French")} {self.date.year}')
        pdf.ln(20)
        
        # Retourne le PDF avec l'entête
        return pdf
    
    def statut_station(self, df, station):
        """
        Détermine la dernière date de transmission. Si la transmission de données a été interrompue 
        pendant plus de 10 jours, calcul le nombre de jour d'interruption de la station inactive.
        """
    
        date_df = pd.to_datetime(df['Date'].iloc[-1]).date()
        
        difference_jours = (self.date - date_df).days
        
        # Si la différence de jours entre la date d'aujourd'hui et la dernière enregistrée dans le fichier excède 10 jours:
        if difference_jours > 10:
            statut = f'Dernière transmission {date_df}. La station {station} est inactive depuis {difference_jours} jours.'
        
        # Sinon, on indique simplement la dernière date de transmission
        else: 
            statut = f'Dernières données disponibles en date du {date_df}. La station est active.'
        
        return statut

    def station_sila(self):
        
        station = 'SILA'
        statut = self.statut_station(self.df_sila, station)
        donnees = self.df_sila.iloc[-5:, 0:10]
        dfi.export(donnees, f'{self.repertoire}Rapport_PDF/Tableau_donnees/{station}.png')
        
        self.pdf_risque.set_font('Arial', 'B', 14)
        
        self.pdf_risque.add_page()
        self.pdf_risque.image(self.logo_cen, 10, 5, 210/10)
        self.titre(self.pdf_risque)
        
        self.pdf_risque.cell(40, 10, station, ln = 20)
        
        self.pdf_risque.set_font('Arial', 'I', 11)
        self.pdf_risque.cell(40, 10, statut, ln = 20)
        
        self.pdf_risque.image(f'{self.repertoire}Rapport_PDF/Tableau_donnees/{station}.png', 10, 80, 160)
        
    def graphiques(self, graphique):
        """
        Création des graphiques à mettre dans les rapports.
        ----------
        graphique (str) : Nom du fichier du graphique à enregistrer
        """
        
        idx = self.df_sila.index[-14:].tolist()
        date = self.df_sila.Date[-14:].tolist()
        
        if graphique == self.graphique_tair:
            
            self.df_sila.SILA[-14:].plot.line(color = 'black', marker = '.', markersize=10, markerfacecolor='white')
            plt.rcParams["font.family"] = 'arial'
            plt.title('Température de l\'air (°C) - Salluit SILA')
            plt.ylabel('TMJA (°C)')
            plt.xticks(idx, date)
            plt.xticks(rotation=90)
            plt.grid(linestyle=':', linewidth=1)
            plt.tight_layout()
            
            plt.savefig(graphique)
            plt.clf()

        if graphique == self.graphique_cumuldjd:
            
            self.df_sila.CUMUL_DJ[-14:].plot.line(color = 'black', marker = '.', markersize=10, markerfacecolor='white')
            plt.rcParams["font.family"] = 'arial'
            plt.title('Cumul degrés-jour de dégel - Salluit SILA') 
            plt.ylabel('DJD (°C)')
            # plt.xticks(mois_gel, nom_gel)
            plt.xticks(idx, date)
            plt.xticks(rotation=90)
            plt.grid(linestyle=':', linewidth=1)
            # plt.ylim(0, 4000)
            plt.tight_layout()
            
            plt.savefig(graphique)
            plt.clf()
            
    def rapport_risque_glissement(self):
        
        # Création d'un PDF format lettre
        self.pdf_risque = FPDF(format = 'Letter')
        
# =============================================================================
#         # PREMIÈRE PAGE : Niveau de risque et indices climatiques
# =============================================================================
        
        # MISE EN FORME DU DOCUMENT        
        self.pdf_risque.add_page()
        self.pdf_risque.image(self.logo_cen, 10, 5, 210/10)
        self.titre(self.pdf_risque, risque = True)
        self.pdf_risque.set_font('Arial', '', 14)
        
        # NIVEAU DE RISQUE EN DATE DU 
        message_risque = f'Le niveau de risque calculé avec les données du {self.date_sila} est :'
        self.pdf_risque.write(5, message_risque)
        self.pdf_risque.ln(10)
    
        self.pdf_risque.set_font('Arial', 'B', 24)
        self.pdf_risque.cell(40, 10, self.niveau_risque, ln = 30)
        
        # INDICE CLIM : CUMUL DJD
        self.pdf_risque.set_font('Arial', '', 14)
        self.pdf_risque.ln(20)
        
        message_cumul = f'Cumul de degrés-jour de dégel depuis le début de la saison le {self.date_degel} :'
        self.pdf_risque.write(5, message_cumul)
        self.pdf_risque.ln(10)
        
        self.pdf_risque.set_font('Arial', 'B', 24)
        self.pdf_risque.cell(40, 10, f'{self.cumul_djd}', ln = 30)
        
        # POURCENTAGE DE VARIATION PRP À L'ANNÉE PRÉCÉDENTE
        self.pdf_risque.set_font('Arial', '', 14)
        self.pdf_risque.ln(20)
    
        message_variation = 'Pourcentage de variation du cumul de degrés-jour par rapport à l\'année précédente :'
        self.pdf_risque.write(5, message_variation)
        self.pdf_risque.ln(10)
        
        self.pdf_risque.set_font('Arial', 'B', 24)
        self.pdf_risque.cell(40, 10, f'{self.variation_cumul} %', ln = 30)
    
        # DASHBOARD EN LIGNE
        self.pdf_risque.set_font('Arial', '', 14)
        self.pdf_risque.ln(20)
        message_dashboard = 'Consulter les graphiques sur la page suivante ou le tableau de bord pour le suivi des indices climatiques et du niveau de risque de glissement de terrain à Salluit :'
        self.pdf_risque.write(5, message_dashboard)
        self.pdf_risque.ln(10)
        
        self.pdf_risque.set_font('Arial', 'B', 12)
        self.pdf_risque.cell(40, 10, f'{self.url}', ln = 30)
        self.pdf_risque.ln(20)
    
# =============================================================================
#         # DEUXIÈME PAGE : Graphiques de température de l'air et du cumul DJD
# =============================================================================
        
        # ajouter graphique température de l'air des 14 derniers jours + cumul
        self.pdf_risque.add_page()
        self.pdf_risque.image(self.graphique_tair, 25, 10, 160)
        self.pdf_risque.image(self.graphique_cumuldjd, 25, 120, 160)

# =============================================================================
#         # TROISIÈME PAGE : Statut de transmission de la station SILA et données récentes
# =============================================================================
        
        self.station_sila()

        # Écriture du rapport de 3 pages
        self.ecrire_pdf(self.pdf_risque, self.rapport_niveau_risque)
    
    def alerte_risque_glissement(self):
        """
        Déterminer si le niveau de risque est assez élevé pour envoyer le courriel
        et écriture du statut d'envoi du signal de préalerte et d'alerte.
        """
        if self.variation_cumul >= 25 and self.variation_cumul < 30 :
            # Le signal d'alerte n'a pas été envoyé, donc on l'envoie
            if self.statut_prealerte == 'Aucune prealerte envoyee':
                self.courriel('prealerte')
            
            else:
                print(self.statut_prealerte)
                
        if self.variation_cumul >= 30:
            # Le signal d'alerte n'a pas été envoyé, donc on l'envoie
            if self.statut_alerte == 'Aucune alerte envoyee': 
                self.courriel('alerte')
            
            else:
                print(self.statut_alerte)
                
        else:
            # Si le risque calculé est faible, le statut d'envoi du signal de préalerte et d'alerte reste 'non envoyé'
            if self.variation_cumul < 25:
                self.statut_prealerte = 'Aucune prealerte envoyee'
                self.ecriture_statut_prealerte = open(self.fichier_statut_prealerte, 'w')
                self.ecriture_statut_prealerte.write(self.statut_prealerte)
                self.ecriture_statut_prealerte.close()
                print(f'Statut de préalerte: {self.statut_prealerte}')
    
                self.statut_alerte = 'Aucune alerte envoyee'
                self.ecriture_statut_alerte = open(self.fichier_statut_alerte, 'w')
                self.ecriture_statut_alerte.write(self.statut_alerte)
                self.ecriture_statut_alerte.close()
                print(f'Statut de d\'alerte: {self.statut_alerte}')
        
        print(f'Niveau de risque de décrochement de couche active : {self.niveau_risque}')

    def courriel(self, type_courriel):
        """
        Envoyer le courriel avec les rapports PDF en PJ si le niveau de risque approche
        du seuil élevé. 
        """
# =============================================================================
# Profondeur de dégel de la veille disponible (self.profondeur_degel) 
# à ajouter dans le courriel au besoin. Decommenter dans __init__
# =============================================================================

        texte_rapports = 'Bonjour,\n\nVous trouverez en PJ les rapports générés par le programme pour le suivi du niveau de risque de glissement de terrain à Salluit et pour le statut de transmission de données des stations SILA, GN et GS.\n\n'
        texte_risque = f'Niveau de risque en date du {self.date_sila} : {self.niveau_risque}.\n\n'
        web_app = f'Consultez le niveau de risque de glissement de terrain et l\'évolution des indices climatiques à l\'adresse {self.url}\n\n'
        prevision_meteo = 'Consultez le prévision météorologique pour prendre connaissance des vagues de chaleur à venir à l\'adresse https://meteo.gc.ca/city/pages/qc-128_metric_f.html\n\n'
        signature = f'Pour toutes questions sur le niveau de risque ou sur l\'application Web, contactez {self.responsable_projet}.\n\nBonne journée.'
        
        receiver = self.destinataire
        
        yag = yagmail.SMTP('arcgisonline.cen@gmail.com')
        yag.send(
        to=receiver,
        subject='Niveau du risque de glissement de terrain à Salluit',
        contents=[texte_rapports, texte_risque, web_app, prevision_meteo, signature], 
        attachments=[self.rapport_niveau_risque, self.rapport_statut_stations]) 
        
        if type_courriel == 'prealerte':
            # On modifie le statut d'envoi du signal pour 'envoyé' pour ne pas l'envoyer à chaque fois. 
            self.statut_prealerte = f'Prealerte envoye - {self.date}'
            self.ecriture_statut_prealerte = open(self.fichier_statut_prealerte, 'w')
            self.ecriture_statut_prealerte.write(self.statut_signal)
            self.ecriture_statut_prealerte.close()
        
        if type_courriel == 'alerte':
            self.statut_alerte = f'Alerte envoye - {self.date}'
            self.ecriture_statut_alerte = open(self.fichier_statut_alerte, 'w')
            self.ecriture_statut_alerte.write(self.statut_alerte)
            self.ecriture_statut_alerte.close()
        
        print(f'Signal {self.courriel} et rapports envoyés à {receiver}.')

    def ecrire_pdf(self, pdf, nom_fichier):
        
        pdf.output(nom_fichier, 'F')

if __name__ == '__main__':
    
    repertoire = input('Repertoire de travail du programme : ')

    destinataire = ['tappezlecourriel1@', 'tappezlecourriel2@']
    
    alerte = AlerteRisqueCourriel(destinataire, repertoire)
# =============================================================================
#     alerte.generer_rapports()
#     alerte.courriel()
# =============================================================================
