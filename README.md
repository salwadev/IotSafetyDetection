# Rapport Détaillé - Système de Détection d'EPI

## 1. Introduction
Ce projet implémente un système de détection d'Équipements de Protection Individuelle (EPI) en temps réel pour la sécurité sur les chantiers de construction.

## 2. Architecture du Système

### 2.1 Backend (Flask)
- **API REST** pour la communication avec le frontend
- **WebSocket** pour les mises à jour en temps réel
- **SQLite** pour le stockage des données
- **MQTT** pour la communication IoT

### 2.2 Frontend (React)
- Interface utilisateur moderne et responsive
- Visualisation des données en temps réel
- Graphiques et tableaux d'historique
- Système d'alertes visuelles et sonores

## 3. Fonctionnalités Principales

### 3.1 Détection d'EPI
- Détection des personnes
- Identification des casques (hardhat)
- Identification des gilets de sécurité (safety vest)
- Classification en temps réel :
  * Personne sécurisée (casque OU gilet)
  * Personne non sécurisée (ni casque ni gilet)

### 3.2 Modes de Détection
1. **Mode Image**
   - Upload d'images
   - Analyse statique
   - Sauvegarde des résultats

2. **Mode Vidéo**
   - Détection en temps réel via webcam
   - Streaming vidéo
   - Analyse continue

### 3.3 Système d'Alertes
- Alertes visuelles (bordures rouges)
- Alertes sonores (fichier audio)
- Déclenchement automatique lors de détection non sécurisée
- Durée d'alerte : 20 secondes

## 4. Stockage et Communication

### 4.1 Base de Données (SQLite)
- Stockage des détections
- Historique des événements
- Statistiques de sécurité

### 4.2 MQTT
- Publication des détections
- Format JSON
- Intervalle : 15 secondes

## 5. Interface Utilisateur

### 5.1 Panneau de Contrôle
- Bouton de détection par image
- Bouton de détection par caméra
- Indicateurs d'état

### 5.2 Zone de Détection
- Affichage des images/vidéo
- Annotations en temps réel
- Indicateurs de sécurité

### 5.3 Statistiques
- Nombre total de personnes
- Personnes sécurisées
- Personnes non sécurisées
- Mise à jour en temps réel

### 5.4 Historique
- Graphique d'évolution
- Tableau des détections
- Pagination (5 entrées par page)
- Miniatures des images

## 6. Installation et Configuration

### 6.1 Prérequis
- Python 3.8+
- Node.js 14+
- Webcam fonctionnelle
- Modèle YOLOv8 entraîné

### 6.2 Installation
1. Cloner le repository
2. Installer les dépendances Python
3. Installer les dépendances Node.js
4. Configurer les variables d'environnement

### 6.3 Configuration
- Configuration MQTT
- Paramètres de la base de données
- Chemins des fichiers média
- Paramètres de détection

## 7. Utilisation

### 7.1 Démarrage
1. Lancer le backend Flask
2. Lancer le frontend React
3. Accéder via navigateur

### 7.2 Utilisation Quotidienne
1. Choisir le mode de détection
2. Surveiller les alertes
3. Consulter les statistiques
4. Analyser l'historique

## 8. Maintenance

### 8.1 Sauvegarde
- Base de données
- Images détectées
- Logs système

### 8.2 Mises à jour
- Modèle YOLOv8
- Dépendances
- Configuration

## 9. Sécurité
- Validation des entrées
- Gestion des erreurs
- Protection des données
- Logs d'activité

## 10. Performance
- Optimisation des images
- Mise en cache
- Gestion de la mémoire
- Intervalle de sauvegarde
