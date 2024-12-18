import network
import time
import ssl
from machine import Pin
import dht
import ujson
from umqtt.robust import MQTTClient

# Configuration MQTT sécurisée
MQTT_CONFIG = {
    'broker_host': "bee321a450aa496ca69c29cfcad112a5.s1.eu.hivemq.cloud",
    'broker_port': 8883,  # Port sécurisé
    'username': "salwaroot",
    'password': "Emploi@2024",
    'topic': "ppe/detections"
}

# MQTT Server Parameters
MQTT_CLIENT_ID = "esp32-weather"
MQTT_BROKER = MQTT_CONFIG['broker_host']
MQTT_PORT = MQTT_CONFIG['broker_port']
MQTT_USER = MQTT_CONFIG['username']
MQTT_PASSWORD = MQTT_CONFIG['password']
MQTT_TOPIC = MQTT_CONFIG['topic']

# Initialisation du capteur DHT22
sensor = dht.DHT22(Pin(15))

# Connexion au réseau Wi-Fi
def connect_wifi():
    print("Connecting to WiFi", end="")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect('Wokwi-GUEST', '')  # Wokwi WiFi Network
    while not sta_if.isconnected():
        print(".", end="")
        time.sleep(0.5)
    print("\n✅ WiFi Connected! IP Address:", sta_if.ifconfig()[0])

# Connexion sécurisée au broker MQTT
def connect_mqtt():
    print("Connecting to MQTT broker...", end="")
    try:
        ssl_params = {'cert_reqs': ssl.CERT_NONE}  # Désactiver la vérification des certificats pour le test
        client = MQTTClient(
            client_id=MQTT_CLIENT_ID,
            server=MQTT_BROKER,
            port=MQTT_PORT,
            user=MQTT_USER,
            password=MQTT_PASSWORD,
            ssl=True,
            ssl_params=ssl_params
        )
        client.connect()
        print(" ✅ Connected!")
        return client
    except Exception as e:
        print("❌ Failed to connect to MQTT broker:", str(e))
        return None

# Fonction principale
def main():
    connect_wifi()  # Connexion au Wi-Fi
    client = connect_mqtt()  # Connexion au broker MQTT sécurisé

    if client is None:
        print("❌ Exiting due to MQTT connection failure.")
        return

    prev_weather = ""
    while True:
        try:
            print("\nMeasuring weather conditions...")
            sensor.measure()

            # Création du message JSON
            message = ujson.dumps({
                "temp": sensor.temperature(),
                "humidity": sensor.humidity(),
            })

            # Publier uniquement si le message change
            if message != prev_weather:
                print(f"📤 Publishing to topic '{MQTT_TOPIC}': {message}")
                client.publish(MQTT_TOPIC, message)
                prev_weather = message
            else:
                print("No change in weather conditions.")

            time.sleep(5)  # Pause de 5 secondes entre les mesures
        except Exception as e:
            print("❌ Error during execution:", str(e))
            time.sleep(5)

# Démarrage du programme
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🚪 Program stopped by user.")
