class DataValidator:
    """
    Classe utilitaire pour valider la cohérence des données
    """
    @staticmethod
    def validate_product_counts(detected_products, displayed_products):
        """
        Vérifie la cohérence entre les produits détectés et affichés
        
        Args:
            detected_products (dict): Données des produits détectés
            displayed_products (int): Nombre de produits affichés
            
        Returns:
            tuple: (is_valid, error_message)
        """
        detected_count = len(detected_products)
        
        if detected_count != displayed_products:
            return (False, f"Incohérence dans le nombre de produits: {detected_count} détectés vs {displayed_products} affichés")
        
        return (True, "Données cohérentes")
    
    @staticmethod
    def count_products_by_type(products_data):
        """
        Compte les produits par type de façon sécurisée
        
        Args:
            products_data (dict): Données des produits
            
        Returns:
            dict: Comptage par type de produit
        """
        type_counts = {}
        
        for product_id, product_info in products_data.items():
            product_type = product_info.get('type', 'Unknown')
            if product_type not in type_counts:
                type_counts[product_type] = 0
            type_counts[product_type] += 1
        
        return type_counts
