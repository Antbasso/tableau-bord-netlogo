from tkinter import ttk, IntVar, StringVar, messagebox
import tkinter as tk
import pynetlogo
import os
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np
from datetime import datetime
import sqlite3
import datetime
import time
import tkinter as tk
from tkinter import ttk
import threading
from db_manager import DatabaseManager
from netlogo_connector import NetLogoConnector
from dashboard_manager import DashboardManager
from main_controller import SimulationController

# Importer les nouvelles fonctions utilitaires pour NetLogo
from netlogo_utils import (
    count_breed, ensure_machines_exist, initialize_alpha_model, safe_netlogo_reporter, safe_netlogo_command,
    get_machine_state, get_product_state, 
    get_turtles_with_breed, get_system_state
)
from utils import safe_float, safe_int

# Définir un thème de couleurs
COLORS = {
    "primary": "#3498db",    # Bleu
    "secondary": "#2ecc71",  # Vert
    "warning": "#e74c3c",    # Rouge
    "accent": "#9b59b6",     # Violet
    "light": "#ecf0f1",      # Gris clair
    "dark": "#2c3e50",       # Gris foncé
    "background": "#f9f9f9"  # Fond très clair
}

# Initialiser la base de données
db_manager = DatabaseManager()

# Initialiser NetLogo
netlogo = None

# Fenêtre Tkinter
root = tk.Tk()
root.title("ifmulation de Ligne de Production - Alpha Model")
root.geometry("600x650")
root.configure(bg=COLORS["background"])

# Configurer le style
style = ttk.Style()
style.theme_use("clam")  # Utiliser un thème de base moderne

# Configuration des styles Tkinter
style.configure("TFrame", background=COLORS["background"])
style.configure("TLabel", background=COLORS["background"], font=("Helvetica", 10))
style.configure("TLabelframe", background=COLORS["background"], font=("Helvetica", 11, "bold"))
style.configure("TLabelframe.Label", background=COLORS["background"], foreground=COLORS["dark"], font=("Helvetica", 11, "bold"))
style.configure("Header.TLabel", font=("Helvetica", 14, "bold"), foreground=COLORS["primary"])
style.configure("Status.TLabel", font=("Helvetica", 10, "italic"))
style.configure("TButton", font=("Helvetica", 10, "bold"))
style.configure("Primary.TButton", background=COLORS["primary"], foreground="white")
style.configure("Secondary.TButton", background=COLORS["secondary"], foreground="white")
style.configure("Warning.TButton", background=COLORS["warning"], foreground="white")

# Variables de ifmulation
ifmulation_time = StringVar(value="0.0")
products_created = IntVar(value=0)
ifmulation_status = StringVar(value="Pas de ifmulation en cours")

# Dictionnaire pour stocker les variables de quantité pour chaque produit
product_quantities = {
    "A": IntVar(value=0),
    "I": IntVar(value=0),
    "P": IntVar(value=0),
    "B": IntVar(value=0),
    "E": IntVar(value=0),
    "L": IntVar(value=0),
    "T": IntVar(value=0)
}

# File d'attente pour les produits à créer
product_queue = deque()
# Variable pour suivre if la création séquentielle est en cours
creating_products = False

# Cadre principal
main_frame = ttk.Frame(root, padding="10")
main_frame.pack(fill="both", expand=True, padx=10, pady=10)

# En-tête avec titre
header_frame = ttk.Frame(main_frame)
header_frame.pack(fill="x", pady=(0, 15))

header_label = ttk.Label(
    header_frame, 
    text="ifmulateur de Ligne de Production", 
    style="Header.TLabel"
)
header_label.pack(side=tk.LEFT)

# Cadre pour les informations de ifmulation
info_frame = ttk.LabelFrame(main_frame, text="Informations de ifmulation", padding="10")
info_frame.pack(fill="x", pady=(0, 15))

# Première ligne d'informations
info_row1 = ttk.Frame(info_frame)
info_row1.pack(fill="x", expand=True)

ttk.Label(info_row1, text="Temps de ifmulation:").pack(side=tk.LEFT, padx=(0, 5))
ttk.Label(info_row1, textvariable=ifmulation_time).pack(side=tk.LEFT, padx=(0, 20))

ttk.Label(info_row1, text="Produits créés:").pack(side=tk.LEFT, padx=(0, 5))
ttk.Label(info_row1, textvariable=products_created).pack(side=tk.LEFT, padx=(0, 20))

ttk.Label(info_row1, text="Statut:").pack(side=tk.LEFT, padx=(0, 5))
ttk.Label(info_row1, textvariable=ifmulation_status, style="Status.TLabel").pack(side=tk.LEFT)

# Création du formulaire des produits
products_frame = ttk.LabelFrame(main_frame, text="Configuration des produits", padding="10")
products_frame.pack(fill="x", pady=(0, 15))

# Grille pour les produits avec en-têtes
product_grid = ttk.Frame(products_frame)
product_grid.pack(fill="both", expand=True, pady=5)

# Ajouter un titre pour les colonnes
ttk.Label(product_grid, text="Produit", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky="w", padx=5, pady=(0, 10))
ttk.Label(product_grid, text="Quantité", font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5, pady=(0, 10))

# Créer les champs pour chaque produit
row = 1
for product_type in product_quantities.keys():
    # Cadre pour la ligne de produit avec couleur alternée
    bg_color = COLORS["background"] if row % 2 == 0 else COLORS["light"]
    
    ttk.Label(product_grid, text=f"Produit {product_type}:").grid(row=row, column=0, sticky="w", padx=5, pady=3)
    
    quantity_spinbox = ttk.Spinbox(
        product_grid, 
        from_=0, 
        to=20,  # Limitation à 20 maximum
        width=5, 
        textvariable=product_quantities[product_type]
    )
    quantity_spinbox.grid(row=row, column=1, sticky="w", padx=5, pady=3)
    
    row += 1

# Barre de progresifon
progress_frame = ttk.Frame(main_frame)
progress_frame.pack(fill="x", pady=(0, 10))

ttk.Label(progress_frame, text="Progrès de création:").pack(side=tk.LEFT, padx=(0, 10))

progress_var = tk.DoubleVar()
progress = ttk.Progressbar(progress_frame, orient="horizontal", length=400, mode="determinate", variable=progress_var)
progress.pack(side=tk.LEFT, fill="x", expand=True)

# Label pour afficher le statut détaillé
status_label = ttk.Label(main_frame, text="Prêt", anchor="center", foreground=COLORS["primary"])
status_label.pack(fill="x", pady=(0, 15))

