import sqlite3
import datetime
import os
import pandas as pd

from utils import safe_float, safe_int

class DatabaseManager:
    def __init__(self, db_path= "projet netlogo/simulation_data.db"):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), db_path)
        self._create_tables()
    
    def _connect(self):
        return sqlite3.connect(self.db_path)
    
    def clear_database(self):
        """Vide toutes les tables de la base de données"""
        with self._connect() as conn:
            cursor = conn.cursor()
            # Désactiver les contraintes de clé étrangère temporairement
            cursor.execute("PRAGMA foreign_keys = OFF")
            
            # Vider toutes les tables
            cursor.execute("DELETE FROM production")
            cursor.execute("DELETE FROM snapshot")
            cursor.execute("DELETE FROM produit")
            cursor.execute("DELETE FROM machine")
            cursor.execute("DELETE FROM simulation")
            
            # Réinitialiser les compteurs d'auto-incrémentation
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='production'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='snapshot'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='produit'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='machine'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='simulation'")
            
            # Réactiver les contraintes de clé étrangère
            cursor.execute("PRAGMA foreign_keys = ON")
            
            conn.commit()
    
    def _create_tables(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # Table machine
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS machine (
                    id_machine INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    etat TEXT CHECK (etat IN('Idle', 'Processing','Down')),
                    temps_restant REAL,
                    operations TEXT,
                    temps_operations TEXT,
                    x INTEGER,
                    y INTEGER,
                    orientation INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table produit
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS produit (
                    id_produit INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    etat TEXT CHECK (etat IN ('Waiting','Movement','Processing.Product','Completed')),
                    sequence_order INTEGER,
                    operations TEXT,
                    operation_suivante TEXT,
                    heure_debut REAL,
                    heure_fin REAL,
                    dernier_noeud INTEGER,
                    prochain_noeud INTEGER,
                    poste_travail TEXT,
                    statut_suivant INTEGER,
                    temps_restant REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table production (pour enregistrer les opérations de production)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS production (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    machine_id INTEGER,
                    produit_id INTEGER,
                    operation TEXT,
                    heure_debut REAL,
                    heure_fin REAL,
                    duree_ticks REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(machine_id) REFERENCES machine(id_machine),
                    FOREIGN KEY(produit_id) REFERENCES produit(id_produit)
                )
            ''')
            
            # Table simulation (pour enregistrer les sessions de simulation)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS simulation (
                    id_simulation INTEGER PRIMARY KEY AUTOINCREMENT,
                    date_debut DATETIME,
                    date_fin DATETIME,
                    duree_totale REAL,
                    nombre_produits INTEGER,
                    nombre_machines INTEGER,
                    ticks_final REAL
                )
            ''')
            
            # Table snapshot (pour enregistrer des instantanés de l'état du système)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS snapshot (
                    id_snapshot INTEGER PRIMARY KEY AUTOINCREMENT,
                    simulation_id INTEGER,
                    tick REAL,
                    nombre_produits_waiting INTEGER,
                    nombre_produits_in_progress INTEGER,
                    nombre_produits_completed INTEGER,
                    nombre_machines_idle INTEGER,
                    nombre_machines_processing INTEGER,
                    nombre_machines_down INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(simulation_id) REFERENCES simulation(id_simulation)
                )
            ''')
            
            # Nouvelle table pour suivre les produits complétés
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS completed_products (
                    id_produit INTEGER PRIMARY KEY,
                    type TEXT NOT NULL,
                    heure_debut REAL,
                    heure_fin REAL,
                    temps_cycle REAL,
                    simulation_id INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(simulation_id) REFERENCES simulation(id_simulation)
                )
            ''')
            
            conn.commit()
    
    def execute(self, query, params=()):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
    
    def fetch_one(self, query, params=()):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
    
    def fetch_all(self, query, params=()):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def fetch_df(self, query, params=()):
        """Exécute une requête et retourne un DataFrame pandas"""
        with self._connect() as conn:
            return pd.read_sql_query(query, conn, params=params)
    
    def start_simulation(self):
        """Enregistre le début d'une nouvelle simulation"""
        query = """
            INSERT INTO simulation (date_debut, nombre_produits, nombre_machines)
            VALUES (?, 0, 0)
        """
        return self.execute(query, (datetime.datetime.now(),))
    
    def end_simulation(self, simulation_id, ticks_final):
        """Enregistre la fin d'une simulation"""
        query = """
            UPDATE simulation
            SET date_fin = ?, duree_totale = ?, ticks_final = ?
            WHERE id_simulation = ?
        """
        # Calculer la durée en secondes
        start_date = self.fetch_one("SELECT date_debut FROM simulation WHERE id_simulation = ?", (simulation_id,))[0]
        start_date = datetime.datetime.fromisoformat(start_date)
        end_date = datetime.datetime.now()
        duration = (end_date - start_date).total_seconds()
        
        self.execute(query, (end_date, duration, ticks_final, simulation_id))
        
        # Mettre à jour le nombre de produits et de machines
        produits = self.fetch_one("SELECT COUNT(*) FROM produit")[0]
        machines = self.fetch_one("SELECT COUNT(*) FROM machine")[0]
        
        self.execute("""
            UPDATE simulation
            SET nombre_produits = ?, nombre_machines = ?
            WHERE id_simulation = ?
        """, (produits, machines, simulation_id))
    
    def save_machine(self, machine_data):
        """Enregistre ou met à jour les données d'une machine avec gestion stricte des types"""
        # Récupérer et nettoyer les données
        machine_name = machine_data.get("name", "Unknown")
        
        # Validation de l'état - s'assurer qu'il est compatible avec la contrainte CHECK
        state = machine_data.get("state", "Idle")
        if state not in ["Idle", "Processing", "Down"]:
            state = "Idle"
        
        # Récupérer et convertir les valeurs numériques avec une gestion stricte des erreurs
        try:
            remaining_time_str = machine_data.get("remaining.time", "0")
            # Nettoyer la chaîne pour s'assurer qu'elle peut être convertie
            remaining_time_str = str(remaining_time_str).strip()
            if remaining_time_str == "" or remaining_time_str.lower() == "none":
                remaining_time = 0.0
            else:
                # Gérer les valeurs comme "10000000.0"
                if remaining_time_str == "10000000" or remaining_time_str == "10000000.0":
                    remaining_time = 0.0
                else:
                    remaining_time = float(remaining_time_str)
        except (ValueError, TypeError, AttributeError):
            remaining_time = 0.0
        
        # Nettoyer et valider les chaînes d'opérations
        operations_str = str(machine_data.get("operations", "[]")).strip()
        operation_times_str = str(machine_data.get("operation.times", "[]")).strip()
        
        # Récupérer et convertir les coordonnées
        try:
            x_str = machine_data.get("xcor", "0").strip()
            if x_str == "" or x_str.lower() == "none":
                x = 0
            else:
                x = int(float(x_str))
        except (ValueError, TypeError, AttributeError):
            x = 0
        
        try:
            y_str = machine_data.get("ycor", "0").strip()
            if y_str == "" or y_str.lower() == "none":
                y = 0
            else:
                y = int(float(y_str))
        except (ValueError, TypeError, AttributeError):
            y = 0
        
        try:
            heading_str = machine_data.get("heading", "0").strip()
            if heading_str == "" or heading_str.lower() == "none":
                heading = 0.0
            else:
                heading = float(heading_str)
        except (ValueError, TypeError, AttributeError):
            heading = 0.0
        
        # Vérifier si la machine existe déjà
        existing = self.fetch_one("SELECT id_machine FROM machine WHERE nom = ?", (machine_name,))
        
        if existing:
            # Mettre à jour la machine existante
            query = """
                UPDATE machine
                SET etat = ?, temps_restant = ?, operations = ?, temps_operations = ?, x = ?, y = ?, orientation = ?
                WHERE id_machine = ?
            """
            self.execute(query, (
                state, 
                remaining_time,
                operations_str,
                operation_times_str,
                x,
                y,
                heading,
                existing[0]
            ))
            return existing[0]
        else:
            # Créer une nouvelle machine
            query = """
                INSERT INTO machine (nom, etat, temps_restant, operations, temps_operations, x, y, orientation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            return self.execute(query, (
                machine_name,
                state,
                remaining_time,
                operations_str,
                operation_times_str,
                x,
                y,
                heading
            ))
    
    def save_product(self, product_data):
        """Enregistre les données d'un produit avec gestion stricte des types"""
        # Récupérer l'identifiant du produit avec conversion explicite
        who = safe_int(product_data.get("who", -1), -1)
        
        if who < 0:
            print("Avertissement: Tentative de sauvegarde d'un produit avec ID invalide")
            return None
        
        # Convertir explicitement tous les types pour SQLite
        product_type = str(product_data.get("type", ""))
        state = str(product_data.get("state", "Waiting"))
        sequence_order = safe_int(product_data.get("sequence.order", 0), 0)
        operations = str(product_data.get("operations", "[]"))
        next_op = str(product_data.get("next.operation", ""))
        start_time = safe_float(product_data.get("start.time", 0), 0.0)
        end_time = safe_float(product_data.get("end.time", 0), 0.0)
        last_node = safe_int(product_data.get("last.node", 0), 0)
        next_node = safe_int(product_data.get("next.node", 0), 0)
        workstation = str(product_data.get("workstation", ""))
        next_status = safe_int(product_data.get("next.status", 0), 0)
        remaining_time = safe_float(product_data.get("remaining.time", 0), 0.0)
        
        try:
            # Vérifier si le produit existe déjà
            existing = self.fetch_one("SELECT id_produit FROM produit WHERE id_produit = ?", (who,))
            
            if existing:
                # Mettre à jour le produit existant
                query = """
                    UPDATE produit
                    SET type = ?, etat = ?, sequence_order = ?, operations = ?, operation_suivante = ?,
                        heure_debut = ?, heure_fin = ?, dernier_noeud = ?, prochain_noeud = ?,
                        poste_travail = ?, statut_suivant = ?, temps_restant = ?
                    WHERE id_produit = ?
                """
                self.execute(query, (
                    product_type, state, sequence_order, operations, next_op,
                    start_time, end_time, last_node, next_node,
                    workstation, next_status, remaining_time,
                    existing[0]
                ))
                return existing[0]
            else:
                # Créer un nouveau produit
                query = """
                    INSERT INTO produit (id_produit, type, etat, sequence_order, operations, operation_suivante,
                                        heure_debut, heure_fin, dernier_noeud, prochain_noeud,
                                        poste_travail, statut_suivant, temps_restant)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                return self.execute(query, (
                    who, product_type, state, sequence_order, operations, next_op,
                    start_time, end_time, last_node, next_node,
                    workstation, next_status, remaining_time
                ))
        except Exception as e:
            print(f"Erreur SQLite lors de l'enregistrement du produit {who}: {e}")
            import traceback
            traceback.print_exc()  # Afficher la trace complète de l'erreur
            return None
    
    def save_production(self, machine_id, product_id, operation, start_time, end_time):
        """Enregistre une opération de production"""
        
        # Traiter les données entrantes
        try:
            machine_id = int(machine_id)
        except (ValueError, TypeError):
            return None
            
        try:
            product_id = int(product_id)
        except (ValueError, TypeError):
            product_id = -1  # -1 pour les opérations sans produit identifié
            
        operation_str = str(operation)
        
        try:
            start_time = float(start_time)
        except (ValueError, TypeError):
            start_time = 0.0
            
        try:
            end_time = float(end_time)
        except (ValueError, TypeError):
            end_time = start_time + 0.1  # Assurer une durée minimale pour éviter des valeurs nulles
        
        # Calculer la durée (avec une valeur minimale)
        duration = max(0.1, end_time - start_time)
        
        # Vérifier si une opération similaire récente existe déjà pour cette machine
        # pour éviter les duplications excessives
        existing = self.fetch_one("""
            SELECT id FROM production 
            WHERE machine_id = ? AND operation = ? 
            AND heure_debut >= ? AND heure_debut <= ?
        """, (machine_id, operation_str, start_time - 1, start_time))
        
        if existing:
            # Mettre à jour l'opération existante
            query = """
                UPDATE production 
                SET heure_fin = ?, duree_ticks = ?
                WHERE id = ?
            """
            return self.execute(query, (end_time, duration, existing[0]))
        else:
            # Créer une nouvelle opération
            query = """
                INSERT INTO production (machine_id, produit_id, operation, heure_debut, heure_fin, duree_ticks)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            return self.execute(query, (machine_id, product_id, operation_str, start_time, end_time, duration))
    
    def save_snapshot(self, simulation_id, tick, system_state):
        """Enregistre un instantané de l'état du système"""
        query = """
            INSERT INTO snapshot (
                simulation_id, tick, 
                nombre_produits_waiting, nombre_produits_in_progress, nombre_produits_completed,
                nombre_machines_idle, nombre_machines_processing, nombre_machines_down
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        return self.execute(query, (
            simulation_id,
            tick,
            system_state.get("waiting_products", 0),
            system_state.get("in_progress_products", 0),
            system_state.get("completed_products", 0),
            system_state.get("idle_machines", 0),
            system_state.get("processing_machines", 0),
            system_state.get("down_machines", 0)
        ))
    
    def get_machine_utilization(self, sim_time_override=None):
        """Calcule le taux d'utilisation des machines en utilisant le temps réel de simulation"""
        # Vérifier d'abord si un temps de simulation a été fourni en paramètre
        if sim_time_override is not None and sim_time_override > 0:
            sim_time = float(sim_time_override)
        else:
            # Sinon, essayer de récupérer le temps depuis la table snapshot
            sim_time_result = self.fetch_one("SELECT MAX(tick) FROM snapshot")
            
            # Valeur par défaut plus réaliste si aucune donnée n'est trouvée
            sim_time = 1.0
            
            if sim_time_result and sim_time_result[0]:
                sim_time_value = float(sim_time_result[0])
                # Si la simulation a réellement progressé
                if sim_time_value > 0:
                    sim_time = sim_time_value
        
        print(f"Temps de simulation utilisé pour les calculs: {sim_time}")
        
        # Récupérer les données brutes d'utilisation des machines
        query = """
            SELECT 
                m.nom, 
                COALESCE(SUM(p.duree_ticks), 0) as temps_total,
                ? as temps_simulation
            FROM 
                machine m
                LEFT JOIN production p ON m.id_machine = p.machine_id
            GROUP BY 
                m.nom
            ORDER BY 
                m.nom
        """
        
        data = self.fetch_all(query, (sim_time,))
        
        # Calculer le taux d'utilisation précisément
        result = []
        for row in data:
            # Extraire les données avec gestion des cas où row a moins d'éléments que prévu
            machine_name = row[0] if len(row) > 0 else "Unknown"
            total_time = float(row[1] if len(row) > 1 and row[1] is not None else 0)
            simulation_time = float(row[2] if len(row) > 2 and row[2] is not None else sim_time)
            
            # S'assurer que le temps de simulation est au moins 1.0 pour éviter les divisions par zéro
            if simulation_time < 1.0:
                simulation_time = 1.0
            
            # Calculer l'utilisation (temps d'exécution / temps de simulation total)
            utilization = (total_time / simulation_time) * 100.0
            
            # Limiter l'utilisation à 100% maximum 
            if utilization > 100:
                utilization = 100.0
            
            # Pour les machines qui ont une activité mais très faible, assurer une visibilité minimale
            # dans le graphique (au moins 1% si la machine a été utilisée)
            if total_time > 0 and utilization < 1.0:
                utilization = 1.0
            
            # Retourner les données complètes pour un traitement ultérieur
            result.append((machine_name, utilization, total_time, simulation_time))
        
        return result
    
    def get_product_status_distribution(self):
        """Récupère la distribution des produits par statut"""
        query = """
            SELECT etat, COUNT(*) as nombre
            FROM produit
            GROUP BY etat
        """
        
        return self.fetch_df(query)
    
    def get_product_type_distribution(self):
        """
        Récupère la distribution des produits par type
        avec un comptage cohérent des produits
        """
        # Récupérer le nombre total prévu de produits
        # On utilise les deux sources pour plus de fiabilité
        active_products = self.fetch_one("SELECT COUNT(*) FROM produit")[0]
        completed_products = self.fetch_one("SELECT COUNT(*) FROM completed_products")[0]
        
        # Utiliser le nombre total de produits créés depuis les tables existantes
        # en évitant les doublons potentiels
        total_products = max(active_products, completed_products)
        
        # Logique adaptée : 
        # - Si la plupart des produits sont actifs, utiliser la table produit
        # - Si la plupart sont complétés et stockés dans completed_products, utiliser cette table
        if active_products >= completed_products:
            query = "SELECT type, COUNT(*) as nombre FROM produit GROUP BY type"
            print(f"Camembert: utilisation des {active_products} produits actifs")
        else:
            query = "SELECT type, COUNT(*) as nombre FROM completed_products GROUP BY type"
            print(f"Camembert: utilisation des {completed_products} produits complétés")
        
        return self.fetch_all(query)
    
    def get_cycle_times(self):
        """
        Récupère les temps de cycle par type de produit uniquement pour les produits réellement complétés
        
        Returns:
            DataFrame: Temps de cycle moyens par type de produit
        """
        # S'assurer que la table completed_products contient des données avant de faire la requête
        check_query = "SELECT COUNT(*) FROM completed_products"
        count = self.fetch_one(check_query)[0]
        
        if count == 0:
            print("Aucun produit complété trouvé dans la base de données")
            # Retourner un DataFrame vide mais correctement formaté
            return pd.DataFrame(columns=['type', 'temps_cycle'])
        
        # Récupérer uniquement les données des produits dont le cycle est calculé correctement
        # et assurer que le type est correctement interprété
        query = """
            SELECT type, AVG(temps_cycle) as temps_cycle
            FROM completed_products 
            WHERE temps_cycle > 0
            GROUP BY type
        """
        
        try:
            result_df = self.fetch_df(query)
            
            # Si le DataFrame est vide, essayer une approche alternative
            if result_df.empty:
                print("Requête standard n'a pas retourné de données, essai méthode alternative")
                
                # Récupérer directement toutes les entrées pour voir s'il y a des données
                all_data = self.fetch_all("""
                    SELECT id_produit, type, temps_cycle 
                    FROM completed_products 
                    WHERE temps_cycle > 0
                """)
                
                if all_data:
                    # Construire manuellement un DataFrame
                    types = {}
                    for row in all_data:
                        product_type = row[1]  # type est à l'index 1
                        cycle_time = float(row[2])  # temps_cycle est à l'index 2
                        
                        if product_type not in types:
                            types[product_type] = []
                        types[product_type].append(cycle_time)
                    
                    # Calculer les moyennes
                    result_list = []
                    for product_type, cycle_times in types.items():
                        avg_cycle_time = sum(cycle_times) / len(cycle_times)
                        result_list.append({'type': product_type, 'temps_cycle': avg_cycle_time})
                    
                    result_df = pd.DataFrame(result_list)
            
            # Afficher des informations détaillées pour le débogage
            raw_times = self.fetch_all("""
                SELECT id_produit, type, heure_debut, heure_fin, temps_cycle
                FROM completed_products
                ORDER BY type, id_produit
            """)
            
            print("Données brutes des temps de cycle des produits complétés:")
            for prod in raw_times:
                prod_id, prod_type, start, end, cycle = prod
                print(f"  ID: {prod_id}, Type: {prod_type}, Début: {start}, Fin: {end}, Cycle: {cycle:.2f}")
            
            if not result_df.empty:
                print("Utilisation des temps de cycle réels:")
                for index, row in result_df.iterrows():
                    print(f"  Type: {row['type']}, Temps de cycle moyen: {row['temps_cycle']:.2f}")
            else:
                print("Aucun temps de cycle disponible après traitement")
            
            return result_df
        
        except Exception as e:
            print(f"Erreur lors de la récupération des temps de cycle: {e}")
            import traceback
            traceback.print_exc()
            # Retourner un DataFrame vide mais correctement formaté
            return pd.DataFrame(columns=['type', 'temps_cycle'])
    
    def get_production_timeline(self):
        """Récupère les données pour créer un timeline de production"""
        query = """
            SELECT s.tick, 
                   s.nombre_produits_waiting, 
                   s.nombre_produits_in_progress, 
                   s.nombre_produits_completed
            FROM snapshot s
            ORDER BY s.tick
        """
        
        return self.fetch_df(query)
    
    def get_machine_timeline(self):
        """Récupère les données pour créer un timeline d'activité des machines"""
        query = """
            SELECT s.tick, 
                   s.nombre_machines_idle, 
                   s.nombre_machines_processing, 
                   s.nombre_machines_down
            FROM snapshot s
            ORDER BY s.tick
        """
        
        return self.fetch_df(query)
    
    def get_production_efficiency(self, total_products_created=None):
        """
        Calcule l'efficacité de production selon la formule:
        (nombre de produits complétés réels) / nombre de produit théorique
        
        Args:
            total_products_created: Nombre total de produits créés lors du lancement
        
        Returns:
            dict: Informations sur l'efficacité de production
        """
        # Constante: capacité théorique fixée à 20
        CAPACITE_THEORIQUE = 20
        
        if total_products_created is None or total_products_created <= 0:
            total_products_created = 0
            print("Aucun produit créé - efficacité à 0%")
            return {
                "completed": 0,
                "total": CAPACITE_THEORIQUE,
                "efficiency": 0,
                "sim_time": 0
            }
        
        # Récupérer le nombre de produits dans la table des produits complétés
        # qui est plus fiable que le calcul par différence
        completed_products_query = "SELECT COUNT(*) FROM completed_products WHERE temps_cycle IS NOT NULL AND temps_cycle > 0"
        completed_products_with_cycle = self.fetch_one(completed_products_query)[0]
        
        # Récupérer également le nombre total de produits complétés, même sans cycle calculable
        total_completed_query = "SELECT COUNT(*) FROM completed_products"
        total_completed_products = self.fetch_one(total_completed_query)[0]
        
        # Récupérer le nombre de produits actuellement actifs
        active_products_query = "SELECT COUNT(*) FROM produit"
        active_products = self.fetch_one(active_products_query)[0]
        
        print(f"⚠️ Données d'efficacité: {total_completed_products} produits complétés (dont {completed_products_with_cycle} avec cycle valide) sur {total_products_created} créés, {active_products} actifs")
        
        # Récupérer le temps de simulation pour information
        sim_time_result = self.fetch_one("SELECT MAX(tick) FROM snapshot")
        sim_time = 1.0 if not sim_time_result or not sim_time_result[0] else max(float(sim_time_result[0]), 1.0)
        
        # Calculer l'efficacité avec le nombre réel de produits complétés
        efficiency = (total_completed_products / CAPACITE_THEORIQUE) * 100 if CAPACITE_THEORIQUE > 0 else 0
        
        # Limiter l'efficacité à 100% maximum
        efficiency = min(efficiency, 100)
        
        return {
            "completed": total_completed_products,
            "completed_with_cycle": completed_products_with_cycle,
            "total": CAPACITE_THEORIQUE,
            "efficiency": efficiency,
            "sim_time": sim_time
        }
    
    def get_production_rate(self):
        """Calcule le taux de production (produits complétés par unité de temps)"""
        query = """
            SELECT 
                (SELECT COUNT(*) FROM produit WHERE etat = 'Completed') as produits_completes,
                (SELECT MAX(tick) FROM snapshot) as temps_simulation
            FROM produit
            LIMIT 1
        """
        
        result = self.fetch_one(query)
        if result:
            completed, sim_time = result
            
            # Éviter les divisions par zéro
            if sim_time:
                rate = completed / sim_time
                return rate
        
        return 0
    
    def get_netlogo_product_data(self, product_data):
        """Convertit les données d'un produit NetLogo au format adapté pour notre base de données"""
        return {
            "NetlogoTurtle-ID": product_data.get("who", -1),
            "ProductType": product_data.get("ProductType", "Unknown"),
            "Product.State": product_data.get("Product.State", "Waiting"),
            "CurrentSequenceOrder": product_data.get("CurrentSequenceOrder", 0),
            "ProductOperations": product_data.get("ProductOperations", []),
            "Next.Product.Operation": product_data.get("Next.Product.Operation", ""),
            "ProductRealStart": product_data.get("ProductRealStart", []),
            "ProductRealCompletion": product_data.get("ProductRealCompletion", []),
            "Last.Node": product_data.get("Last.Node", 0),
            "Next.Node": product_data.get("Next.Node", 0),
            "Heading.Workstation": product_data.get("Heading.Workstation", ""),
            "Next.Product.status": product_data.get("Next.Product.status", 0),
            "Next.Product.Completion.Time": product_data.get("Next.Product.Completion.Time", 0)
        }
    
    def get_netlogo_machine_data(self, machine_data):
        """Convertit les données d'une machine NetLogo au format adapté pour notre base de données"""
        return {
            "Machine.Name": machine_data.get("Machine.Name", "Unknown"),
            "Machine.State": machine_data.get("Machine.State", "Idle"),
            "Next.Completion": machine_data.get("Next.Completion", 0),
            "Machine.Operations.Type": machine_data.get("Machine.Operations.Type", []),
            "Machine.Operations.Time": machine_data.get("Machine.Operations.Time", []),
            "xcor": machine_data.get("xcor", 0),
            "ycor": machine_data.get("ycor", 0),
            "heading": machine_data.get("heading", 0)
        }
    
    def clear_simulation_data(self):
        """Efface les données temporaires de la simulation en cours"""
        try:
            self.execute("DELETE FROM produit")
            self.execute("DELETE FROM machine")
            self.execute("DELETE FROM production")
            print("Données temporaires de simulation effacées")
        except Exception as e:
            print(f"Erreur lors de l'effacement des données: {e}")
    
    def get_product_counts(self):
        """
        Récupère le nombre actuel de produits par type
        
        Returns:
            list: Liste de tuples (type, count)
        """
        try:
            return self.fetch_all("SELECT type, COUNT(*) FROM produit GROUP BY type")
        except Exception as e:
            print(f"Erreur lors de la récupération des comptages de produits: {e}")
            return []

    def save_completed_product(self, product_id, product_type, product_data=None):
        """
        Sauvegarde un produit complété dans la base de données
        
        Args:
            product_id: ID du produit ou dictionnaire contenant les données du produit
            product_type: Type du produit
            product_data: Données du produit déjà récupérées (optionnel)
        """
        try:
            # Vérifier si product_id est un dictionnaire
            original_type = None
            if isinstance(product_id, dict):
                # Si le premier paramètre est un dictionnaire, l'utiliser comme données du produit
                product_data = product_id
                # Extraire l'ID réel du dictionnaire
                actual_id = product_data.get('who', -1)
                if actual_id < 0:
                    print(f"ID de produit invalide dans les données: {product_data}")
                    return None
                product_id = actual_id
                # Conserver le type original du produit s'il est disponible
                original_type = product_data.get('type')
                if original_type:
                    # Remplacer le type fourni par le type du produit
                    product_type = original_type
                    print(f"Utilisation du type d'origine '{original_type}' pour le produit {product_id}")
            
            # Si product_data est None, créer un dictionnaire minimal
            if product_data is None:
                product_data = {}
                
            # NOUVELLE LOGIQUE: Vérification si un produit est complété
            # Priorité 1: Vérifier l'état du produit explicitement
            product_state = product_data.get('state', '').lower()
            is_completed = product_state == 'completed'
            
            if not is_completed:
                # Priorité 2: Vérifier si le temps de fin est défini
                has_end_time = 'end.time' in product_data and product_data.get('end.time', 0) > 0
                if has_end_time:
                    is_completed = True
                else:
                    # Priorité 3: Vérification basée sur les opérations 
                    # (uniquement si les deux premières vérifications ont échoué)
                    has_operations = 'operations' in product_data and product_data.get('operations')
                    next_op_empty = 'next.operation' in product_data and not product_data.get('next.operation')
                    if has_operations and next_op_empty:
                        is_completed = True
            
            # Si le produit n'est toujours pas détecté comme complété, on arrête
            if not is_completed:
                print(f"Produit {product_id} non détecté comme complété, sauvegarde ignorée")
                return None
            
            # Extraire les temps de début et fin du cycle
            cycle_time = None
            start_time = None
            end_time = None
            
            # Calculer le temps de cycle à partir des données disponibles
            if 'start.time' in product_data and 'end.time' in product_data:
                try:
                    start_time = float(product_data.get('start.time', 0))
                    end_time = float(product_data.get('end.time', 0))
                    
                    # Vérifier la validité des valeurs
                    if end_time > start_time:
                        cycle_time = end_time - start_time
                        print(f"Temps de cycle calculé pour {product_id}: {cycle_time:.2f}")
                except (ValueError, TypeError) as e:
                    print(f"Erreur lors de la conversion des temps pour le produit {product_id}: {e}")
            
            # Vérifier si le produit a une liste productrealstart
            elif 'productrealstart' in product_data:
                start_times = product_data.get('productrealstart', [])
                
                # Vérifier si on a une liste ou un objet avec des méthodes d'accès
                if not isinstance(start_times, list) and hasattr(start_times, '__getitem__'):
                    try:
                        start_times = list(start_times)
                    except Exception:
                        print(f"Impossible de convertir productrealstart en liste pour le produit {product_id}")
                
                # Calculer le temps de cycle si on a au moins un début et une fin
                if start_times and len(start_times) >= 2:
                    try:
                        start_time = float(start_times[0])
                        end_time = float(start_times[-1])
                        
                        # Vérifier la validité des valeurs
                        if end_time > start_time:
                            cycle_time = end_time - start_time
                    except (ValueError, TypeError) as e:
                        print(f"Erreur lors de la conversion des temps pour le produit {product_id}: {e}")
            
            # Si on n'a pas pu calculer le cycle, essayer de récupérer depuis la base
            if cycle_time is None:
                # Récupérer les données du produit depuis la base de données
                query = "SELECT heure_debut, heure_fin, type FROM produit WHERE id_produit = ?"
                try:
                    product_row = self.fetch_one(query, (int(product_id),))
                    
                    if product_row:
                        db_start = product_row[0]
                        db_end = product_row[1]
                        db_type = product_row[2]
                        
                        # Si aucun type n'a été fourni ou trouvé, utiliser celui de la base
                        if not original_type and (not product_type or product_type.isdigit()):
                            product_type = db_type
                            print(f"Utilisation du type de la base '{db_type}' pour le produit {product_id}")
                        
                        if db_start is not None and db_end is not None and db_end > db_start:
                            start_time = float(db_start)
                            end_time = float(db_end)
                            cycle_time = end_time - start_time
                except Exception as e:
                    print(f"Erreur lors de la récupération des données de temps depuis la base: {e}")
            
            # IMPORTANT: S'assurer que le type n'est pas numérique (11, 12, etc.)
            if product_type and product_type.isdigit():
                print(f"ATTENTION: Type numérique détecté '{product_type}' pour le produit {product_id}, correction requise")
                # Essayer de retrouver le type réel à partir du dictionnaire des données
                if original_type:
                    product_type = original_type
                    print(f"Correction du type à '{original_type}'")
            
            # S'assurer que les variables sont définies avant d'insérer dans la base
            if cycle_time is not None and start_time is not None and end_time is not None:
                print(f"Produit {product_id} de type {product_type} complété avec "
                      f"cycle calculé: {cycle_time:.2f}, début: {start_time:.2f}, fin: {end_time:.2f}")
                
                # Récupérer l'ID de simulation actuelle (ou utiliser 1 par défaut)
                current_sim_id = self.fetch_one("SELECT MAX(id_simulation) FROM simulation")[0] or 1
                
                # Vérifier si ce produit existe déjà dans la table des produits complétés
                existing = self.fetch_one("SELECT id_produit FROM completed_products WHERE id_produit = ?", (int(product_id),))
                
                if existing:
                    # Mettre à jour le produit existant
                    query = """
                        UPDATE completed_products
                        SET type = ?, heure_debut = ?, heure_fin = ?, temps_cycle = ?
                        WHERE id_produit = ?
                    """
                    self.execute(query, (product_type, start_time, end_time, cycle_time, int(product_id)))
                else:
                    # Insérer le nouveau produit complété
                    query = """
                        INSERT INTO completed_products (id_produit, type, heure_debut, heure_fin, temps_cycle, simulation_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """
                    self.execute(query, (int(product_id), product_type, start_time, end_time, cycle_time, current_sim_id))
                
                return product_id
            else:
                print(f"Impossible de calculer le temps de cycle pour le produit {product_id}: données manquantes")
                return None
                
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du produit complété {product_id}: {e}")
            import traceback
            traceback.print_exc()
            return None