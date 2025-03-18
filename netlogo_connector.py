import pynetlogo
import os
from utils import safe_float, safe_int
from netlogo_utils import (
    safe_netlogo_reporter, safe_netlogo_command,
    get_machine_state, get_product_state, get_system_state
)

class NetLogoConnector:
    """
    Classe qui fournit une interface pour interagir avec NetLogo.
    """
    def __init__(self):
        """Initialisation du connecteur NetLogo"""
        self.netlogo = None
        self.model_path = None
        self.initialized = False
        self.jvm_path = r"jdk\openjdk-23.0.2_windows-x64_bin\jdk-23.0.2\bin\server\jvm.dll"

    def initialize(self, model_path="Alpha.nlogo"):
        """
        Initialise la connexion avec NetLogo
        
        Args:
            model_path (str): Chemin vers le fichier modèle NetLogo
        
        Returns:
            bool: True si l'initialisation est réussie, False sinon
        """
        try:
            # Fermer l'instance précédente si elle existe
            if self.netlogo is not None:
                try:
                    self.netlogo.kill_workspace()
                    print("Workspace précédent fermé")
                except:
                    pass
            
            # Créer une nouvelle instance
            self.netlogo = pynetlogo.NetLogoLink(gui=True, jvm_path=self.jvm_path)
            print("NetLogo initialisé avec succès")
            
            # Définir et charger le modèle
            self.model_path = os.path.abspath(model_path)
            print(f"Chargement du modèle depuis: {self.model_path}")
            self.netlogo.load_model(self.model_path)
            print("Modèle chargé avec succès")
            
            # Initialiser le modèle
            self.netlogo.command("setup")
            print("Modèle initialisé avec succès")
            
            self.initialized = True
            return True
        except Exception as e:
            print(f"Erreur lors de l'initialisation de NetLogo: {str(e)}")
            self.initialized = False
            return False

    def get_products_data(self):
        """
        Récupère les données des produits depuis NetLogo
        
        Returns:
            list: Liste des données des produits
        """
        if not self.initialized or self.netlogo is None:
            return []
        
        try:
            # Récupérer le nombre de produits
            count_products = safe_int(safe_netlogo_reporter(self.netlogo, "count products", 0), 0)
            
            products_data = []
            if count_products > 0:
                # Récupérer les IDs des produits
                for potential_id in range(200, 300):  # Plage typique pour les IDs de produits dans NetLogo
                    is_product = safe_netlogo_reporter(
                        self.netlogo, 
                        f"is-turtle? turtle {potential_id} and [breed] of turtle {potential_id} = products", 
                        False,
                        False  # Ne pas logger les erreurs pour chaque tentative
                    )
                    
                    if is_product:
                        # Récupérer les données du produit
                        product_data = get_product_state(self.netlogo, potential_id)
                        if product_data:
                            products_data.append(product_data)
                        
                        # Si on a trouvé tous les produits, on arrête
                        if len(products_data) >= count_products:
                            break
            
            return products_data
        except Exception as e:
            print(f"Erreur lors de la récupération des données des produits: {str(e)}")
            return []

    def get_machines_data(self):
        """
        Récupère les données des machines depuis NetLogo
        
        Returns:
            list: Liste des données des machines
        """
        if not self.initialized or self.netlogo is None:
            return []
        
        try:
            # Les IDs connus des machines pour le modèle Alpha
            machine_ids = [186, 187, 188, 189, 190, 191, 192]
            
            machines_data = []
            for machine_id in machine_ids:
                try:
                    # Récupérer les données de la machine
                    machine_data = get_machine_state(self.netlogo, machine_id)
                    if machine_data:
                        machines_data.append(machine_data)
                except Exception as e:
                    print(f"Erreur lors de la récupération des données de la machine {machine_id}: {e}")
            
            return machines_data
        except Exception as e:
            print(f"Erreur lors de la récupération des données des machines: {str(e)}")
            return []

    def execute_command(self, command):
        """
        Exécute une commande NetLogo
        
        Args:
            command (str): Commande NetLogo à exécuter
            
        Returns:
            bool: True si la commande est exécutée avec succès, False sinon
        """
        if not self.initialized or self.netlogo is None:
            return False
        
        return safe_netlogo_command(self.netlogo, command)

    def get_reporter_value(self, reporter, default=None):
        """
        Récupère la valeur d'un reporter NetLogo
        
        Args:
            reporter (str): Reporter NetLogo à évaluer
            default: Valeur par défaut à retourner en cas d'erreur
            
        Returns:
            La valeur du reporter ou la valeur par défaut si une erreur survient
        """
        if not self.initialized or self.netlogo is None:
            return default
        
        return safe_netlogo_reporter(self.netlogo, reporter, default)

    def close(self):
        """
        Ferme la connexion avec NetLogo
        """
        if self.netlogo is not None:
            try:
                self.netlogo.kill_workspace()
                print("NetLogo fermé")
            except Exception as e:
                print(f"Erreur lors de la fermeture de NetLogo: {str(e)}")
            
            self.netlogo = None
            self.initialized = False