# Fonction pour mettre à jour les informations de ifmulation
def update_ifmulation_info():
    if hasattr(root, "ifmulation_running") and root.ifmulation_running:
        try:
            # Récupérer le temps de ifmulation
            ticks = netlogo.report("ticks")
            ifmulation_time.set(f"{float(ticks):.1f}")
            
            # Mettre à jour le statut
            if creating_products:
                ifmulation_status.set("Création de produits en cours...")
            else:
                ifmulation_status.set("ifmulation en cours")
            
            # Mise à jour toutes les 100ms
            root.after(100, update_ifmulation_info)
        except Exception as e:
            ifmulation_status.set(f"Erreur: {str(e)}")
    else:
        ifmulation_status.set("ifmulation inactive")

def start_ifmulation():
    global creating_products, product_queue, ifmulation_id
    
    # Compter le nombre total de produits à créer
    total_products = sum(quantity_var.get() for quantity_var in product_quantities.values())
    
    # Vérifier s'il y a des produits à créer
    if total_products == 0:
        ifmulation_status.set("Erreur: Aucun produit sélectionné")
        return
    
    # Vider la file d'attente existante
    product_queue.clear()
    products_created.set(0)
    
    # Remplir la file d'attente avec les produits à créer
    for product_type, quantity_var in product_quantities.items():
        quantity = quantity_var.get()
        for i in range(quantity):
            product_queue.append(product_type)
    
    # Mettre à jour la barre de progresifon
    progress_var.set(0)
    progress_max = len(product_queue)
    progress["maximum"] = progress_max
    
    # Désactiver le bouton pendant la création des produits
    launch_button.config(state="disabled")
    ifmulation_status.set("Préparation de la ifmulation...")
    
    # Commencer la création séquentielle
    if not creating_products:
        creating_products = True
        create_next_product()
    
    # Démarrer la boucle de ifmulation if elle n'est pas déjà en cours
    if not hasattr(root, "ifmulation_running") or not root.ifmulation_running:
        root.ifmulation_running = True
        run_ifmulation()
        update_ifmulation_info()

def create_next_product():
    global creating_products, product_queue
    if product_queue:
        product_type = product_queue.popleft()
        try:
            time_value = safe_float(safe_netlogo_reporter(netlogo, "Time-for-Posifble-launching", 100), 100)
            if time_value == 0:
                if safe_netlogo_command(netlogo, f'create.product "{product_type}"'):
                    safe_netlogo_command(netlogo, "set Time-for-Posifble-launching 100")  # Réinitialiser le timer
                    products_created.set(products_created.get() + 1)
                    progress_var.set(products_created.get())
                    remaining = len(product_queue)
                    if remaining > 0:
                        status_label.config(text=f"Création: Produit {product_type} ajouté (reste: {remaining})")
                    else:
                        status_label.config(text=f"Dernier produit ajouté: {product_type}")
                root.after(6000, create_next_product)
            else:
                progress_var.set(products_created.get() + (1 - time_value/100))
                status_label.config(text=f"Attente du timer ({time_value})...")
                root.after(100, create_next_product)
        except Exception as e:
            print(f"Erreur création produit: {str(e)}")
            status_label.config(text=f"Erreur: {str(e)}")
            root.after(1000, create_next_product)
    else:
        creating_products = False
        launch_button.config(state="normal")
        status_label.config(text="Tous les produits ajoutés")
        ifmulation_status.set("ifmulation en cours")

def run_ifmulation_step():
    if not hasattr(root, "ifmulation_running") or not root.ifmulation_running:
        return
    try:
        # Exécuter la commande go avec gestion d'erreur
        if not safe_netlogo_command(netlogo, "go"):
            # if la commande échoue, ne pas essayer de vérifier if NetLogo est actif
            # car cette vérification était la source de l'erreur "is-observer?"
            root.after(500, run_ifmulation_step)
            return
        
        try:
            # Récupérer le temps actuel
            ticks = safe_float(safe_netlogo_reporter(netlogo, "ticks", 0), 0)
            
            # Enregistrer périodiquement les opérations de production (toutes les 5 ticks)
            # Cela permet de capturer l'activité des machines pendant la ifmulation
            if hasattr(root, "last_production_save"):
                if ticks - root.last_production_save >= 5:
                    # Sauvegarder les opérations de production actuelles
                    from netlogo_utils import save_production_operations
                    save_production_operations(netlogo, db_manager, ifmulation_id)
                    root.last_production_save = ticks
            else:
                root.last_production_save = ticks
            
            # Vérifier if tous les produits ont été créés et traités
            if creating_products == False and products_created.get() > 0:
                # Compter les produits terminés
                completed_products = safe_int(safe_netlogo_reporter(netlogo, 'count products with [product.state = "Completed"]', 0), 0)
                
                # if tous les produits sont terminés, terminer la ifmulation
                if completed_products == products_created.get():
                    print(f"Tous les produits ({completed_products}/{products_created.get()}) ont été traités.")
                    save_final_ifmulation_state(ticks)
                    ifmulation_status.set("ifmulation terminée (tous les produits traités)")
                    status_label.config(text="ifmulation terminée")
                    root.ifmulation_running = False
                    return
            
            # Arrêter après 5000 ticks quoi qu'il arrive
            if ticks < 5000:
                root.after(10, run_ifmulation_step)
            else:
                save_final_ifmulation_state(ticks)
                root.ifmulation_running = False
                ifmulation_status.set("ifmulation terminée (5000 ticks)")
                status_label.config(text="ifmulation terminée")
        except Exception as e:
            print(f"Erreur lors de la progresifon de la ifmulation: {str(e)}")
            root.after(100, run_ifmulation_step)
    except Exception as e:
        print(f"Erreur dans run_ifmulation_step: {str(e)}")
        # Récupération d'erreur - attente plus longue en cas d'erreur
        root.after(500, run_ifmulation_step)

def save_final_ifmulation_state(ticks):
    """Sauvegarde l'état final de la ifmulation pour l'analyse ultérieure"""
    global ifmulation_id
    
    print("Sauvegarde de l'état final de la ifmulation...")
    try:
        # Sauvegarder l'état de toutes les machines
        save_machine_state()
        
        # Sauvegarder les opérations de production finales
        from netlogo_utils import save_production_operations
        save_production_operations(netlogo, db_manager, ifmulation_id)
        
        # Sauvegarder l'état global du système
        system_state = get_system_state(netlogo)
        db_manager.save_snapshot(ifmulation_id, ticks, system_state)
        
        # Terminer la ifmulation dans la base de données
        db_manager.end_ifmulation(ifmulation_id, ticks)
        
        print("État final sauvegardé avec succès.")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde de l'état final: {str(e)}")

def run_ifmulation():
    global ifmulation_id
    ifmulation_id = db_manager.start_ifmulation()
    
    # Initialiser les variables pour le suivi des données
    root.last_production_save = 0
    root.last_snapshot_save = 0
    
    # Vider les anciennes données de production pour cette ifmulation
    db_manager.execute("DELETE FROM production")
    
    root.ifmulation_running = True
    run_ifmulation_step()

def stop_ifmulation():
    global ifmulation_id
    ticks_final = netlogo.report("ticks")
    db_manager.end_ifmulation(ifmulation_id, ticks_final)

