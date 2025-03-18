import tkinter as tk
import time
import threading
from utils import safe_float, safe_int

class SimulationController:
    """
    Contrôleur principal de la simulation.
    Gère la communication entre NetLogo, la base de données et l'interface utilisateur.
    """
    def __init__(self, root, simulation_tab, netlogo_connector, db_manager, dashboard_manager):
        """
        Initialise le contrôleur de simulation.
        
        Args:
            root: Fenêtre principale Tkinter
            simulation_tab: Onglet de simulation
            netlogo_connector: Connecteur NetLogo
            db_manager: Gestionnaire de base de données
            dashboard_manager: Gestionnaire de tableau de bord
        """
        self.root = root
        self.simulation_tab = simulation_tab
        self.netlogo_connector = netlogo_connector
        self.db_manager = db_manager
        self.dashboard_manager = dashboard_manager
        
        # Variables de simulation
        self.simulation_running = False
        self.simulation_id = None
        self.products_created = 0
        
        # Initialisation de l'interface
        self.init_ui()
        
        # Démarrer le timer pour mettre à jour le tableau de bord
        self.start_dashboard_timer()
    
    def init_ui(self):
        """
        Initialise l'interface utilisateur du contrôleur.
        """
        # Créer les composants de l'interface
        controls_frame = tk.Frame(self.simulation_tab)
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Bouton pour initialiser NetLogo
        self.init_button = tk.Button(controls_frame, text="Initialiser NetLogo", command=self.initialize_netlogo)
        self.init_button.pack(side=tk.LEFT, padx=5)
        
        # Bouton pour démarrer la simulation
        self.start_button = tk.Button(controls_frame, text="Démarrer", command=self.start_simulation)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # Bouton pour arrêter la simulation
        self.stop_button = tk.Button(controls_frame, text="Arrêter", command=self.stop_simulation)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Cadre pour les informations de simulation
        info_frame = tk.LabelFrame(self.simulation_tab, text="Informations")
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Étiquettes d'information
        self.status_label = tk.Label(info_frame, text="Status: Non initialisé")
        self.status_label.pack(anchor=tk.W, padx=5, pady=5)
        
        self.time_label = tk.Label(info_frame, text="Temps: 0.0")
        self.time_label.pack(anchor=tk.W, padx=5, pady=5)
        
        self.products_label = tk.Label(info_frame, text="Produits: 0")
        self.products_label.pack(anchor=tk.W, padx=5, pady=5)
    
    def initialize_netlogo(self):
        """
        Initialise NetLogo avec le modèle.
        """
        try:
            # Mettre à jour l'interface
            self.status_label.config(text="Status: Initialisation en cours...")
            self.root.update_idletasks()
            
            # Initialiser NetLogo via le connecteur
            success = self.netlogo_connector.initialize()
            
            if success:
                self.status_label.config(text="Status: NetLogo initialisé")
                # Activer le bouton de démarrage
                self.start_button.config(state=tk.NORMAL)
            else:
                self.status_label.config(text="Status: Échec de l'initialisation")
        except Exception as e:
            print(f"Erreur lors de l'initialisation de NetLogo: {e}")
            self.status_label.config(text=f"Status: Erreur: {str(e)}")
    
    def start_simulation(self):
        """
        Démarre la simulation NetLogo.
        """
        if not self.simulation_running:
            try:
                # Démarrer une nouvelle simulation dans la BD
                self.simulation_id = self.db_manager.start_simulation()
                
                # Exécuter la commande setup de NetLogo
                self.netlogo_connector.execute_command("setup")
                
                # Mettre à jour l'interface
                self.status_label.config(text="Status: Simulation en cours...")
                self.start_button.config(state=tk.DISABLED)
                self.stop_button.config(state=tk.NORMAL)
                
                # Démarrer la simulation
                self.simulation_running = True
                
                # Lancer la simulation dans un thread séparé
                threading.Thread(target=self.run_simulation, daemon=True).start()
            except Exception as e:
                print(f"Erreur lors du démarrage de la simulation: {e}")
                self.status_label.config(text=f"Status: Erreur: {str(e)}")
    
    def run_simulation(self):
        """
        Exécute la simulation NetLogo de manière continue.
        """
        try:
            while self.simulation_running:
                # Exécuter une étape de la simulation
                self.netlogo_connector.execute_command("go")
                
                # Récupérer les informations actuelles
                current_time = self.netlogo_connector.get_reporter_value("ticks", 0.0)
                
                # Mettre à jour l'interface
                self.root.after(0, lambda t=current_time: self.update_ui(t))
                
                # Courte pause pour ne pas surcharger NetLogo
                time.sleep(0.05)
        except Exception as e:
            print(f"Erreur dans la boucle de simulation: {e}")
            self.root.after(0, lambda: self.status_label.config(text=f"Status: Erreur: {str(e)}"))
            self.simulation_running = False
    
    def update_ui(self, current_time):
        """
        Met à jour l'interface utilisateur avec les informations actuelles.
        
        Args:
            current_time: Temps actuel de la simulation
        """
        # Mettre à jour les étiquettes
        self.time_label.config(text=f"Temps: {current_time:.1f}")
        
        # Compter les produits
        count_products = self.netlogo_connector.get_reporter_value("count products", 0)
        self.products_label.config(text=f"Produits: {count_products}")
    
    def stop_simulation(self):
        """
        Arrête la simulation en cours.
        """
        if self.simulation_running:
            # Arrêter la boucle de simulation
            self.simulation_running = False
            
            # Mettre à jour l'interface
            self.status_label.config(text="Status: Simulation arrêtée")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            
            # Finaliser la simulation dans la base de données
            current_time = self.netlogo_connector.get_reporter_value("ticks", 0.0)
            self.db_manager.end_simulation(self.simulation_id, current_time)
    
    def start_dashboard_timer(self):
        """
        Démarre un timer pour mettre à jour périodiquement le tableau de bord.
        """
        # Mettre à jour le tableau de bord toutes les 2 secondes
        def update_timer():
            if self.simulation_running:
                self.update_dashboard()
            self.root.after(2000, update_timer)
        
        # Démarrer le timer
        self.root.after(2000, update_timer)
    
    def update_dashboard(self):
        """
        Met à jour le tableau de bord avec les données de la simulation
        """
        # Récupérer les données des produits
        products_data = self.netlogo_connector.get_products_data()
        
        # Mettre à jour les statistiques avec les données récupérées
        self.dashboard_manager.update_product_stats(products_data)
        
        # Récupérer les données des machines
        machines_data = self.netlogo_connector.get_machines_data()
        self.dashboard_manager.update_machine_stats(machines_data)
        
        # Vérification de cohérence
        actual_product_count = len(products_data)
        dashboard_product_count = self.dashboard_manager.total_products
        
        if actual_product_count != dashboard_product_count:
            print(f"ATTENTION: Incohérence dans le nombre de produits! Actuel: {actual_product_count}, Affiché: {dashboard_product_count}")
            # Synchroniser les nombres si nécessaire
            self.dashboard_manager.total_products = actual_product_count
        
        print(f"Données actuelles (rafraîchissement): {len(machines_data)} machines, {actual_product_count} produits")
        
        # MISE À JOUR DU GRAPHIQUE D'EFFICACITÉ DE PRODUCTION
        # Obtenir les données d'efficacité depuis le gestionnaire de base de données
        efficiency_data = self.db_manager.get_production_efficiency(actual_product_count)
        
        # Afficher un message clair si des produits sont complétés mais sans temps de cycle
        if "completed" in efficiency_data and "completed_with_cycle" in efficiency_data:
            completed = efficiency_data["completed"]
            with_cycle = efficiency_data["completed_with_cycle"]
            if completed > with_cycle:
                print(f"ℹ️ Attention: {completed-with_cycle} produits complétés n'ont pas de temps de cycle valide")
        
        # Mettre à jour le graphique en camembert du taux d'efficacité
        self.dashboard_manager.update_efficiency_pie_chart(efficiency_data)
        
        # MISE À JOUR DU GRAPHIQUE DE TEMPS DE CYCLE
        try:
            # Récupérer directement les temps de cycle depuis la base de données
            cycle_times_df = self.db_manager.get_cycle_times()
            
            # Si nous avons des données de temps de cycle, les utiliser
            if not cycle_times_df.empty:
                self.dashboard_manager.update_cycle_time_chart(cycle_times_df)
                print(f"Données de temps de cycle récupérées: {type(cycle_times_df)}")
                print(cycle_times_df)
            else:
                print("Aucune donnée de temps de cycle trouvée dans la base - tentative alternative")
                
                # NOUVELLE APPROCHE PLUS ROBUSTE: Rechercher directement dans la table des produits complétés
                raw_data = self.db_manager.fetch_all("""
                    SELECT type, temps_cycle FROM completed_products 
                    WHERE temps_cycle > 0
                """)
                
                if raw_data:
                    # Construire manuellement un DataFrame
                    types = {}
                    for row in raw_data:
                        product_type = row[0] 
                        cycle_time = float(row[1])
                        
                        if product_type not in types:
                            types[product_type] = []
                        types[product_type].append(cycle_time)
                    
                    # Calculer les moyennes
                    result_list = []
                    for product_type, cycle_times in types.items():
                        avg_cycle_time = sum(cycle_times) / len(cycle_times)
                        result_list.append({'type': product_type, 'temps_cycle': avg_cycle_time})
                    
                    if result_list:
                        # Créer DataFrame
                        import pandas as pd
                        manual_df = pd.DataFrame(result_list)
                        print(f"Données calculées manuellement: {manual_df}")
                        self.dashboard_manager.update_cycle_time_chart(manual_df)
                        return
                
                # Si toujours pas de données, essayer la méthode des produits actifs
                total_cycle_time = 0
                completed_products = 0
                
                for product in products_data:
                    if isinstance(product, dict):
                        # Vérifier si le produit est complété
                        if product.get('state', '').lower() == 'completed':
                            if 'start.time' in product and 'end.time' in product:
                                start_time = float(product.get('start.time', 0))
                                end_time = float(product.get('end.time', 0))
                                
                                if end_time > start_time:
                                    cycle_time = end_time - start_time
                                    total_cycle_time += cycle_time
                                    completed_products += 1
                                    print(f"Produit {product.get('who', 'inconnu')}: début={start_time}, fin={end_time}, cycle={cycle_time}")
                            # Alternative: utiliser productrealstart si disponible
                            elif 'productrealstart' in product:
                                start_times = product.get('productrealstart', [])
                                if len(start_times) >= 2:
                                    start_time = float(start_times[0])
                                    end_time = float(start_times[-1])
                                    
                                    if end_time > start_time:
                                        cycle_time = end_time - start_time
                                        total_cycle_time += cycle_time
                                        completed_products += 1
                                        print(f"Produit {product.get('who', 'inconnu')}: début={start_time}, fin={end_time}, cycle={cycle_time}")
                
                # Calculer et afficher le temps de cycle moyen
                if completed_products > 0:
                    average_cycle_time = total_cycle_time / completed_products
                    print(f"Temps de cycle moyen calculé pour {completed_products} produits: {average_cycle_time}")
                    self.dashboard_manager.update_cycle_time_chart(average_cycle_time)
                else:
                    print("Aucun produit avec cycle complet détecté.")
                    self.dashboard_manager.update_cycle_time_chart(0)
                
        except Exception as e:
            print(f"ERREUR lors du calcul du temps de cycle des produits: {e}")
            import traceback
            traceback.print_exc()
            # En cas d'erreur, utiliser une valeur par défaut
            self.dashboard_manager.update_cycle_time_chart(0)