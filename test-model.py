from ultralytics import YOLO
import cv2
import numpy as np
import os

def process_frame(frame, model):
    # Faire la prédiction
    results = model(frame)[0]
    
    # Dictionnaire pour stocker les détections par personne
    person_detections = {}
    
    # Première passe : identifier toutes les personnes
    for r in results.boxes.data.tolist():
        x1, y1, x2, y2, score, class_id = r
        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
        class_name = model.names[int(class_id)]
        
        if class_name == 'Person':
            person_id = f"{x1}_{y1}"
            person_detections[person_id] = {
                'bbox': (x1, y1, x2, y2),
                'has_hardhat': False,
                'has_vest': False
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
    
    # Dessiner les résultats
    for person_id, data in person_detections.items():
        x1, y1, x2, y2 = data['bbox']
        has_hardhat = data['has_hardhat']
        has_vest = data['has_vest']
        
        if has_hardhat and has_vest:
            color = (0, 255, 0)  # Vert
            message = "Personne bien securisee"
        elif has_hardhat or has_vest:
            color = (0, 165, 255)  # Orange
            message = "Personne partiellement securisee"
        else:
            color = (0, 0, 255)  # Rouge
            message = "Personne non securisee"
        
        # Dessiner le rectangle
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
        
        # Ajouter le texte avec fond
        text_size = cv2.getTextSize(message, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        cv2.rectangle(frame, (x1, y1 - text_size[1] - 10), 
                     (x1 + text_size[0], y1), color, -1)
        cv2.putText(frame, message, (x1, y1 - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    return frame

def test_image(model_path, image_path):
    if not os.path.exists(image_path):
        print(f"Erreur: L'image n'existe pas: {image_path}")
        return
        
    print(f"Traitement de l'image: {image_path}")
    
    try:
        model = YOLO(model_path)
        print("Modèle chargé avec succès!")
    except Exception as e:
        print(f"Erreur lors du chargement du modèle: {e}")
        return
    
    image = cv2.imread(image_path)
    if image is None:
        print(f"Erreur: Impossible de charger l'image: {image_path}")
        return
    
    processed_image = process_frame(image, model)
    
    cv2.imshow('Detection de securite', processed_image)
    print("\nAppuyez sur une touche pour fermer la fenêtre...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def test_webcam(model_path):
    try:
        model = YOLO(model_path)
        print("Modèle chargé avec succès!")
    except Exception as e:
        print(f"Erreur lors du chargement du modèle: {e}")
        return
    
    # Initialiser la webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Erreur: Impossible d'ouvrir la webcam")
        return
    
    print("Démarrage de la détection en temps réel...")
    print("Appuyez sur 'q' pour quitter")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Erreur: Impossible de lire le flux vidéo")
            break
        
        # Traiter l'image
        processed_frame = process_frame(frame, model)
        
        # Afficher le résultat
        cv2.imshow('Detection en temps reel', processed_frame)
        
        # Quitter si 'q' est pressé
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    MODEL_PATH = "models/best.pt"
    IMAGE_PATH = "test_images/image6.jpg"
    
    if not os.path.exists(MODEL_PATH):
        print(f"Erreur: Le modèle n'existe pas: {MODEL_PATH}")
        print("Veuillez vérifier que le fichier best.pt est bien dans le dossier 'models'")
    else:
        while True:
            print("\nChoisissez le mode de détection:")
            print("1. Image")
            print("2. Webcam")
            print("3. Quitter")
            
            choice = input("Votre choix (1/2/3): ")
            
            if choice == '1':
                print("\nDémarrage de l'analyse d'image...")
                test_image(MODEL_PATH, IMAGE_PATH)
            elif choice == '2':
                print("\nDémarrage de la détection en temps réel...")
                test_webcam(MODEL_PATH)
            elif choice == '3':
                print("\nAu revoir!")
                break
            else:
                print("\nChoix invalide. Veuillez réessayer.") 