from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
import paho.mqtt.client as mqtt
import ssl
import sqlite3
from datetime import datetime
import cv2
import numpy as np
from ultralytics import YOLO
import base64
import json
from flask_sock import Sock
import time
import os
import random
import string

app = Flask(__name__)
CORS(app)

# Configuration MQTT
MQTT_BROKER_HOST = "bee321a450aa496ca69c29cfcad112a5.s1.eu.hivemq.cloud"
MQTT_BROKER_PORT = 8883
MQTT_USERNAME = "salwaroot"
MQTT_PASSWORD = "Emploi@2024"
MQTT_TOPIC = "ppe/detections"

# Initialisation du client MQTT avec un ID unique
mqtt_client = mqtt.Client(client_id=f'python-mqtt-{random.randint(0, 1000)}')
mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
mqtt_client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2)
mqtt_client.tls_insecure_set(False)

# Callback pour la connexion
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connecté au broker MQTT")
    else:
        print(f"Échec de connexion au broker MQTT, code: {rc}")

mqtt_client.on_connect = on_connect

# Chargement du modèle YOLOv8
model = YOLO('models/best.pt')

sock = Sock(app)

def init_db():
    conn = sqlite3.connect('detections.db')
    c = conn.cursor()
    
    # Supprimer la table si elle existe
    c.execute('DROP TABLE IF EXISTS detections')
    
    # Créer la nouvelle table avec la bonne structure
    c.execute('''CREATE TABLE IF NOT EXISTS detections
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  total_persons INTEGER,
                  secured_persons INTEGER,
                  partially_secured INTEGER,
                  unsecured INTEGER,
                  image_path TEXT)''')
    conn.commit()
    conn.close()

# Au début du fichier, après les imports
import os

# Définir le chemin absolu du dossier detections
DETECTIONS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'detections')

# S'assurer que le dossier detections existe avec les bonnes permissions
try:
    if not os.path.exists(DETECTIONS_FOLDER):
        os.makedirs(DETECTIONS_FOLDER, mode=0o777)
    print(f"Dossier de détections créé/vérifié: {DETECTIONS_FOLDER}")
except Exception as e:
    print(f"Erreur lors de la création du dossier detections: {e}")

def find_closest_person(equipment_box, detections):
    """
    Trouve la personne la plus proche d'un équipement détecté
    """
    if not detections:
        return None
        
    equipment_center = ((equipment_box[0] + equipment_box[2])/2, (equipment_box[1] + equipment_box[3])/2)
    min_distance = float('inf')
    closest_person = None
    
    for person_id, person in detections.items():
        person_box = person['bbox']
        person_center = ((person_box[0] + person_box[2])/2, (person_box[1] + person_box[3])/2)
        
        distance = ((person_center[0] - equipment_center[0])**2 + 
                   (person_center[1] - equipment_center[1])**2)**0.5
                   
        if distance < min_distance:
            min_distance = distance
            closest_person = person_id
            
    return closest_person

def resize_image(image, target_width=520):
    """
    Redimensionne l'image en gardant le ratio d'aspect
    """
    height, width = image.shape[:2]
    ratio = target_width / width
    target_height = int(height * ratio)
    return cv2.resize(image, (target_width, target_height), interpolation=cv2.INTER_AREA)

