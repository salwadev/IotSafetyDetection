import paho.mqtt.client as mqtt
import ssl
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MQTTService:
    def __init__(self, broker_host, broker_port, username, password, topic):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.topic = topic
        self.client = None
        self.setup_client()

    def setup_client(self):
        """Configure le client MQTT avec les paramètres de sécurité"""
        try:
            # Créer un client avec un ID unique
            client_id = f'python-mqtt-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
            self.client = mqtt.Client(client_id=client_id)
            
            # Configurer les credentials
            self.client.username_pw_set(self.username, self.password)
            
            # Configurer TLS
            self.client.tls_set(cert_reqs=ssl.CERT_REQUIRED,
                              tls_version=ssl.PROTOCOL_TLSv1_2)
            self.client.tls_insecure_set(False)
            
            # Définir les callbacks
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_publish = self.on_publish

            logger.info("Client MQTT configuré avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la configuration du client MQTT: {e}")
            raise

    def connect(self):
        """Établit la connexion au broker MQTT"""
        try:
            self.client.connect(self.broker_host, self.broker_port)
            self.client.loop_start()
            logger.info("Connexion MQTT établie")
        except Exception as e:
            logger.error(f"Erreur de connexion au broker MQTT: {e}")
            raise

    def disconnect(self):
        """Ferme la connexion MQTT proprement"""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Déconnexion MQTT effectuée")
        except Exception as e:
            logger.error(f"Erreur lors de la déconnexion MQTT: {e}")

    def publish_detection(self, detection_data):
        """Publie les données de détection sur le topic MQTT"""
        try:
            if not self.client.is_connected():
                self.connect()

            # Ajouter le timestamp
            detection_data["timestamp"] = datetime.now().isoformat()
            
            # Publier le message
            message = json.dumps(detection_data)
            result = self.client.publish(self.topic, message, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Message publié avec succès sur {self.topic}")
            else:
                logger.error(f"Échec de la publication: {result.rc}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la publication MQTT: {e}")
            raise

    # Callbacks MQTT
    def on_connect(self, client, userdata, flags, rc):
        """Callback appelé lors de la connexion au broker"""
        if rc == 0:
            logger.info("Connecté au broker MQTT")
        else:
            logger.error(f"Échec de connexion au broker MQTT, code: {rc}")

    def on_disconnect(self, client, userdata, rc):
        """Callback appelé lors de la déconnexion"""
        if rc != 0:
            logger.warning("Déconnexion inattendue du broker MQTT")

    def on_publish(self, client, userdata, mid):
        """Callback appelé après la publication d'un message"""
        logger.debug(f"Message {mid} publié avec succès") 