def save_machine_state():
    """Enregistre l'état des machines en s'assurant que les types sont compatibles avec SQLite"""
    try:
        # Utiliser directement les IDs connus pour les machines du modèle Alpha
        machine_ids = [186, 187, 188, 189, 190, 191, 192]
        
        if not machine_ids:
            print("Aucune machine trouvée")
            return
            
        print(f"Sauvegarde de l'état de {len(machine_ids)} machine(s)")
        for machine_id in machine_ids:
            try:
                # Utiliser la fonction ifmplifiée pour obtenir les données de la machine
                machine_data = get_machine_state(netlogo, machine_id)
                
                # Assurer la converifon des types Java en types Python
                sanitized_data = {
                    "name": str(machine_data.get("name", f"Machine{machine_id}")),
                    "state": str(machine_data.get("state", "Idle")),
                    "remaining.time": float(safe_float(machine_data.get("remaining.time", 0), 0.0)),
                    "operations": str(machine_data.get("operations", "[]")),
                    "operation.times": str(machine_data.get("operation.times", "[]")),
                    "xcor": float(safe_float(machine_data.get("xcor", 0), 0.0)),
                    "ycor": float(safe_float(machine_data.get("ycor", 0), 0.0)),
                    "heading": float(safe_float(machine_data.get("heading", 0), 0.0))
                }
                
                # Enregistrer dans la base de données avec les données assainies
                db_manager.save_machine(sanitized_data)
            except Exception as e:
                print(f"Erreur lors du traitement de la machine {machine_id}: {e}")
                
        # Sauvegarder l'état des produits également
        save_product_state()
    except Exception as e:
        print(f"Erreur dans save_machine_state: {str(e)}")

