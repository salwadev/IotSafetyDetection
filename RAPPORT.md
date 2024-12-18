# Rapport Détaillé - Système de Détection EPI avec ESP32 et MQTT

## 1. Vue d'ensemble du projet

### 1.1 Objectif
Développement d'un système de surveillance en temps réel des équipements de protection individuelle (EPI) utilisant :
- Détection vidéo avec YOLOv8
- Communication MQTT
- Visualisation en temps réel
- Alertes visuelles sur ESP32

### 1.2 Architecture globale

## 2. Composants du système

### 2.1 Backend (Flask)
- **Fichier principal**: `backend/app.py`
- **Service MQTT**: `backend/services/mqtt_service.py`
- **Fonctionnalités**:
  * Détection en temps réel avec YOLOv8
  * API REST pour les requêtes frontend
  * WebSocket pour les mises à jour en direct
  * Publication MQTT des détections
  * Stockage dans SQLite
  * Gestion des images de détection

### 2.2 Frontend (React)
- **Fichiers principaux**:
  * `frontend/src/App.jsx`
  * `frontend/src/App.css`
- **Fonctionnalités**:
  * Interface utilisateur moderne
  * Affichage vidéo en temps réel
  * Graphiques statistiques
  * Tableau historique paginé
  * Alertes sonores et visuelles
  * Responsive design

### 2.3 ESP32
- **Fichiers**:
  * `main.py` : Programme principal
  * `boot.py` : Configuration initiale
- **Fonctionnalités**:
  * Connexion WiFi automatique
  * Client MQTT
  * Gestion des LEDs d'alerte
  * Système de debug

## 3. Détails techniques

### 3.1 Configuration MQTT
python
MQTT_CONFIG = {
'broker_host': "bee321a450aa496ca69c29cfcad112a5.s1.eu.hivemq.cloud",
'broker_port': 8883,
'username': "salwaroot",
'password': "Emploi@2024",
'topic': "ppe/detections"
}


### 3.2 Structure de la base de données
sql
CREATE TABLE detections (
id INTEGER PRIMARY KEY AUTOINCREMENT,
timestamp TEXT,
total_persons INTEGER,
secured_persons INTEGER,
partially_secured INTEGER,
unsecured INTEGER,
image_path TEXT
);

### 3.3 Format des messages MQTT
json
{
"timestamp": "2024-03-17T21:18:04",
"total_persons": 3,
"secured_persons": 2,
"partially_secured": 0,
"unsecured": 1,
"is_secure": false,
"detections": [...]
}


## 4. Fonctionnalités détaillées

### 4.1 Détection d'EPI
- **Classes détectées**:
  * Personnes
  * Casques de sécurité
  * Gilets réfléchissants
- **États possibles**:
  * Sécurisé (casque ET gilet)
  * Partiellement sécurisé (casque OU gilet)
  * Non sécurisé (ni casque ni gilet)

### 4.2 Système d'alertes
- **Visuelles**:
  * LED verte : Situation sécurisée
  * LED rouge : Situation non sécurisée
- **Sonores**:
  * Alarme de 20 secondes lors d'une détection non sécurisée
  * Réinitialisation automatique

### 4.3 Historique et statistiques
- Sauvegarde toutes les 15 secondes
- Pagination : 5 entrées par page
- Graphique d'évolution
- Miniatures des détections

## 5. Configuration matérielle

### 5.1 ESP32
- **Pins utilisés**:
  * GPIO2 : LED Rouge
  * GPIO4 : LED Verte
- **Composants**:
  * 2 LEDs (rouge et verte)
  * 2 résistances 220Ω

### 5.2 Caméra
- Résolution : 640x480
- FPS : 30
- Format : MJPG

## 6. Sécurité

### 6.1 Communication
- MQTT sécurisé (TLS)
- Authentification requise
- Certificats SSL

