# Tableau de Bord de Simulation de Production

## Description
Ce projet est une interface de tableau de bord qui se connecte à une simulation NetLogo pour visualiser et analyser des données de production en temps réel. Il permet de surveiller l'état des machines, le flux de produits et de calculer des métriques d'efficacité pour optimiser les processus de production.

## Fonctionnalités principales
- Connexion en temps réel à une simulation NetLogo
- Visualisation dynamique des états des machines et des produits
- Calcul et affichage d'indicateurs de performance (KPI)
- Graphiques d'efficacité et de temps de cycle
- Mise à jour automatique des données

## Prérequis
- Python 3.7 ou supérieur
- Java Development Kit (JDK) 8 ou supérieur (nécessaire pour NetLogo)
- NetLogo 6.x
- Bibliothèques Python requises (voir la section Installation)

## Installation

### 1. Installer le JDK
Assurez-vous d'avoir un JDK installé sur votre système :
- Téléchargez et installez le JDK depuis [le site officiel d'Oracle](https://www.oracle.com/java/technologies/javase-jdk16-downloads.html) ou utilisez OpenJDK
- Vérifiez l'installation en exécutant `java -version` dans un terminal

### 2. Cloner le dépôt
```bash
git clone https://github.com/Antbasso/tableau-bord-netlogo.git
cd tableau-bord-netlogo
```

### 3. Créer un environnement virtuel (recommandé)
```bash
python -m venv venv
```

Activation de l'environnement virtuel:
- Windows:
  ```bash
  venv\Scripts\activate
  ```
- macOS/Linux:
  ```bash
  source venv/bin/activate
  ```

### 4. Installer les dépendances
```bash
pip install -r requirements.txt
```

## Configuration

### Configuration de l'application
1. Modifiez le fichier `config.ini` pour spécifier:
   - Le chemin vers l'exécutable NetLogo
   - Le chemin vers votre modèle
   - Les paramètres de simulation par défaut

### Variables d'environnement Java
Si NetLogo ne trouve pas automatiquement votre JDK, vous devrez peut-être configurer la variable d'environnement `JAVA_HOME`:

- Windows:
  ```
  set JAVA_HOME=C:\chemin\vers\votre\jdk
  ```
- macOS/Linux:
  ```
  export JAVA_HOME=/chemin/vers/votre/jdk
  ```

## Utilisation

### Lancement de l'application
```bash
python main.py
```

### Interface utilisateur
L'interface se compose de:
- Un panneau de contrôle pour démarrer/arrêter la simulation
- Un tableau de bord avec des statistiques en temps réel
- Des graphiques montrant:
  - Le taux d'efficacité de la production
  - Le temps de cycle des machines
  - La distribution des états des machines

### Fonctions principales
- **Démarrer la simulation**: Lance la simulation NetLogo et commence la collecte de données
- **Pause**: Suspend la simulation temporairement
- **Modifier les paramètres**: Ajuste les paramètres de simulation en temps réel
- **Exporter les données**: Sauvegarde les données collectées au format CSV

## Structure du projet
```
projet/
├── main.py                  # Point d'entrée principal
├── main_controller.py       # Contrôleur principal de l'application
├── netlogo_connector.py     # Interface avec NetLogo
├── dashboard_manager.py     # Gestion de l'affichage du tableau de bord
├── config.ini               # Fichier de configuration
├── models/                  # Modèles NetLogo
├── utils/                   # Utilitaires divers
└── ui/                      # Composants de l'interface utilisateur
```

## Métriques calculées
- **Taux d'efficacité**: Pourcentage de produits complétés par rapport au total
- **Temps de cycle**: Ratio du temps passé par les machines en état "Processing" par rapport au temps total
- **États des machines**: Distribution des différents états des machines (Idle, Processing, Setup, etc.)

## Dépannage
- **Le tableau de bord ne s'affiche pas**: Vérifiez que les bibliothèques graphiques sont correctement installées
- **Erreur de connexion à NetLogo**: Assurez-vous que le chemin vers l'exécutable NetLogo est correctement configuré
- **Les graphiques ne se mettent pas à jour**: Vérifiez les logs pour des erreurs potentielles liées au calcul des métriques

## Licence
Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## Contributeurs
- [Votre nom]
- [Contributeur 2]

## Contact
Pour toute question ou suggestion, veuillez contacter [votre-email@exemple.com].
