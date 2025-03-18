"""
Fonctions d'aide pour interagir avec NetLogo de manière robuste
"""
from utils import to_python_list, safe_int, safe_float, safe_str

def get_machine_properties(netlogo, machine_id):
    """
    Récupère les propriétés d'une machine de manière robuste
    
    Args:
        netlogo: L'instance NetLogoLink
        machine_id: L'ID de la machine
        
    Returns:
        Un dictionnaire des propriétés de la machine
    """
    machine_data = {}
    
    # Vérifier que la tortue existe
    exists_cmd = f"is-turtle? turtle {machine_id}"
    try:
        exists = netlogo.report(exists_cmd)
        if not exists:
            return {"name": f"Machine{machine_id}", "state": "Idle"}
    except Exception:
        return {"name": f"Machine{machine_id}", "state": "Idle"}
    
    # Récupérer le nom
    try:
        machine_data["name"] = safe_str(netlogo.report(f"[machine.name] of turtle {machine_id}"))
    except Exception:
        machine_data["name"] = f"Machine{machine_id}"
    
    # Récupérer l'état
    try:
        state = safe_str(netlogo.report(f"[machine.state] of turtle {machine_id}"))
        # Adapter l'état pour la base de données
        if state == "Machine.Processing":
            machine_data["state"] = "Processing"
        elif state in ["Idle", "Down"]:
            machine_data["state"] = state
        else:
            machine_data["state"] = "Idle"
    except Exception:
        machine_data["state"] = "Idle"
    
    # Récupérer le temps restant
    try:
        machine_data["remaining.time"] = safe_float(netlogo.report(f"[next.completion] of turtle {machine_id}"))
    except Exception:
        machine_data["remaining.time"] = 0.0
    
    # Récupérer les opérations et temps comme chaînes simples
    try:
        machine_data["operations"] = str(netlogo.report(f"[machine.operations.type] of turtle {machine_id}"))
    except Exception:
        machine_data["operations"] = "[]"
    
    try:
        machine_data["operation.times"] = str(netlogo.report(f"[machine.operations.time] of turtle {machine_id}"))
    except Exception:
        machine_data["operation.times"] = "[]"
    
    # Récupérer les coordonnées
    try:
        machine_data["xcor"] = safe_float(netlogo.report(f"[xcor] of turtle {machine_id}"))
        machine_data["ycor"] = safe_float(netlogo.report(f"[ycor] of turtle {machine_id}"))
        machine_data["heading"] = safe_float(netlogo.report(f"[heading] of turtle {machine_id}"))
    except Exception:
        machine_data["xcor"] = 0.0
        machine_data["ycor"] = 0.0
        machine_data["heading"] = 0.0
    
    return machine_data