### 6.2 Données
- Validation des entrées
- Sanitization des chemins de fichiers
- Protection contre les injections SQL

## 7. Performance

### 7.1 Optimisations
- Compression des images
- Mise en cache
- Intervalle de sauvegarde optimisé
- WebSocket pour les mises à jour en direct

### 7.2 Limitations
- Une seule caméra à la fois
- Délai de détection : ~100ms
- Taille maximale des images : 640x480

## 8. Installation

### 8.1 Prérequis
Backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
Frontend
cd frontend
npm install
ESP32
Flasher MicroPython
Uploader main.py

### 8.2 Configuration requise
- Python 3.8+
- Node.js 14+
- ESP32 avec MicroPython
- Modèle YOLOv8 entraîné

## 9. Maintenance

### 9.1 Logs
- Backend : Logs détaillés des détections
- ESP32 : Debug série
- Frontend : Console browser

### 9.2 Dépannage
- Vérification connexion WiFi
- Test connexion MQTT
- Diagnostic LEDs
- Monitoring mémoire

## 10. Évolutions futures

### 10.1 Améliorations possibles
- Interface d'administration
- Support multi-caméras
- Notifications push
- API REST complète
- Dashboard avancé

### 10.2 Limitations actuelles
- Pas de gestion utilisateurs
- Pas de backup automatique
- Reconnexion manuelle
- Alertes basiques

## 11. Conclusion

Le système fournit une solution robuste et efficace pour la surveillance des EPI en temps réel. L'architecture modulaire permet une maintenance facile et des évolutions futures. Les différentes composantes (détection, communication, visualisation, alertes) fonctionnent de manière cohérente pour assurer la sécurité des travailleurs.

## 12. Annexes

### 12.1 Dépendances

### 12.2 Structure des fichiers
project/
├── backend/
│ ├── app.py
│ ├── services/
│ │ └── mqtt_service.py
│ └── detections/
├── frontend/
│ ├── src/
│ │ ├── App.jsx
│ │ └── App.css
│ └── public/
├── esp32/
│ ├── main.py
│ └── boot.py
└── README.md
encore tu pa generer dans le rapport 

Je vais continuer à générer le rapport avec plus de détails et une meilleure structure :
+---------------+
| Caméra |
+-------+-------+
|
v
+---------------+
| Backend Flask |
+-------+-------+
|
+-------v-------+
| MQTT Broker |
+-------+-------+
|
+-------------+-------------+
| |
+-------v-------+ +-------v-------+
| Frontend React| | ESP32 |
+---------------+ +-------+-------+
|
+-------v-------+
| LEDs (R/G) |
+---------------+
python
MQTT_CONFIG = {
'broker_host': "bee321a450aa496ca69c29cfcad112a5.s1.eu.hivemq.cloud",
'broker_port': 8883,
'username': "salwaroot",
'password': "Emploi@2024",
'topic': "ppe/detections"
}
json
{
"timestamp": "2024-03-17T21:18:04",
"total_persons": 3,
"secured_persons": 2,
"partially_secured": 0,
"unsecured": 1,
"is_secure": false,
"detections": [...]
}
sql
CREATE TABLE detections (
id INTEGER PRIMARY KEY AUTOINCREMENT,
timestamp TEXT,
total_persons INTEGER,
secured_persons INTEGER,
partially_secured INTEGER,
unsecured INTEGER,
image_path TEXT
);
bash
Backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
Frontend
cd frontend
npm install
ESP32
Flasher MicroPython
Uploader main.py et boot.py
project/
├── backend/
│ ├── app.py
│ ├── services/
│ │ └── mqtt_service.py
│ └── detections/
├── frontend/
│ ├── src/
│ │ ├── App.jsx
│ │ └── App.css
│ └── public/
├── esp32/
│ ├── main.py
│ └── boot.py
└── README.md
Ce rapport fournit une documentation complète et structurée du projet, facilitant sa compréhension, son déploiement et sa maintenance.