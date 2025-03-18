"""
Utilitaires pour la gestion des données et conversions de types
"""
import numpy as np

def safe_int(value, default=0):
    """Convertit une valeur en entier de manière sécurisée"""
    if value is None:
        return default
    try:
        if isinstance(value, str):
            # Si c'est un nombre décimal comme '1.5', convertir d'abord en float
            if '.' in value:
                return int(float(value))
            return int(value)
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float(value, default=0.0):
    """Convertit une valeur en float de manière sécurisée"""
    if value is None:
        return default
    try:
        if isinstance(value, str):
            return float(value)
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_str(value, default=""):
    """Convertit une valeur en chaîne de caractères de manière sécurisée"""
    if value is None:
        return default
    try:
        return str(value)
    except Exception:
        return default

def ensure_list(value, default=None):
    """S'assure qu'une valeur est une liste"""
    if default is None:
        default = []
    
    if value is None:
        return default
    
    if isinstance(value, list):
        return value
    
    # Si c'est déjà une collection itérable mais pas une chaîne
    if hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
        return list(value)
    
    # Sinon, retourner la valeur dans une liste
    return [value]

def parse_netlogo_result(result, expected_type=None):
    """
    Parse et valide le résultat d'un appel à NetLogo
    
    Args:
        result: La valeur retournée par NetLogo
        expected_type: Le type attendu (list, int, float, str, etc.)
        
    Returns:
        La valeur convertie au type attendu ou None si impossible
    """
    if result is None:
        return None
    
    if expected_type is None:
        return result
    
    try:
        if expected_type == list:
            return ensure_list(result)
        elif expected_type == int:
            return safe_int(result)
        elif expected_type == float:
            return safe_float(result)
        elif expected_type == str:
            return safe_str(result)
        else:
            # Pour d'autres types, essayer la conversion directe
            return expected_type(result)
    except Exception as e:
        print(f"Erreur de conversion vers {expected_type.__name__}: {str(e)}")
        return None

def to_python_list(value, default=None):
    """
    Convertit différents types de collections (y compris numpy.ndarray) en liste Python standard
    
    Args:
        value: La valeur à convertir
        default: La valeur par défaut à retourner si la conversion échoue
        
    Returns:
        Une liste Python standard
    """
    if default is None:
        default = []
        
    if value is None:
        return default
    
    # Si c'est déjà une liste Python
    if isinstance(value, list):
        return value
    
    # Si c'est un tableau NumPy
    if isinstance(value, np.ndarray):
        return value.tolist()
    
    # Si c'est un autre type itérable (mais pas une chaîne)
    if hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
        return list(value)
    
    # Sinon, retourner une liste avec cet élément unique
    return [value]

def safe_netlogo_node(node_value, default=0):
    """
    Extrait l'ID numérique d'un nœud NetLogo ou retourne une valeur par défaut
    
    Args:
        node_value: La valeur du nœud NetLogo (peut être un str comme "node 93")
        default: La valeur par défaut si l'ID ne peut pas être extrait
    
    Returns:
        L'ID numérique du nœud
    """
    if node_value is None:
        return default
    
    try:
        # Si c'est une chaîne comme "node 93"
        if isinstance(node_value, str) and "node" in node_value.lower():
            # Tenter d'extraire le numéro
            parts = node_value.split()
            for part in parts:
                try:
                    return int(part)
                except ValueError:
                    continue
            return default
        
        # Sinon, tenter de convertir directement
        return int(float(node_value))
    except (ValueError, TypeError, AttributeError):
        return default

def safe_netlogo_list_item(list_or_str, index=0, default=0):
    """
    Récupère un élément d'une liste NetLogo de manière sécurisée
    
    Args:
        list_or_str: Une liste Python ou une chaîne représentant une liste NetLogo
        index: L'indice de l'élément à récupérer
        default: La valeur par défaut si l'élément n'existe pas
        
    Returns:
        L'élément à l'indice spécifié ou la valeur par défaut
    """
    if list_or_str is None:
        return default
    
    # Si c'est une chaîne, essayer de l'évaluer comme une liste
    if isinstance(list_or_str, str):
        try:
            import ast
            list_or_str = ast.literal_eval(list_or_str)
        except (ValueError, SyntaxError):
            # Si l'évaluation échoue, retourner la valeur par défaut
            return default
    
    # Maintenant tenter d'accéder à l'élément de la liste
    try:
        if isinstance(list_or_str, (list, tuple)) and 0 <= index < len(list_or_str):
            return list_or_str[index]
    except (IndexError, TypeError):
        pass
    
    return default

