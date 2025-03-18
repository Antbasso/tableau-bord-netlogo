import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk  # Ajout de l'import tkinter

class DashboardManager:
    def __init__(self, root_frame):
        """
        Initialisation du gestionnaire de tableau de bord
        
        Args:
            root_frame: Frame Tkinter principal où les widgets seront placés
        """
        self.root = root_frame
        self.product_counts = {}
        self.total_products = 0
        self.products_detail = []
        
        # Création des frames pour chaque graphique
        self.product_frame = tk.Frame(self.root)
        self.product_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        self.efficiency_frame = tk.Frame(self.root)
        self.efficiency_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        self.cycle_frame = tk.Frame(self.root)
        self.cycle_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        
        # Initialisation des figures et canvas
        self.init_product_chart()
        self.init_efficiency_chart()
        self.init_cycle_chart()
        
        # Configuration du redimensionnement
        root_frame.grid_rowconfigure(0, weight=1)
        root_frame.grid_rowconfigure(1, weight=1)
        root_frame.grid_columnconfigure(0, weight=1)
        root_frame.grid_columnconfigure(1, weight=1)
    
    def init_product_chart(self):
        """Initialise le graphique de répartition des produits"""
        self.product_fig = Figure(figsize=(6, 4), dpi=100)
        self.product_ax = self.product_fig.add_subplot(111)
        self.product_canvas = FigureCanvasTkAgg(self.product_fig, master=self.product_frame)
        self.product_widget = self.product_canvas.get_tk_widget()
        self.product_widget.pack(fill=tk.BOTH, expand=True)
    
    def init_efficiency_chart(self):
        """Initialise le graphique d'efficacité de production"""
        self.efficiency_fig = Figure(figsize=(6, 4), dpi=100)
        self.efficiency_ax = self.efficiency_fig.add_subplot(111)
        self.efficiency_canvas = FigureCanvasTkAgg(self.efficiency_fig, master=self.efficiency_frame)
        self.efficiency_widget = self.efficiency_canvas.get_tk_widget()
        self.efficiency_widget.pack(fill=tk.BOTH, expand=True)
    
    def init_cycle_chart(self):
        """Initialise le graphique des temps de cycle"""
        self.cycle_fig = Figure(figsize=(8, 4), dpi=100)
        self.cycle_ax = self.cycle_fig.add_subplot(111)
        self.cycle_canvas = FigureCanvasTkAgg(self.cycle_fig, master=self.cycle_frame)
        self.cycle_widget = self.cycle_canvas.get_tk_widget()
        self.cycle_widget.pack(fill=tk.BOTH, expand=True)
    
    def update_product_stats(self, products_data):
        """
        Met à jour les statistiques des produits en utilisant uniquement 
        les données des produits actuellement détectés
        """
        # Réinitialiser le comptage avant de traiter les données actuelles
        self.product_counts = {}
        self.total_products = 0
        
        # Ne compter que les produits réellement détectés
        for product in products_data:
            if isinstance(product, dict):
                product_type = product.get('type', 'Unknown')
                if product_type not in self.product_counts:
                    self.product_counts[product_type] = 0
                self.product_counts[product_type] += 1
                self.total_products += 1
        
        # Mettre à jour les données pour l'affichage
        self.products_detail = [(ptype, count) for ptype, count in self.product_counts.items()]
        
        # Log de vérification
        print(f"Détails des produits: {self.products_detail}")
        
        # Mise à jour du graphique en camembert des types de produits
        self.update_product_pie_chart()
    
    def update_machine_stats(self, machines_data):
        """
        Met à jour les statistiques des machines
        
        Args:
            machines_data: Liste des données de machines
        """
        # Implémentation simplifiée - à développer selon vos besoins
        pass
    
    def update_product_pie_chart(self):
        """Met à jour le graphique en camembert des types de produits"""
        # Nettoyer la figure existante
        self.product_ax.clear()
        
        if not self.products_detail:
            self.product_ax.text(0.5, 0.5, "Aucun produit détecté",
                               ha='center', va='center', fontsize=14)
            self.product_ax.axis('off')
        else:
            # Extraire les données pour le camembert
            labels = [p[0] for p in self.products_detail]
            sizes = [p[1] for p in self.products_detail]
            
            # Générer des couleurs pour chaque type de produit
            colors = plt.cm.tab10.colors[:len(labels)]
            explode = [0.1] + [0] * (len(labels) - 1)  # Faire ressortir le premier segment
            
            # Création du camembert
            wedges, texts, autotexts = self.product_ax.pie(
                sizes, 
                explode=explode if len(explode) == len(sizes) else None,
                labels=labels, 
                colors=colors,
                autopct='%1.1f%%',
                startangle=90,
                shadow=True
            )
            
            # Propriétés du texte
            for text in texts:
                text.set_fontsize(10)
            for autotext in autotexts:
                autotext.set_fontsize(10)
                autotext.set_weight('bold')
            
            # Titre du graphique
            self.product_ax.set_title('Répartition des Types de Produits', fontsize=14)
            
            # Égaliser les axes pour éviter un camembert ovale
            self.product_ax.axis('equal')
        
        # Rafraîchir le canvas
        self.product_fig.tight_layout()
        self.product_canvas.draw()
    
    def update_efficiency_pie_chart(self, efficiency_data):
        """
        Met à jour le graphique en camembert d'efficacité de production
        
        Args:
            efficiency_data: dictionnaire contenant les données d'efficacité ou pourcentage
        """
        # Nettoyer la figure existante
        self.efficiency_ax.clear()
        
        # Récupérer les données nécessaires
        if isinstance(efficiency_data, dict):
            completed = efficiency_data.get("completed", 0)
            # Utiliser le total de produits complétés, pas seulement ceux avec cycle valide
            total = efficiency_data.get("total", 20)  # Nombre théorique maximum
            efficiency = efficiency_data.get("efficiency", 0)
            remaining = max(0, 100 - efficiency)  # Assurer que la valeur n'est pas négative
            
            # Détailler les produits qui n'ont pas de cycle calculable
            completed_with_cycle = efficiency_data.get("completed_with_cycle", completed)
            completed_without_cycle = completed - completed_with_cycle
            
            # Log détaillé pour débogage
            if completed_without_cycle > 0:
                print(f"⚠️ {completed_without_cycle} produit(s) complété(s) sans temps de cycle valide")
        else:
            # Si on reçoit directement un pourcentage
            efficiency = min(100, float(efficiency_data) * 100 if efficiency_data <= 1 else float(efficiency_data))
            completed = int((efficiency / 100) * 20)  # 20 est le maximum théorique
            total = 20
            remaining = max(0, 100 - efficiency)  # Assurer que la valeur n'est pas négative
            completed_with_cycle = completed  # Par défaut tous ont un cycle valide
            completed_without_cycle = 0
        
        # Données pour le camembert
        sizes = [efficiency, remaining]
        # Inclure l'information sur les produits sans cycle valide dans le label si nécessaire
        if completed_without_cycle > 0:
            labels = [f'Complétés ({completed}/{total}) dont {completed_without_cycle} sans cycle', f'Restants ({total-completed}/{total})']
        else:
            labels = [f'Complétés ({completed}/{total})', f'Restants ({total-completed}/{total})']
        colors = ['#4CAF50', '#F5F5F5']  # Vert pour complétés, gris clair pour restants
        explode = (0.1, 0)  # Pour faire ressortir la partie complétée
        
        # Vérifier que les données sont correctes pour le camembert
        print(f"Données d'efficacité pour le camembert: sizes={sizes}, labels={labels}")
        
        # Création du camembert
        wedges, texts, autotexts = self.efficiency_ax.pie(
            sizes, 
            explode=explode,
            labels=labels, 
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            shadow=True,
            wedgeprops={'linewidth': 1, 'edgecolor': 'white'}
        )
        
        # Propriétés du texte
        for text in texts:
            text.set_fontsize(12)
        for autotext in autotexts:
            autotext.set_fontsize(12)
            autotext.set_weight('bold')
            autotext.set_color('black')
        
        # Titre du graphique
        self.efficiency_ax.set_title('Efficacité de Production', fontsize=16, pad=20)
        
        # Égaliser les axes pour éviter un camembert ovale
        self.efficiency_ax.axis('equal')
        
        # Rafraîchir le canvas avec tight_layout pour bien positionner le graphique
        self.efficiency_fig.tight_layout()
        self.efficiency_canvas.draw()
        
        # Forcer la mise à jour de l'interface
        self.root.update_idletasks()
    
    def update_cycle_time_chart(self, cycle_time_data):
        """
        Met à jour le graphique des temps de cycle moyens par type de produit
        
        Args:
            cycle_time_data: DataFrame pandas ou valeur moyenne globale
        """
        # Nettoyer la figure existante
        self.cycle_ax.clear()
        
        # Debug - voir ce que contient exactement cycle_time_data
        print(f"DEBUG update_cycle_time_chart: type={type(cycle_time_data)}, data={cycle_time_data}")
        
        # Vérifier si nous avons des données par type ou juste une moyenne globale
        if hasattr(cycle_time_data, 'empty'):
            # C'est un DataFrame pandas
            if not cycle_time_data.empty:
                try:
                    # Extraire les types et les temps de cycle
                    types = cycle_time_data['type'].tolist()
                    times = cycle_time_data['temps_cycle'].tolist()
                    
                    print(f"Types extraits: {types}")
                    print(f"Temps extraits: {times}")
                    
                    # Créer le graphique à barres
                    bars = self.cycle_ax.bar(types, times, color='skyblue', edgecolor='black')
                    
                    # Ajouter les valeurs sur les barres
                    for bar in bars:
                        height = bar.get_height()
                        self.cycle_ax.text(bar.get_x() + bar.get_width()/2., height,
                                          f'{height:.1f}',
                                          ha='center', va='bottom', fontsize=12)
                    
                    # Propriétés du graphique
                    self.cycle_ax.set_xlabel('Type de produit', fontsize=14)
                    self.cycle_ax.set_ylabel('Temps de cycle moyen (ticks)', fontsize=14)
                    self.cycle_ax.set_title('Temps de cycle moyen par type de produit', fontsize=16)
                    self.cycle_ax.grid(True, linestyle='--', alpha=0.7)
                    
                    # Si on a beaucoup de types de produits, faire une rotation des étiquettes
                    if len(types) > 5:
                        plt.setp(self.cycle_ax.get_xticklabels(), rotation=45, ha='right')
                except Exception as e:
                    print(f"Erreur lors du traitement des données de temps de cycle: {e}")
                    self.cycle_ax.text(0.5, 0.5, f'Erreur: {str(e)}',
                                    ha='center', va='center', fontsize=12)
                    self.cycle_ax.set_xticks([])
                    self.cycle_ax.set_yticks([])
            else:
                # Pas de données dans le DataFrame
                # Essayer de récupérer des données directement des produits actifs
                print("Tentative de récupération de données alternatives pour temps de cycle...")
                
                # Afficher un message explicatif
                self.cycle_ax.text(0.5, 0.5, 'Calcul automatique des temps de cycle...\nAttendez que quelques produits soient complétés.',
                                  ha='center', va='center', fontsize=12)
                self.cycle_ax.set_xticks([])
                self.cycle_ax.set_yticks([])
        else:
            # C'est une valeur unique (moyenne globale)
            try:
                cycle_time = float(cycle_time_data) if cycle_time_data else 0
                
                if cycle_time > 0:
                    # Créer un graphique à barre simple
                    bars = self.cycle_ax.bar(['Moyenne'], [cycle_time], color='skyblue', edgecolor='black')
                    for bar in bars:
                        height = bar.get_height()
                        self.cycle_ax.text(bar.get_x() + bar.get_width()/2., height,
                                      f'{height:.1f}', ha='center', va='bottom', fontsize=12)
                    
                    # Propriétés du graphique
                    self.cycle_ax.set_ylabel('Temps de cycle moyen (ticks)', fontsize=14)
                    self.cycle_ax.set_title('Temps de cycle moyen global', fontsize=16)
                    self.cycle_ax.grid(True, linestyle='--', alpha=0.7, axis='y')
                else:
                    # Message spécial pour une valeur nulle
                    self.cycle_ax.text(0.5, 0.5, 'En attente de produits terminés pour calculer le temps de cycle',
                                      ha='center', va='center', fontsize=12)
                    self.cycle_ax.set_xticks([])
                    self.cycle_ax.set_yticks([])
            except (ValueError, TypeError) as e:
                print(f"Erreur de conversion pour temps de cycle: {e}")
                self.cycle_ax.text(0.5, 0.5, 'Temps de cycle non disponible',
                                  ha='center', va='center', fontsize=14)
                self.cycle_ax.set_xticks([])
                self.cycle_ax.set_yticks([])
        
        # Rafraîchir le canvas avec tight_layout pour bien positionner le graphique
        self.cycle_fig.tight_layout()
        self.cycle_canvas.draw()
        
        # Forcer la mise à jour de l'interface
        try:
            self.root.update_idletasks()
        except:
            pass