def process_detection(image):
    # Redimensionner l'image
    image = resize_image(image, target_width=640)
    
    # Faire la prédiction
    results = model(image)[0]
    
    # Dictionnaire pour stocker les détections par personne
    person_detections = {}
    person_id = 0
    
    # Première passe : identifier toutes les personnes
    for r in results.boxes.data.tolist():
        x1, y1, x2, y2, score, class_id = r
        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
        class_name = model.names[int(class_id)]
        
        if class_name == 'Person':
            person_id += 1
            person_detections[person_id] = {
                'bbox': (x1, y1, x2, y2),
                'has_hardhat': False,
                'has_vest': False,
                'confidence': score
            }
    
    # Deuxième passe : vérifier les équipements
    for r in results.boxes.data.tolist():
        x1, y1, x2, y2, score, class_id = r
        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
        class_name = model.names[int(class_id)]
        
        if class_name in ['Hardhat', 'Safety Vest']:
            center_equipment = ((x1 + x2) // 2, (y1 + y2) // 2)
            min_distance = float('inf')
            closest_person = None
            
            for person_id, person_data in person_detections.items():
                px1, py1, px2, py2 = person_data['bbox']
                center_person = ((px1 + px2) // 2, (py1 + py2) // 2)
                distance = np.sqrt((center_equipment[0] - center_person[0])**2 + 
                                 (center_equipment[1] - center_person[1])**2)
                
                if distance < min_distance:
                    min_distance = distance
                    closest_person = person_id
            
            if closest_person and min_distance < 300:
                if class_name == 'Hardhat':
                    person_detections[closest_person]['has_hardhat'] = True
                elif class_name == 'Safety Vest':
                    person_detections[closest_person]['has_vest'] = True
    
    # Créer une copie de l'image pour les annotations
    annotated_frame = image.copy()
    detections = []
    is_secure = True
    
    # Dessiner les résultats
    for person_id, data in person_detections.items():
        x1, y1, x2, y2 = data['bbox']
        has_hardhat = data['has_hardhat']
        has_vest = data['has_vest']
        
        if has_hardhat or has_vest:
            color = (0, 255, 0)  # Vert
            message = "Securisee"
            icon = "+"  # Plus simple et plus fiable que ✓
        elif not has_hardhat and has_vest:
            color = (0, 165, 255)  # Orange
            message = "Partiellement Securisee"
            icon = "~"  # Plus simple et plus fiable que !
        else:
            color = (0, 0, 255)  # Rouge
            message = "Non Securisee"
            icon = "X"  # Plus simple et plus fiable que ⚠
            is_secure = False
        
        # Dessiner le rectangle
        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 3)
        
        # Paramètres du texte
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6  # Légèrement plus grand pour meilleure lisibilité
        thickness = 2  # Plus épais pour meilleure visibilité
        padding = 5
        
        # Ajouter le texte avec fond
        text = f"[{icon}] {message}"  # Icône entre crochets pour meilleure visibilité
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        
        # Fond semi-transparent pour le texte
        overlay = annotated_frame.copy()
        cv2.rectangle(overlay, 
                     (x1, y1 - text_size[1] - 2*padding),
                     (x1 + text_size[0] + 2*padding, y1),
                     color, -1)
        cv2.addWeighted(overlay, 0.7, annotated_frame, 0.3, 0, annotated_frame)
        
        # Ajouter le texte
        cv2.putText(annotated_frame, text,
                   (x1 + padding, y1 - padding),
                   font, font_scale, (255, 255, 255),
                   thickness, cv2.LINE_AA)
        
        # Ajouter le pourcentage de confiance
        conf_text = f"{data['confidence']*100:.1f}%"
        conf_size = cv2.getTextSize(conf_text, font, font_scale*0.8, thickness)[0]
        
        # Fond pour le pourcentage
        cv2.rectangle(annotated_frame,
                     (x2 - conf_size[0] - 2*padding, y2),
                     (x2, y2 + conf_size[1] + 2*padding),
                     color, -1)
        
        # Ajouter le pourcentage
        cv2.putText(annotated_frame, conf_text,
                   (x2 - conf_size[0] - padding, y2 + conf_size[1] + padding//2),
                   font, font_scale*0.8, (255, 255, 255),
                   thickness, cv2.LINE_AA)
        
        # Ajouter à la liste des détections
        detections.append({
            "label": message,
            "confidence": float(data['confidence'])
        })
    
    return detections, is_secure, annotated_frame

def publish_to_mqtt(detections, is_secure):
    try:
        # Se connecter au broker MQTT si pas déjà connecté
        if not mqtt_client.is_connected():
            mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT)
            mqtt_client.loop_start()

        # Préparer les données à envoyer
        data = {
            "timestamp": datetime.now().isoformat(),
            "total_persons": len(detections),
            "secured_persons": sum(1 for d in detections if d['label'] == "Securisee"),
            "partially_secured": sum(1 for d in detections if d['label'] == "Partiellement Securisee"),
            "unsecured": sum(1 for d in detections if d['label'] == "Non Securisee"),
            "is_secure": is_secure,
            "detections": detections
        }

        # Publier les données
        mqtt_client.publish(MQTT_TOPIC, json.dumps(data))
        print(f"Données publiées sur MQTT: {data}")

    except Exception as e:
        print(f"Erreur lors de la publication MQTT: {e}")

BASE62 = string.digits + string.ascii_letters
def encode_base62(num):
    if num == 0:
        return BASE62[0]
    
    arr = []
    base = len(BASE62)
    while num:
        num, rem = divmod(num, base)
        arr.append(BASE62[rem])
    arr.reverse()
    return ''.join(arr)

def generate_base62_filename():
    # Générer un timestamp unique et l'encoder en base62
    timestamp = int(datetime.now().timestamp() * 1000)  # Millisecondes
    return f"det_{encode_base62(timestamp)}.jpg"

@app.route('/detect', methods=['POST'])
def detect():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400
        
    file = request.files['image']
    npimg = np.fromstring(file.read(), np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    
    # Vérifier si l'image est valide
    if img is None:
        return jsonify({"error": "Invalid image"}), 400
    
    # Redimensionner l'image
    img = resize_image(img, target_width=640)
    
    detections, is_secure, annotated_frame = process_detection(img)
    
    # Convertir l'image annotée en base64
    _, buffer = cv2.imencode('.jpg', annotated_frame)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    
    # Sauvegarder dans la base de données
    conn = sqlite3.connect('detections.db')
    c = conn.cursor()
    
    # Générer un nom de fichier en base62
    image_filename = generate_base62_filename()
    image_path = os.path.join(DETECTIONS_FOLDER, image_filename)
    success = cv2.imwrite(image_path, annotated_frame)
    if success:
        print(f"Image sauvegardée avec succès: {image_path}")
    else:
        print(f"Échec de la sauvegarde de l'image: {image_path}")
    
    c.execute('''INSERT INTO detections 
                 (timestamp, total_persons, secured_persons, partially_secured, unsecured, image_path)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (datetime.now().isoformat(), 
               len(detections),
               sum(1 for d in detections if d['label'] == "Securisee"),
               sum(1 for d in detections if d['label'] == "Partiellement securisee"),
               sum(1 for d in detections if d['label'] == "Non securisee"),
               image_filename))  # Sauvegarder uniquement le nom du fichier
    conn.commit()
    conn.close()
    
    # Préparer la réponse
    response_data = {
        "timestamp": datetime.now().isoformat(),
        "total_persons": len(detections),
        "secured_persons": sum(1 for d in detections if d['label'] == "Securisee"),
        "partially_secured": sum(1 for d in detections if d['label'] == "Partiellement Securisee"),
        "unsecured": sum(1 for d in detections if d['label'] == "Non Securisee"),
        "image": img_base64,
        "detections": detections,
        "is_secure": is_secure
    }
    
    return jsonify(response_data)

@app.route('/stop-video')
def stop_video():
    try:
        # Libérer la caméra globale si elle existe
        if hasattr(app, 'camera') and app.camera is not None:
            app.camera.release()
            app.camera = None
            cv2.destroyAllWindows()  # Fermer toutes les fenêtres OpenCV
            print("Caméra arrêtée et libérée")
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Erreur lors de l'arrêt de la caméra: {e}")
        return jsonify({"status": "error", "message": str(e)})

last_save_time = 0
SAVE_INTERVAL = 15  # Intervalle en secondes

@app.route('/video-feed')
def video_feed():
    def generate():
        global last_save_time
        print("Démarrage de la détection en temps réel...")
        
        # Vérifier si une instance de caméra existe déjà et la fermer
        if hasattr(app, 'camera') and app.camera is not None:
            app.camera.release()
            app.camera = None
            cv2.destroyAllWindows()
        
        # Essayer différentes méthodes d'ouverture de la caméra
        for api in [cv2.CAP_DSHOW, cv2.CAP_ANY]:
            app.camera = cv2.VideoCapture(0, api)
            if app.camera.isOpened():
                print(f"Caméra ouverte avec succès en utilisant l'API {api}")
                break
        
        if not app.camera.isOpened():
            print("Erreur: Impossible d'ouvrir la caméra")
            return
        
        try:
            # Configuration de la caméra
            app.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            app.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            app.camera.set(cv2.CAP_PROP_FPS, 30)
            app.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            
            # Attendre que la caméra s'initialise
            time.sleep(2)
            
            while getattr(app, 'camera', None) is not None and app.camera.isOpened():
                try:
                    success, frame = app.camera.read()
                    if not success or frame is None:
                        print("Erreur de lecture de frame, tentative de réinitialisation...")
                        break  # Sortir de la boucle en cas d'erreur
                    
                    # Traitement des détections
                    detections, is_secure, annotated_frame = process_detection(frame)
                    
                    # Vérifier si 15 secondes se sont écoulées
                    current_time = time.time()
                    if current_time - last_save_time >= SAVE_INTERVAL:
                        # Publier sur MQTT
                        publish_to_mqtt(detections, is_secure)
                        
                        # Sauvegarder dans la base de données
                        try:
                            conn = sqlite3.connect('detections.db')
                            c = conn.cursor()
                            image_filename = generate_base62_filename()
                            image_path = os.path.join(DETECTIONS_FOLDER, image_filename)
                            cv2.imwrite(image_path, annotated_frame)
                            
                            c.execute('''INSERT INTO detections 
                                        (timestamp, total_persons, secured_persons, partially_secured, unsecured, image_path)
                                        VALUES (?, ?, ?, ?, ?, ?)''',
                                     (datetime.now().isoformat(), 
                                      len(detections),
                                      sum(1 for d in detections if d['label'] == "Securisee"),
                                      sum(1 for d in detections if d['label'] == "Partiellement Securisee"),
                                      sum(1 for d in detections if d['label'] == "Non Securisee"),
                                      image_filename))
                            conn.commit()
                            conn.close()
                            print("Données sauvegardées avec succès")
                            last_save_time = current_time
                        except Exception as e:
                            print(f"Erreur lors de la sauvegarde en base de données: {e}")
                    
                    # Encoder et envoyer l'image
                    ret, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                    if not ret:
                        continue
                    
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    
                except Exception as e:
                    print(f"Erreur lors du traitement: {e}")
                    break  # Sortir de la boucle en cas d'erreur
                
                time.sleep(0.01)
            
        finally:
            # S'assurer que la caméra est bien libérée
            if hasattr(app, 'camera') and app.camera is not None:
                app.camera.release()
                app.camera = None
                cv2.destroyAllWindows()
                print("Caméra libérée")
            
            # Déconnecter MQTT à la fin
            if mqtt_client.is_connected():
                mqtt_client.loop_stop()
                mqtt_client.disconnect()
    
    return Response(generate(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/check-camera')
def check_camera():
    """Route pour vérifier la disponibilité de la caméra"""
    try:
        # Essayer d'abord avec DirectShow
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            # Si ça échoue, essayer l'API par défaut
            cap = cv2.VideoCapture(0)
            
        if cap.isOpened():
            # Lire quelques frames pour s'assurer que la caméra fonctionne
            for _ in range(5):
                ret, frame = cap.read()
                if ret and frame is not None:
                    cap.release()
                    return jsonify({
                        "status": "success",
                        "message": "Caméra fonctionnelle"
                    })
            
            cap.release()
            return jsonify({
                "status": "error",
                "message": "La caméra ne fournit pas d'images valides"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Impossible d'ouvrir la caméra"
            })
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Erreur: {str(e)}"
        })

@app.route('/get-history')
def get_history():
    conn = sqlite3.connect('detections.db')
    c = conn.cursor()
    c.execute('''SELECT 
                    timestamp,
                    total_persons,
                    secured_persons as securise,
                    unsecured as non_securise,
                    image_path
                 FROM detections 
                 ORDER BY timestamp DESC 
                 LIMIT 50''')
    
    history = [{
        "timestamp": row[0],
        "total_persons": row[1],
        "securise": row[2],
        "non_securise": row[3],
        "image_path": row[4]
    } for row in c.fetchall()]
    
    conn.close()
    return jsonify(history)

@app.route('/detections/<path:filename>')
def serve_detection_image(filename):
    try:
        # Vérifier si le fichier existe
        full_path = os.path.join(DETECTIONS_FOLDER, filename)
        if os.path.exists(full_path):
            return send_from_directory(DETECTIONS_FOLDER, filename)
        else:
            print(f"Fichier non trouvé: {full_path}")
            return jsonify({"error": "Image not found"}), 404
    except Exception as e:
        print(f"Erreur lors de l'accès à l'image {filename}: {e}")
        return jsonify({"error": str(e)}), 500

@sock.route('/ws')
def ws(ws):
    while True:
        try:
            if not hasattr(app, 'camera') or app.camera is None:
                time.sleep(0.1)
                continue
                
            success, frame = app.camera.read()
            if success:
                detections, is_secure, _ = process_detection(frame)
                
                # Calculer les statistiques
                secured_count = sum(1 for d in detections if d['label'] == "Securisee")
                partially_secured_count = sum(1 for d in detections if d['label'] == "Partiellement Securisee")
                unsecured_count = sum(1 for d in detections if d['label'] == "Non Securisee")
                
                data = {
                    "timestamp": datetime.now().isoformat(),
                    "total_persons": len(detections),
                    "secured_persons": secured_count,
                    "partially_secured": partially_secured_count,
                    "unsecured": unsecured_count,
                    "detections": detections,
                    "is_secure": is_secure
                }
                
                ws.send(json.dumps(data))
            
            time.sleep(0.1)  # Éviter de surcharger la connexion
            
        except Exception as e:
            print(f"Erreur WebSocket: {e}")
            break

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
