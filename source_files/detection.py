from ultralytics import YOLO
import cv2
import numpy as np

class PPEDetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        
    def detect_image(self, image):
        results = self.model(image)
        annotated_frame = results[0].plot()
        
        detections = []
        is_secure = False
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                label = self.model.names[cls]
                
                if label == "person":
                    has_hardhat = any(self.model.names[int(b.cls[0])] == "hardhat" for b in boxes)
                    has_vest = any(self.model.names[int(b.cls[0])] == "vest" for b in boxes)
                    
                    if has_hardhat and has_vest:
                        label = "personne securisee"
                        is_secure = True
                    else:
                        label = "personne non securisee"
                        
                detections.append({
                    "label": label,
                    "confidence": conf,
                    "bbox": box.xyxy[0].tolist()
                })
        
        return annotated_frame, detections, is_secure
        
    def detect_video(self, video_source=0):
        cap = cv2.VideoCapture(video_source)
        
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break
                
            annotated_frame, detections, is_secure = self.detect_image(frame)
            
            yield annotated_frame, detections, is_secure
            
        cap.release()