def is_empty_netlogo_list(netlogo_obj, default=True):
    """
    Détermine si un objet NetLogo représente une liste vide
    
    Args:
        netlogo_obj: L'objet NetLogo à vérifier
        default: La valeur par défaut à retourner en cas d'erreur
        
    Returns:
        True si la liste est vide, False sinon, ou la valeur par défaut en cas d'erreur
    """
    if netlogo_obj is None:
        return default
    
    # Si c'est une chaîne représentant une liste
    if isinstance(netlogo_obj, str):
        return netlogo_obj.strip() in ["[]", "", "None"]
    
    # Si c'est déjà une liste Python
    if isinstance(netlogo_obj, (list, tuple)):
        return len(netlogo_obj) == 0
    
    # Par défaut, considérer comme non-vide
    return False

def safe_netlogo_state_conversion(state):
    """
    Convertit un état NetLogo en un état compatible avec la base de données
    
    Args:
        state: L'état NetLogo (chaîne)
        
    Returns:
        L'état compatible avec la base de données
    """
    if state is None:
        return "Idle"
    
    state_str = str(state).strip()
    
    # Mappings d'états
    state_mappings = {
        "idle": "Idle",
        "machine.processing": "Processing",
        "down": "Down",
        "waiting": "Waiting",
        "processing.product": "In Progress",
        "completed": "Completed",
        "movement": "Movement"
    }
    
    # Rechercher une correspondance insensible à la casse
    for netlogo_state, db_state in state_mappings.items():
        if netlogo_state.lower() == state_str.lower():
            return db_state
    
    # État par défaut
    return "Idle"

def build_safe_netlogo_command(command_template, params):
    """
    Construit une commande NetLogo sécurisée en échappant correctement les paramètres
    
    Args:
        command_template: Modèle de commande NetLogo avec des placeholders {}
        params: Dictionnaire de paramètres à insérer dans le template
    
    Returns:
        La commande NetLogo prête à être exécutée
    """
    # Échapper les chaînes pour NetLogo
    escaped_params = {}
    for key, value in params.items():
        if isinstance(value, str):
            # Doubler les guillemets pour l'échappement NetLogo
            escaped_params[key] = value.replace('"', '""')
        else:
            escaped_params[key] = value
    
    # Construire la commande finale
    return command_template.format(**escaped_params)

def execute_safe_netlogo_reporter(netlogo, reporter_template, params=None, default=None):
    """
    Exécute un reporter NetLogo avec gestion d'erreur
    
    Args:
        netlogo: L'instance NetLogoLink
        reporter_template: Modèle de reporter NetLogo
        params: Dictionnaire de paramètres à insérer (facultatif)
        default: Valeur à retourner en cas d'erreur
        
    Returns:
        Le résultat du reporter ou la valeur par défaut en cas d'erreur
    """
    try:
        if params:
            reporter = build_safe_netlogo_command(reporter_template, params)
        else:
            reporter = reporter_template
            
        result = netlogo.report(reporter)
        return result
    except Exception as e:
        print(f"Erreur dans l'exécution du reporter NetLogo: {e}")
        return default

def convert_java_to_python(value):
    """
    Convertit explicitement les types Java en types Python natifs.
    
    Args:
        value: La valeur Java/Python à convertir
        
    Returns:
        La valeur convertie en type Python natif
    """
    # Pour les chaînes Java, convertir en chaîne Python
    if str(type(value)).find('java.lang.String') != -1:
        return str(value)
    
    # Pour les nombres Java, convertir en nombre Python
    if str(type(value)).find('java.lang.Double') != -1 or str(type(value)).find('java.lang.Float') != -1:
        return float(value)
    
    if str(type(value)).find('java.lang.Integer') != -1 or str(type(value)).find('java.lang.Long') != -1:
        return int(value)
    
    # Pour les booléens Java, convertir en booléen Python
    if str(type(value)).find('java.lang.Boolean') != -1:
        return bool(value)
    
    # Pour les listes Java, convertir en liste Python
    if str(type(value)).find('java.util.ArrayList') != -1 or str(type(value)).find('java.util.List') != -1:
        return [convert_java_to_python(item) for item in value]
    
    # Pour les tableaux Java, convertir en liste Python
    if str(type(value)).startswith('['):  # Les tableaux Java ont un type qui commence par '['
        return [convert_java_to_python(item) for item in value]
    
    # Pour les autres types, renvoyer la valeur telle quelle
    return value

def normalize_tuple_length(data_tuple, expected_length, default_values=None):
    """
    Normalise la longueur d'un tuple pour qu'il corresponde à la longueur attendue
    
    Args:
        data_tuple: Le tuple à normaliser
        expected_length: La longueur attendue
        default_values: Liste des valeurs par défaut à utiliser si nécessaire
        
    Returns:
        Un nouveau tuple de la longueur attendue
    """
    if default_values is None:
        default_values = [0] * expected_length
    
    # Convertir en liste pour pouvoir la modifier
    result = list(data_tuple)
    
    # Si le tuple est trop court, ajouter des valeurs par défaut
    while len(result) < expected_length:
        position = len(result)
        if position < len(default_values):
            result.append(default_values[position])
        else:
            result.append(0)
    
    # Si le tuple est trop long, le tronquer
    if len(result) > expected_length:
        result = result[:expected_length]
    
    return tuple(result)