def get_product_properties(netlogo, product_id):
    """
    Récupère les propriétés d'un produit de manière robuste
    
    Args:
        netlogo: L'instance NetLogoLink
        product_id: L'ID du produit
        
    Returns:
        Un dictionnaire des propriétés du produit
    """
    product_data = {"who": str(product_id)}
    
    # Vérifier que le produit existe
    exists_cmd = f"is-turtle? turtle {product_id}"
    try:
        exists = netlogo.report(exists_cmd)
        if not exists:
            return product_data
    except Exception:
        return product_data
    
    # Récupérer l'état et le type
    try:
        product_data["state"] = safe_str(netlogo.report(f"[product.state] of turtle {product_id}"))
    except Exception:
        product_data["state"] = "Waiting"
    
    try:
        product_data["type"] = safe_str(netlogo.report(f"[ProductType] of turtle {product_id}"))
    except Exception:
        product_data["type"] = "Unknown"
    
    # Récupérer les informations d'opération
    try:
        product_data["next.operation"] = safe_str(netlogo.report(f"[next.product.operation] of turtle {product_id}"))
    except Exception:
        product_data["next.operation"] = ""
    
    try:
        product_data["operations"] = str(netlogo.report(f"[ProductOperations] of turtle {product_id}"))
    except Exception:
        product_data["operations"] = "[]"
    
    try:
        product_data["sequence.order"] = safe_int(netlogo.report(f"[currentsequenceorder] of turtle {product_id}"))
    except Exception:
        product_data["sequence.order"] = 0
    
    # Utiliser des reporters NetLogo sécurisés pour les listes
    try:
        real_start_cmd = f"""
        let tmp_list [ProductRealStart] of turtle {product_id}
        ifelse empty? tmp_list [0][first tmp_list]
        """
        product_data["start.time"] = safe_float(netlogo.report(real_start_cmd))
    except Exception:
        product_data["start.time"] = 0.0
    
    try:
        real_completion_cmd = f"""
        let tmp_list [ProductRealCompletion] of turtle {product_id}
        ifelse empty? tmp_list [0][first tmp_list]
        """
        product_data["end.time"] = safe_float(netlogo.report(real_completion_cmd))
    except Exception:
        product_data["end.time"] = 0.0
    
    # Récupérer les informations de nœud
    try:
        last_node_cmd = f"""
        let n [Last.Node] of turtle {product_id}
        ifelse is-turtle? n [[who] of n][0]
        """
        product_data["last.node"] = safe_int(netlogo.report(last_node_cmd))
    except Exception:
        product_data["last.node"] = 0
    
    try:
        next_node_cmd = f"""
        let n [Next.Node] of turtle {product_id}
        ifelse is-turtle? n [[who] of n][0]
        """
        product_data["next.node"] = safe_int(netlogo.report(next_node_cmd))
    except Exception:
        product_data["next.node"] = 0
    
    # Autres propriétés
    try:
        product_data["workstation"] = safe_str(netlogo.report(f"[Heading.Workstation] of turtle {product_id}"))
    except Exception:
        product_data["workstation"] = "Unknown"
    
    try:
        product_data["next.status"] = safe_int(netlogo.report(f"[Next.Product.status] of turtle {product_id}"))
    except Exception:
        product_data["next.status"] = 0
    
    try:
        product_data["next.completion.time"] = safe_float(netlogo.report(f"[Next.Product.Completion.Time] of turtle {product_id}"))
    except Exception:
        product_data["next.completion.time"] = 0.0
    
    try:
        product_data["xcor"] = safe_float(netlogo.report(f"[xcor] of turtle {product_id}"))
        product_data["ycor"] = safe_float(netlogo.report(f"[ycor] of turtle {product_id}"))
        product_data["heading"] = safe_float(netlogo.report(f"[heading] of turtle {product_id}"))
    except Exception:
        product_data["xcor"] = 0.0
        product_data["ycor"] = 0.0
        product_data["heading"] = 0.0
    
    return product_data

def get_system_stats(netlogo):
    """
    Récupère les statistiques du système
    
    Args:
        netlogo: L'instance NetLogoLink
        
    Returns:
        Un dictionnaire des statistiques du système
    """
    stats = {
        "waiting_products": 0,
        "in_progress_products": 0,
        "completed_products": 0,
        "idle_machines": 0,
        "processing_machines": 0,
        "down_machines": 0,
    }
    
    try:
        stats["waiting_products"] = safe_int(netlogo.report('count turtles with [breed = products and product.state = "Waiting"]'))
    except Exception:
        pass
        
    try:
        stats["in_progress_products"] = safe_int(netlogo.report('count turtles with [breed = products and product.state = "Processing.Product"]'))
    except Exception:
        pass
        
    try:
        stats["completed_products"] = safe_int(netlogo.report('count turtles with [breed = products and product.state = "Completed"]'))
    except Exception:
        pass
        
    try:
        stats["idle_machines"] = safe_int(netlogo.report('count turtles with [breed = machines and machine.state = "Idle"]'))
    except Exception:
        pass
        
    try:
        stats["processing_machines"] = safe_int(netlogo.report('count turtles with [breed = machines and machine.state = "Machine.Processing"]'))
    except Exception:
        pass
        
    try:
        stats["down_machines"] = safe_int(netlogo.report('count turtles with [breed = machines and machine.state = "Down"]'))
    except Exception:
        pass
    
    return stats
