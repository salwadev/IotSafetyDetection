#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// Configuration WiFi
const char* ssid = "Wokwi-GUEST";
const char* password = "";

// Configuration MQTT
const char* mqtt_server = "broker.hivemq.com";  // Broker public HiveMQ
const int mqtt_port = 1883;  // Port non sécurisé
const char* mqtt_topic = "ppe/detections";

// Définition des pins LED
const int LED_RED = D2;    // LED rouge pour non sécurisé
const int LED_GREEN = D3;  // LED verte pour sécurisé

// Variables de debug
unsigned long lastDebugTime = 0;
const unsigned long DEBUG_INTERVAL = 5000; // 5 secondes

WiFiClient espClient;
PubSubClient client(espClient);

void setup_wifi() {
  delay(10);
  Serial.println("\nConnexion au WiFi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connecté");
  Serial.print("Adresse IP: ");
  Serial.println(WiFi.localIP());
}

void updateLEDs(bool is_secure) {
  if (is_secure) {
    digitalWrite(LED_RED, LOW);
    digitalWrite(LED_GREEN, HIGH);
    Serial.println("Situation sécurisée - LED verte allumée");
  } else {
    digitalWrite(LED_RED, HIGH);
    digitalWrite(LED_GREEN, LOW);
    Serial.println("Situation non sécurisée - LED rouge allumée");
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message reçu [");
  Serial.print(topic);
  Serial.print("] ");

  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println(message);

  StaticJsonDocument<1024> doc;
  DeserializationError error = deserializeJson(doc, message);

  if (error) {
    Serial.print("deserializeJson() failed: ");
    Serial.println(error.c_str());
    return;
  }

  int total_persons = doc["total_persons"];
  int secured_persons = doc["secured_persons"];
  int unsecured = doc["unsecured"];
  bool is_secure = doc["is_secure"];

  Serial.println("\nDétections:");
  Serial.print("Total personnes: "); Serial.println(total_persons);
  Serial.print("Personnes sécurisées: "); Serial.println(secured_persons);
  Serial.print("Personnes non sécurisées: "); Serial.println(unsecured);
  Serial.print("Situation sécurisée: "); Serial.println(is_secure ? "Oui" : "Non");

  updateLEDs(is_secure);
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Tentative de connexion MQTT...");
    String clientId = "ESP32Client-" + String(random(0xffff), HEX);
    
    if (client.connect(clientId.c_str())) {
      Serial.println("connecté");
      client.subscribe(mqtt_topic);
      
      // Test des LEDs à la connexion
      digitalWrite(LED_RED, HIGH);
      delay(500);
      digitalWrite(LED_RED, LOW);
      digitalWrite(LED_GREEN, HIGH);
      delay(500);
      digitalWrite(LED_GREEN, LOW);
    } else {
      Serial.print("échec, rc=");
      Serial.print(client.state());
      Serial.println(" nouvelle tentative dans 5 secondes");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  
  // Configuration des pins LED
  pinMode(LED_RED, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);
  
  // Test initial des LEDs
  digitalWrite(LED_RED, HIGH);
  digitalWrite(LED_GREEN, HIGH);
  delay(1000);
  digitalWrite(LED_RED, LOW);
  digitalWrite(LED_GREEN, LOW);
  
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
  
  Serial.println("Système de détection EPI démarré!");
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Debug périodique
  unsigned long currentTime = millis();
  if (currentTime - lastDebugTime > DEBUG_INTERVAL) {
    lastDebugTime = currentTime;
    Serial.print("État MQTT: ");
    Serial.println(client.connected() ? "Connecté" : "Déconnecté");
    Serial.print("État WiFi: ");
    Serial.println(WiFi.status() == WL_CONNECTED ? "Connecté" : "Déconnecté");
  }
} 