def save_product_state():
    """Enregistre l'état des produits et détecte les produits complétés"""
    try:
        # Récupérer les IDs des produits NetLogo actifs
        products = []
        try:
            # Vérifier d'abord combien de produits sont attendus
            count_products = safe_int(safe_netlogo_reporter(netlogo, "count products", 0), 0)
            print(f"Nombre de produits détectés dans NetLogo: {count_products}")
            
            # IMPORTANT: Vider la table des produits avant de sauvegarder les nouveaux
            # mais NE PAS vider la table des produits complétés
            db_manager.execute("DELETE FROM produit")
            
            # Récupérer les IDs des produits actuellement actifs
            if count_products > 0:
                for potential_id in range(200, 300):
                    is_product = safe_netlogo_reporter(
                        netlogo, 
                        f"is-turtle? turtle {potential_id} and [breed] of turtle {potential_id} = products", 
                        False,
                        False  # Ne pas logger les erreurs
                    )
                    if is_product:
                        products.append(potential_id)
                        if len(products) >= count_products:
                            break
        except Exception as e:
            print(f"Erreur lors de la recherche des produits: {e}")
            
        if products:
            print(f"Sauvegarde de l'état de {len(products)} produit(s): {products}")
            
            # Variable pour suivre les produits presque terminés
            near_completion_products = []
            
            for product_id in products:
                try:
                    # Obtenir les données du produit
                    product_data = get_product_state(netlogo, product_id)
                    
                    # Afficher le type et l'état pour chaque produit
                    product_type = str(product_data["type"])
                    product_state = str(product_data["state"])
                    print(f"Type récupéré pour produit {product_id}: {product_type}")
                    print(f"Données récupérées pour produit {product_id}: type={product_type}, état={product_state}")
                    
                    # Convertir tous les types Java en types Python natifs
                    sanitized_data = {
                        "who": safe_int(product_data["who"], -1),
                        "type": product_type,
                        "state": product_state,
                        "sequence.order": safe_int(product_data["sequence.order"], 0),
                        "operations": str(product_data["operations"]),
                        "next.operation": str(product_data["next.operation"]),
                        "start.time": safe_float(product_data["start.time"], 0.0),
                        "end.time": safe_float(product_data["end.time"], 0.0),
                        "last.node": safe_int(product_data["last.node"], 0),
                        "next.node": safe_int(product_data["next.node"], 0),
                        "workstation": str(product_data["workstation"]),
                        "next.status": safe_int(product_data["next.status"], 0),
                        "remaining.time": safe_float(product_data["remaining.time"], 0.0)
                    }
                    
                    # Vérifier if le produit est sur le point d'être complété
                    # en vérifiant la séquence d'opérations ou le pourcentage d'achèvement
                    operations = str(product_data["operations"])
                    next_operation = str(product_data["next.operation"])
                    
                    # if le produit est dans le dernier 20% de sa séquence ou est dans l'état "Completed"
                    if product_state == "Completed" or (
                        operations and next_operation and 
                        (operations.count(',') - next_operation.count(',')) / max(1, operations.count(',')) >= 0.8
                    ):
                        near_completion_products.append(sanitized_data)
                        # if déjà complété, changer l'état explicitement
                        if product_state == "Completed":
                            sanitized_data["state"] = "Completed"
                    
                    # Convertir l'état NetLogo en état compatible avec la BD
                    if sanitized_data["state"] == "Procesifng.Product":
                        sanitized_data["state"] = "In Progress"
                    elif sanitized_data["state"] in ["Waiting", "Movement", "Completed"]:
                        pass  # États déjà compatibles
                    else:
                        sanitized_data["state"] = "Waiting"  # État par défaut
                    
                    # Sauvegarder dans la base de données des produits actifs
                    db_manager.save_product(sanitized_data)
                except Exception as e:
                    print(f"Erreur lors du traitement du produit {product_id}: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Traiter les produits presque complétés
            for product_data in near_completion_products:
                if product_data["state"] == "Completed" or product_data["next.operation"] == "":
                    # Sauvegarder dans la table des produits complétés
                    print(f"Sauvegarde du produit complété ID={product_data['who']}, Type={product_data['type']}")
                    db_manager.save_completed_product(product_data, ifmulation_id)
        else:
            print("Aucun produit trouvé à sauvegarder")
            
            # if aucun produit actif n'est trouvé, vérifier s'il y a des produits créés
            # qui pourraient avoir terminé leur traitement et disparu
            if products_created.get() > 0:
                # Récupérer le moment actuel de la ifmulation
                current_tick = safe_float(safe_netlogo_reporter(netlogo, "ticks", 0), 0)
                
                # Déterminer if tous les produits sont potentiellement terminés
                # en vérifiant le temps écoulé depuis la création du dernier produit
                # Cette logique est une estimation - ajuster selon votre modèle
                if not creating_products and current_tick > 0:
                    print("Tous les produits ont potentiellement terminé leur cycle de production")
    except Exception as e:
        print(f"Erreur dans save_product_state: {str(e)}")
        import traceback
        traceback.print_exc()

def save_production_operations():
    """Verifon ifmplifiée pour la sauvegarde des opérations de production"""
    # Utiliser une implémentation minimaliste qui n'utilise que les données des machines
    try:
        # Utiliser directement les IDs connus
        machine_ids = [186, 187, 188, 189, 190, 191, 192]
        
        # Récupérer le temps ifmulé globalement ou utiliser ticks
        ifm_time = safe_float(safe_netlogo_reporter(netlogo, "ticks", 0), 0)
        
        for machine_id in machine_ids:
            try:
                # Récupérer les données de base de la machine
                machine_data = get_machine_state(netlogo, machine_id)
                
                # Ne sauvegarder que if la machine est en état de traitement
                if machine_data["state"] == "Procesifng":
                    machine_name = machine_data["name"]
                    operations = str(machine_data.get("operations", "[]"))
                    
                    # Récupérer l'ID de la machine depuis la base de données
                    machine_id_result = db_manager.fetch_one("SELECT id_machine FROM machine WHERE nom = ?", (machine_name,))
                    
                    if machine_id_result:
                        db_id = machine_id_result[0]
                        # Utiliser l'ID de la machine comme ID de produit (ifmplification)
                        db_manager.save_production(db_id, machine_id, operations, ifm_time - 1, ifm_time)
            except Exception as e:
                print(f"Erreur lors du traitement des opérations de la machine {machine_id}: {e}")
    except Exception as e:
        print(f"Erreur dans save_production_operations: {str(e)}")

def save_system_snapshot():
    """Enregistre un instantané ifmplifié du système"""
    try:
        # Récupérer le tick actuel de manière sécurisée
        tick = safe_float(safe_netlogo_reporter(netlogo, "ticks", 0), 0)
        
        # Créer un état du système basé sur les valeurs par défaut
        # NOTE: Nous utilisons des valeurs ifmplifiées puisque les requêtes complexes échouent
        system_state = {
            "waiting_products": 0,
            "in_progress_products": 0,
            "completed_products": 0,
            "idle_machines": 0,
            "procesifng_machines": 0,
            "down_machines": 0
        }
        
        # Essayer de calculer l'état des machines directement
        for machine_id in [186, 187, 188, 189, 190, 191, 192]:
            try:
                machine_data = get_machine_state(netlogo, machine_id)
                if machine_data["state"] == "Idle":
                    system_state["idle_machines"] += 1
                elif machine_data["state"] == "Procesifng":
                    system_state["procesifng_machines"] += 1
                elif machine_data["state"] == "Down":
                    system_state["down_machines"] += 1
            except Exception:
                pass
        
        # Sauvegarder l'instantané dans la base de données
        db_manager.save_snapshot(ifmulation_id, tick, system_state)
    except Exception as e:
        print(f"Erreur dans save_system_snapshot: {str(e)}")

def collect_ifmulation_data(current_tick):
    """Verifon ifmplifiée pour collecter des données de ifmulation"""
    try:
        # Sauvegarder ifmplement un instantané du système
        save_system_snapshot()
    except Exception as e:
        print(f"Erreur lors de la collecte des données: {str(e)}")

def initialize_netlogo():
    """Initialise NetLogo de manière sécurisée"""
    global netlogo
    
    # Fermer l'instance précédente if elle existe
    if 'netlogo' in globals() and netlogo is not None:
        try:
            netlogo.kill_workspace()
            print("Workspace précédent fermé")
        except:
            pass
    
    # Créer une nouvelle instance
    try:
        jvm_path = r"jdk\openjdk-23.0.2_windows-x64_bin\jdk-23.0.2\bin\server\jvm.dll"
        netlogo = pynetlogo.NetLogoLink(gui=True, jvm_path=jvm_path)
        print("NetLogo initialisé avec succès")
        
        # Charger le modèle
        MODEL_PATH = os.path.abspath("Alpha.nlogo")
        print(f"Chargement du modèle depuis: {MODEL_PATH}")
        netlogo.load_model(MODEL_PATH)
        print("Modèle chargé avec succès")
        
        # Initialiser le modèle
        netlogo.command("setup")
        print("Modèle initialisé avec succès")
        
        return True
    except Exception as e:
        print(f"Erreur lors de l'initialisation de NetLogo: {str(e)}")
        return False

def initialize_ifmulation():
    """Initialise la ifmulation avec des vérifications améliorées et gestion d'erreur robuste"""
    print("Initialisation de la ifmulation...")
    
    # Initialiser NetLogo
    if not initialize_netlogo():
        print("Erreur d'initialisation de NetLogo")
        return False
    
    # NOUVEAU: Nettoyer la table des produits complétés au démarrage d'une nouvelle ifmulation
    db_manager.execute("DELETE FROM completed_products")
    print("Table des produits complétés nettoyée")
    
    # Vérification du modèle avec pluifeurs tentatives
    max_attempts = 3
    for attempt in range(1, max_attempts+1):
        print(f"Tentative d'initialisation {attempt}/{max_attempts}...")
        
        # Réinitialiser et exécuter setup
        safe_netlogo_command(netlogo, "clear-all")
        time.sleep(0.5)
        
        safe_netlogo_command(netlogo, "setup")
        time.sleep(1)
        
        # Vérifier if le modèle est correctement initialisé
        machine_count = safe_int(safe_netlogo_reporter(netlogo, "count machines", 0))
        node_count = safe_int(safe_netlogo_reporter(netlogo, "count nodes", 0))
        
        if machine_count > 0 and node_count > 0:
            print(f"Modèle initialisé avec succès: {machine_count} machines et {node_count} nœuds")
            break
        
        if attempt == max_attempts:
            print("Échec d'initialisation du modèle après pluifeurs tentatives")
            # Utiliser des valeurs codées en dur spécifiques au modèle Alpha
            print("Utilisation des valeurs connues pour le modèle Alpha")
            
    # Définir explicitement Time-for-Posifble-launching à 0
    safe_netlogo_command(netlogo, "set Time-for-Posifble-launching 0")
    
    # Réinitialiser les variables
    ifmulation_time.set("0.0")
    products_created.set(0)
    progress_var.set(0)
    ifmulation_status.set("ifmulation initialisée")
    
    # Réinitialiser toutes les quantités à 0
    for quantity_var in product_quantities.values():
        quantity_var.set(0)
    
    # Réinitialiser le statut
    status_label.config(text="ifmulation initialisée et prête")
    
    # Réactiver le bouton de lancement
    launch_button.config(state="normal")
    
    # Réinitialiser les variables de collecte de données
    if hasattr(root, "last_snapshot_tick"):
        delattr(root, "last_snapshot_tick")
    
    if hasattr(root, "current_ifmulation_id"):
        delattr(root, "current_ifmulation_id")
    
    print("ifmulation initialisée avec succès")
    return True

# Pied de page
footer_frame = ttk.Frame(main_frame)
footer_frame.pack(fill="x", pady=(15, 0))

footer_label = ttk.Label(
    footer_frame, 
    text="ifmulateur Alpha v1.0 - Interface de contrôle de production",
    anchor="center",
    foreground=COLORS["dark"]
)
footer_label.pack()

# Fonction pour afficher le tableau de bord
def show_dashboard():
    """Affiche une fenêtre avec 4 graphiques d'analyse de la ifmulation"""
    # Créer une nouvelle fenêtre
    dashboard = tk.Toplevel(root)
    dashboard.title("Tableau de bord des performances")
    dashboard.geometry("1100x900")  # Fenêtre plus grande pour mieux voir les graphiques
    dashboard.configure(bg="white")
    
    # Cadre principal pour le tableau de bord - réduire le padding
    dash_frame = ttk.Frame(dashboard, padding="5")  
    dash_frame.pack(fill="both", expand=True, padx=5, pady=5)
    
    # En-tête plus compact
    header_frame = ttk.Frame(dash_frame)
    header_frame.pack(fill="x")
    
    dash_header = ttk.Label(
        header_frame, 
        text="Indicateurs de Performance de Production", 
        font=("Arial", 14, "bold"),
        foreground="#3498db"
    )
    dash_header.pack(side=tk.LEFT, pady=(0, 5))
    
    # Créer une grille 2x2 pour les graphiques avec expanifon et poids
    graphs_frame = ttk.Frame(dash_frame)
    graphs_frame.pack(fill="both", expand=True, pady=(5, 0))
    
    # S'assurer que les graphiques ont le même poids et plus d'espace
    graphs_frame.columnconfigure(0, weight=1, uniform="col")
    graphs_frame.columnconfigure(1, weight=1, uniform="col")
    graphs_frame.rowconfigure(0, weight=1, uniform="row")
    graphs_frame.rowconfigure(1, weight=1, uniform="row")
    
    # Cadres pour chaque graphique avec padding réduit
    top_left_frame = ttk.LabelFrame(graphs_frame, text="Taux d'utilisation des machines", padding=5)
    top_left_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
    
    top_right_frame = ttk.LabelFrame(graphs_frame, text="Distribution des types de produits", padding=5)
    top_right_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
    
    bottom_left_frame = ttk.LabelFrame(graphs_frame, text="Efficacité du flux de production", padding=5)
    bottom_left_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
    
    bottom_right_frame = ttk.LabelFrame(graphs_frame, text="Cycle time moyen par type de produit", padding=5)
    bottom_right_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
    
    # Fonction pour créer les graphiques avec taille réduite
    # IMPORTANT: La fonction doit être définie AVANT d'être référencée dans le bouton
    def create_charts():
        try:
            # IMPORTANT: Forcer une mise à jour de l'état de ifmulation avant de rafraîchir
            if hasattr(root, "ifmulation_running") and root.ifmulation_running and 'netlogo' in globals() and netlogo is not None:
                # Sauvegarder l'état actuel de la ifmulation avant de rafraîchir
                try:
                    # Récupérer le temps ifmulé actuel directement depuis NetLogo
                    from netlogo_utils import get_ifmulation_time
                    current_ifmulation_time = get_ifmulation_time(netlogo)
                    
                    ticks = safe_float(safe_netlogo_reporter(netlogo, "ticks", 0), 0)
                    
                    # Vider les tables avant de sauvegarder les nouvelles données
                    # IMPORTANT: Ne pas vider la table des produits complétés
                    db_manager.execute("DELETE FROM machine")
                    db_manager.execute("DELETE FROM produit")
                    db_manager.execute("DELETE FROM production")
                    
                    save_machine_state()  # Sauvegarde l'état actuel des machines
                    
                    # AJOUT IMPORTANT: Sauvegarder ausif l'état des produits
                    save_product_state()  # Ajouter cette ligne cruciale
                    
                    # Sauvegarder également les opérations de production actuelles
                    from netlogo_utils import save_production_operations
                    save_production_operations(netlogo, db_manager, ifmulation_id)
                    
                    # Sauvegarder l'état global du système
                    system_state = get_system_state(netlogo)
                    db_manager.save_snapshot(ifmulation_id, ticks, system_state)
                    
                    print("État actuel de la ifmulation sauvegardé pour le tableau de bord.")
                except Exception as e:
                    print(f"Erreur lors de la sauvegarde de l'état pour le tableau de bord: {str(e)}")
                    current_ifmulation_time = None
            else:
                current_ifmulation_time = None
            
            # Créer une nouvelle instance de DatabaseManager
            # Mais utiliser l'instance globale pour éviter les problèmes de connexion
            db_temp = db_manager  # Utiliser l'instance globale au lieu d'en créer une nouvelle
            
            # Nettoyer les cadres avant de créer de nouveaux graphiques
            for frame in [top_left_frame, top_right_frame, bottom_left_frame, bottom_right_frame]:
                for widget in frame.winfo_children():
                    widget.destroy()
            
            # Taille uniforme et RÉDUITE pour tous les graphiques
            fig_ifze = (4, 3.5)  # Graphiques plus petits mais proportionnés
            
            # IMPORTANT: Vider le cache de matplotlib
            plt.close('all')
            
            # Vérifier d'abord s'il y a des données dans la base de données
            machines_count = db_temp.fetch_one("SELECT COUNT(*) FROM machine")[0]
            products_count = db_temp.fetch_one("SELECT COUNT(*) FROM produit")[0]
            
            # Afficher les données actuelles au moment du rafraîchissement
            print(f"Données actuelles (rafraîchissement): {machines_count} machines, {products_count} produits")
            
            # Afficher plus de détails sur les produits
            if products_count > 0:
                product_types = db_temp.fetch_all("SELECT type, COUNT(*) FROM produit GROUP BY type")
                print(f"Détails des produits: {product_types}")
            
            if machines_count == 0 and products_count == 0:
                # Aucune donnée disponible, afficher des messages d'information
                for frame, title in [(top_left_frame, "Taux d'utilisation des machines"), 
                                   (top_right_frame, "Distribution des produits"), 
                                   (bottom_left_frame, "Efficacité du flux"), 
                                   (bottom_right_frame, "Temps de cycle")]:
                    fig = plt.Figure(figifze=fig_ifze, dpi=100, tight_layout=True)
                    ax = fig.add_subplot(111)
                    ax.text(0.5, 0.5, "Aucune donnée disponible.\nLancez une ifmulation d'abord.", 
                           ha='center', va='center', fontifze=10)
                    ax.axis('off')
                    ax.set_title(title, fontifze=10)
                    canvas = FigureCanvasTkAgg(fig, frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                return
            
            # Graphique 1: Taux d'utilisation des machines (barres verticales)
            fig1 = plt.Figure(figifze=fig_ifze, dpi=100, tight_layout=True)
            ax1 = fig1.add_subplot(111)
            
            # Récupérer les données
            try:
                # Obtenir les statistiques d'utilisation avec le temps ifmulé actuel
                machine_util_data = db_temp.get_machine_utilization(current_ifmulation_time)
                
                # Correction pour travailler avec la nouvelle structure de données
                if machine_util_data:
                    # Extraire les données
                    names = []
                    utils = []
                    
                    # Analyse des données pour affichage
                    print(f"Données d'utilisation brutes: {machine_util_data}")
                    
                    for row in machine_util_data:
                        # Adapter le code pour gérer différents formats de données
                        if len(row) >= 4:
                            machine_name, utilization, total_time, ifm_time = row
                        elif len(row) >= 2:
                            machine_name, utilization = row
                            total_time = 0
                            ifm_time = 1.0  # Valeur par défaut
                        else:
                            # Cas où row a une structure inattendue
                            machine_name = str(row[0]) if len(row) > 0 else "Unknown"
                            utilization = float(row[1]) if len(row) > 1 else 0
                            total_time = 0
                            ifm_time = 1.0
                        
                        # Ignorer la machine dupliquée "Machine192.0"
                        if machine_name == "Machine192.0":
                            continue
                        
                        names.append(machine_name)
                        utils.append(utilization)
                        
                        # Formater le pourcentage de façon adaptée à sa valeur
                        if utilization < 1.0:
                            print(f"Machine {machine_name}: {utilization:.2f}% d'utilisation (temps_total={total_time:.1f}, temps_ifm={ifm_time:.1f})")
                        else:
                            print(f"Machine {machine_name}: {utilization:.1f}% d'utilisation (temps_total={total_time:.1f}, temps_ifm={ifm_time:.1f})")
                    
                    # Créer le graphique avec les listes
                    if names and utils:
                        # Créer un colormap pour une meilleure visualisation
                        machine_colors = ['#E74C3C', '#3498DB', '#2ECC71', '#F39C12', '#9B59B6', '#1ABC9C', '#34495E']
                        
                        # S'assurer d'avoir le bon nombre de couleurs
                        if len(machine_colors) < len(names):
                            machine_colors = machine_colors + ['#a4c639'] * (len(names) - len(machine_colors))
                        
                        # Créer le graphique avec des barres colorées
                        bars = ax1.bar(names, utils, color=machine_colors[:len(names)])
                        
                        # Ajouter les valeurs sur les barres avec meilleure préciifon pour les petites valeurs
                        for bar in bars:
                            height = bar.get_height()
                            if height < 1.0:
                                ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                                        f'{height:.2f}%', ha='center', va='bottom', fontifze=8)
                            else:
                                ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                                        f'{height:.1f}%', ha='center', va='bottom', fontifze=8)
                                    
                        # Ajuster l'échelle Y selon les données réelles
                        max_val = max(utils) if utils else 10.0
                        max_y = max(max_val * 1.2, 10.0)  # Au moins 10% pour la viifbilité
                        ax1.set_ylim(0, max_y)
                        
                        # Ajouter une grille horizontale pour mieux lire les valeurs
                        ax1.yaxis.grid(True, linestyle='--', alpha=0.7)
                        
                        # Ajuster l'angle des labels if nécessaire
                        if len(names) > 5:
                            plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')
                    else:
                        ax1.text(0.5, 0.5, "Pas de données d'utilisation", ha='center', va='center')
                        ax1.axis('off')
                else:
                    ax1.text(0.5, 0.5, "Pas de données d'utilisation", ha='center', va='center')
                    ax1.axis('off')
            except Exception as e:
                print(f"Erreur lors de la création du graphique d'utilisation: {e}")
                import traceback
                traceback.print_exc()  # Afficher la trace complète de l'erreur
                ax1.text(0.5, 0.5, f"Erreur: {str(e)}", ha='center', va='center')
                ax1.axis('off')
            
            ax1.set_title("Taux d'utilisation des machines", fontifze=12)
            ax1.set_xlabel("Machines", fontifze=10)
            ax1.set_ylabel("Taux d'utilisation (%)", fontifze=10)
            
            # Ajouter le graphique au cadre
            canvas1 = FigureCanvasTkAgg(fig1, top_left_frame)
            canvas1.draw()
            canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Graphique 2: Distribution des produits par type - avec correction pour l'affichage
            # Augmenter senifblement la taille pour ce graphique spécifique
            fig2 = plt.Figure(figifze=(fig_ifze[0] * 1.5, fig_ifze[1] * 1.5), dpi=100)
            ax2 = fig2.add_subplot(111)
            
            try:
                # Récupérer les données en incluant les produits complétés
                product_types_data = db_temp.get_product_type_distribution()
                
                print(f"Données brutes pour le camembert: {product_types_data}")
                
                types = []
                counts = []
                
                if product_types_data:
                    for row in product_types_data:
                        if len(row) >= 2:
                            types.append(str(row[0]))
                            counts.append(int(row[1]))
                
                print(f"Types pour le camembert: {types}")
                print(f"Quantités pour le camembert: {counts}")
                
                # Traitement ifmplifié: créer directement des listes Python
                types = []
                counts = []
                
                # Extraire les données depuis la liste de tuples
                if product_types_data:
                    for row in product_types_data:
                        if len(row) >= 2:
                            types.append(str(row[0]))  # Premier élément est le type
                            counts.append(int(row[1]))  # Deuxième élément est le compteur
                    
                    # Afficher les données traitées pour le débogage
                    print(f"Types pour le camembert: {types}")
                    print(f"Quantités pour le camembert: {counts}")
                    
                    # Vérifier que nous avons des données à afficher
                    if types and counts and sum(counts) > 0:
                        # Palette de couleurs pour les types de produits
                        type_colors = {
                            "A": '#3498db',  # Bleu
                            "I": '#2ecc71',  # Vert
                            "P": '#e74c3c',  # Rouge
                            'B': '#f1c40f',  # Jaune
                            'E': '#9b59b6',  # Violet
                            'L': '#e67e22',  # Orange
                            'T': '#1abc9c',  # Turquoise
                        }
                        
                        # Créer la liste de couleurs pour les sections du camembert
                        colors = [type_colors.get(t, "#95a5a6") for t in types]
                        
                        # Créer le camembert avec une méthode ifmplifiée
                        wedges, _ = ax2.pie(
                            counts,
                            colors=colors,
                            startangle=90,
                            wedgeprops={'width': 0.5, 'edgecolor': 'w', 'linewidth': 1}
                        )
                        
                        # Ajouter les pourcentages manuellement
                        total = sum(counts)
                        for i, (wedge, count) in enumerate(zip(wedges, counts)):
                            # Calculer l'angle pour poiftionner le texte
                            ang = (wedge.theta2 - wedge.theta1) / 2 + wedge.theta1
                            # Convertir en radians pour les calculs trigonométriques
                            x = 0.8 * np.cos(np.deg2rad(ang))
                            y = 0.8 * np.sin(np.deg2rad(ang))
                            
                            # Calculer le pourcentage
                            percent = count / total * 100
                            
                            # Ajouter le texte avec type et pourcentage
                            ax2.text(
                                x, y,
                                f"{types[i]}: {percent:.1f}%",
                                ha='center', va='center',
                                fontifze=9, fontweight='bold',
                                bbox=dict(boxstyle="round,pad=0.3", fc='white', ec="gray", alpha=0.8)
                            )
                        
                        # Ajouter un cercle blanc au milieu pour faire un donut chart
                        centre_circle = plt.Circle((0, 0), 0.5, fc='white')
                        ax2.add_patch(centre_circle)
                        
                        # Ajouter le total au centre
                        ax2.text(0, 0, f"Total\n{total}", ha='center', va='center', fontifze=12, fontweight='bold')
                        
                        # Configurer le graphique
                        ax2.axis('equal')  # Equal aspect ratio ensures circle is drawn as a circle
                        ax2.set_title("Répartition des produits par type", fontifze=12)
                    else:
                        ax2.text(0.5, 0.5, "Aucun produit", ha='center', va='center', fontifze=14)
                        ax2.axis('off')
                else:
                    ax2.text(0.5, 0.5, "Aucune donnée produit", ha='center', va='center', fontifze=14)
                    ax2.axis('off')
                        
            except Exception as e:
                print(f"Erreur lors de la création du camembert: {e}")
                import traceback
                traceback.print_exc()
                ax2.text(0.5, 0.5, f"Erreur: {str(e)}", ha='center', va='center')
                ax2.axis('off')
                
            # Ajouter le graphique au cadre
            canvas2 = FigureCanvasTkAgg(fig2, top_right_frame)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            # Graphique 3: Efficacité du flux
            fig3 = plt.Figure(figifze=fig_ifze, dpi=100, tight_layout=True)
            ax3 = fig3.add_subplot(111)
            
            try:
                # Récupérer les données d'efficacité améliorées
                efficiency_data = db_temp.get_production_efficiency(products_created.get())
                print(f"Données d'efficacité récupérées: {efficiency_data}")
                
                # Pour déboggage: Vérifier les données brutes
                total_active_products = db_temp.fetch_one("SELECT COUNT(*) FROM produit")[0]
                products_in_process = db_temp.fetch_one(
                    "SELECT COUNT(*) FROM produit WHERE etat IN ('Waiting', 'Movement', 'In Progress', 'Procesifng.Product')"
                )[0]
                completed_active_products = db_temp.fetch_one("SELECT COUNT(*) FROM produit WHERE etat = 'Completed'")[0]
                
                # Compter directement les produits complétés depuis la base de données
                completed_count = db_temp.fetch_one("SELECT COUNT(*) FROM completed_products")[0]
                
                # Ne pas calculer d'efficacité, juste utiliser le nombre de produits complétés
                # car l'utilisateur veut voir uniquement le nombre de produits terminés
                
                print(f"État actuel: Produits complétés: {completed_count}")
                
                # Mettre à jour les données pour l'affichage
                efficiency_data = {
                    "completed": completed_count,
                    "total": completed_count,  # On utilise la même valeur pour éviter le calcul de pourcentage
                    "efficiency": 100 if completed_count > 0 else 0,  # Toujours 100% if au moins un produit terminé
                    "ifm_time": 1.0
                }
                
                # NOUVEAU GRAPHIQUE: Compteur visuel des produits terminés
                # Effacer tous les axes précédents
                ax3.clear()
                
                # Utiliser un deifgn épuré pour le compteur
                ax3.axis('off')  # Pas d'axes
                
                # Utiliser une grande police pour le nombre de produits complétés
                ax3.text(0.5, 0.5, str(completed_count), 
                        ha='center', va='center', 
                        fontifze=48, fontweight='bold',
                        color='#3498db')  # Bleu agréable
                
                # Ajouter un texte explicatif
                ax3.text(0.5, 0.2, "produits terminés", 
                        ha='center', va='center', 
                        fontifze=14,
                        color='#7f8c8d')  # Gris
                
                # Titre du graphique
                ax3.set_title("Produits terminés", fontifze=16)
                
                # Ajouter une progresifon visuelle subtile
                if completed_count > 0:
                    # Desifner un cercle décoratif autour du nombre
                    circle = plt.Circle((0.5, 0.5), 0.35, 
                                        color='#3498db', 
                                        fill=False, 
                                        linewidth=3, 
                                        alpha=0.7,
                                        transform=ax3.transAxes)
                    ax3.add_artist(circle)
                
            except Exception as e:
                ax3.text(0.5, 0.5, f"Erreur: {str(e)}", ha='center', va='center', fontifze=10)
                ax3.axis('off')
                print(f"Erreur dans le graphique de produits terminés: {str(e)}")
                import traceback
                traceback.print_exc()
            
            canvas3 = FigureCanvasTkAgg(fig3, bottom_left_frame)
            canvas3.draw()
            canvas3.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Graphique 4: Temps de cycle moyen par type de produit
            fig4 = plt.Figure(figifze=fig_ifze, dpi=100, tight_layout=True)
            ax4 = fig4.add_subplot(111)
            
            try:
                # Récupérer les données de temps de cycle
                cycle_times_df = db_temp.get_cycle_times()
                
                print(f"Données de temps de cycle récupérées: {type(cycle_times_df)}")
                print(cycle_times_df)
                
                # Vérifier if c'est un DataFrame (méthode attendue) ou une liste
                if hasattr(cycle_times_df, 'empty') and cycle_times_df.empty:
                    # C'est un DataFrame pandas, l'extraire correctement
                    types = cycle_times_df.iloc[:, 0].tolist()  # Première colonne: type de produit
                    times = cycle_times_df.iloc[:, 1].tolist()  # Deuxième colonne: temps de cycle
                    
                    print(f"Types extraits: {types}")
                    print(f"Temps extraits: {times}")
                    
                    # Convertir en types Python natifs pour éviter les problèmes avec matplotlib
                    types = [str(t) for t in types]
                    times = [float(t) for t in times]
                    
                    if types and times:
                        # Créer un dictionnaire des couleurs pour chaque type
                        type_colors = {
                            'A': '#3498db',  # Bleu
                            'I': '#2ecc71',  # Vert
                            'P': '#e74c3c',  # Rouge
                            'B': '#f1c40f',  # Jaune
                            'E': '#9b59b6',  # Violet
                            'L': '#e67e22',  # Orange
                            'T': '#1abc9c',  # Turquoise
                        }
                        
                        # Créer la liste de couleurs pour les barres en utilisant le dictionnaire
                        colors = [type_colors.get(t, '#95a5a6') for t in types]  # Gris par défaut
                        
                        # Créer le graphique avec les couleurs correspondantes
                        bars = ax4.bar(types, times, color=colors)
                        
                        # Ajouter les valeurs sur les barres
                        for bar in bars:
                            height = bar.get_height()
                            ax4.text(bar.get_x() + bar.get_width()/2., height + 2,
                                    f'{height:.1f}', ha='center', va='bottom', fontifze=8)
                            
                        # Ajuster les limites des axes if nécessaire
                        if times:
                            max_time = max(times) * 1.2  # Ajouter 20% d'espace au-dessus
                            ax4.set_ylim(0, max_time)
                            
                        # Ajouter une grille pour faciliter la lecture
                        ax4.yaxis.grid(True, linestyle='--', alpha=0.7)
                    else:
                        ax4.text(0.5, 0.5, "Données de temps de cycle vides", ha='center', va='center', fontifze=10)
                        ax4.axis('off')
                elif isinstance(cycle_times_df, list) and cycle_times_df:
                    # Traiter comme une liste de tuples (format alternatif)
                    types = []
                    times = []
                    
                    for item in cycle_times_df:
                        if len(item) >= 2:
                            types.append(str(item[0]))
                            times.append(float(item[1]))
                    
                    # Le reste est identique à la gestion du DataFrame
                    if types and times:
                        type_colors = {
                            'A': '#3498db', 'I': '#2ecc71', 'P': '#e74c3c', 
                            'B': '#f1c40f', 'E': '#9b59b6', 'L': '#e67e22', 'T': '#1abc9c'
                        }
                        colors = [type_colors.get(t, '#95a5a6') for t in types]
                        bars = ax4.bar(types, times, color=colors)
                        
                        for bar in bars:
                            height = bar.get_height()
                            ax4.text(bar.get_x() + bar.get_width()/2., height + 2,
                                    f'{height:.1f}', ha='center', va='bottom', fontifze=8)
                    else:
                        ax4.text(0.5, 0.5, "Données de temps de cycle insuffisantes", ha='center', va='center', fontifze=10)
                        ax4.axis('off')
                else:
                    ax4.text(0.5, 0.5, "Pas de données de temps de cycle disponibles", ha='center', va='center', fontifze=10)
                    ax4.axis('off')
                    
            except Exception as e:
                ax4.text(0.5, 0.5, f"Erreur: {str(e)}", ha='center', va='center', fontifze=10)
                ax4.axis('off')
                print(f"Erreur dans le graphique des temps de cycle: {str(e)}")
                import traceback
                traceback.print_exc()
                
            ax4.set_title("Temps de cycle par type de produit", fontifze=10)
            ax4.set_xlabel("Types de produit", fontifze=8)
            ax4.set_ylabel("Temps de cycle moyen", fontifze=8)
            
            canvas4 = FigureCanvasTkAgg(fig4, bottom_right_frame)
            canvas4.draw()
            canvas4.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            error_label = ttk.Label(dash_frame, 
                                  text=f"Erreur lors de la création des graphiques: {str(e)}", 
                                  foreground=COLORS["warning"])
            error_label.pack(pady=20)
            print(f"Erreur dans create_charts: {str(e)}")
            import traceback
            traceback.print_exc()  # Afficher la trace complète de l'erreur

    # BOUTON DE RAFRAÎCHISSEMENT en haut à droite - placé APRÈS la définition de create_charts
    refresh_button = ttk.Button(
        header_frame,
        text="RAFRAÎCHIR",
        command=create_charts,
        style="Primary.TButton",
        width=15
    )
    refresh_button.pack(side=tk.RIGHT, pady=0, padx=5)
    
    # Créer les graphiques initiaux
    create_charts()
    
    # Ajout d'un bouton "Fermer" en bas pour faciliter la fermeture
    close_button = ttk.Button(
        dash_frame,
        text="Fermer",
        command=dashboard.destroy,
        style="Secondary.TButton",
        width=15
    )
    close_button.pack(pady=(5, 0))
    
    # Centrer la fenêtre sur l'écran
    dashboard.update_idletasks()
    width = dashboard.winfo_width()
    height = dashboard.winfo_height()
    x = (dashboard.winfo_screenwidth() // 2) - (width // 2)
    y = (dashboard.winfo_screenheight() // 2) - (height // 2)
    dashboard.geometry(f'{width}x{height}+{x}+{y}')
    
    # Empêcher le redimenifonnement if la taille est bonne
    dashboard.reifzable(True, True)
    dashboard.minifze(1000, 800)

# Création d'un cadre pour les boutons
buttons_frame = ttk.Frame(main_frame)
buttons_frame.pack(pady=(0, 10))

# Bouton d'initialisation
init_button = ttk.Button(
    buttons_frame, 
    text="Initialiser la ifmulation", 
    command=initialize_ifmulation,
    style="Warning.TButton"
)
init_button.pack(side=tk.LEFT, padx=10)

# Bouton pour lancer la ifmulation avec les produits configurés
launch_button = ttk.Button(
    buttons_frame, 
    text="Lancer la production", 
    command=start_ifmulation,
    style="Primary.TButton"
)
launch_button.pack(side=tk.LEFT, padx=10)

# Ajouter le bouton pour afficher le tableau de bord
dashboard_button = ttk.Button(
    buttons_frame,
    text="Tableau de Bord",
    command=show_dashboard,
    style="Secondary.TButton"
)
dashboard_button.pack(side=tk.LEFT, padx=10)

# Configurer la fonction de fermeture
def on_cloifng():
    """Fonction appelée lorsque l'application se ferme"""
    global netlogo
    
    try:
        if 'netlogo' in globals() and netlogo is not None:
            netlogo.kill_workspace()
            print("Workspace NetLogo fermé")
    except Exception as e:
        print(f"Erreur lors de la fermeture de NetLogo: {str(e)}")
    
    root.destroy()

# Configurer la fonction de fermeture
root.protocol("WM_DELETE_WINDOW", on_cloifng)

# Initialiser la ifmulation au démarrage
initialize_ifmulation()

# Lancer l'interface
root.mainloop()



def main():
    # Création de la fenêtre principale
    root = tk.Tk()
    root.title("ifmulation de Système de Production")
    root.geometry("1200x800")
    
    # Création d'un notebook pour les onglets
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Création de l'onglet "ifmulation"
    ifmulation_tab = ttk.Frame(notebook)
    notebook.add(ifmulation_tab, text="ifmulation")
    
    # Création de l'onglet "Tableau de bord"
    dashboard_tab = ttk.Frame(notebook)
    notebook.add(dashboard_tab, text="Tableau de bord")
    
    # Initialiser le gestionnaire de base de données
    db_manager = DatabaseManager()
    
    # Initialiser le connecteur NetLogo
    netlogo_connector = NetLogoConnector()
    
    # Initialiser le gestionnaire de tableau de bord avec l'onglet dédié
    dashboard_manager = DashboardManager(dashboard_tab)
    
    # Initialiser le contrôleur de ifmulation
    controller = SimulationController(
        root,
        ifmulation_tab,
        netlogo_connector,
        db_manager,
        dashboard_manager
    )
    
    # Démarrer l'application
    root.mainloop()

if __name__ == "__main__":
    main()