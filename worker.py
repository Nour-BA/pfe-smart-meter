import paho.mqtt.client as mqtt
from pymongo import MongoClient
import json
from datetime import datetime
import os

# --- CONFIGURATION (À adapter avec tes accès) ---
# Si tu l'héberges, utilise des variables d'environnement. 
# Pour un test rapide, tu peux mettre tes liens en texte entre guillemets.
MONGO_URI = "ton_lien_atlas"
MQTT_BROKER = "ton_broker_hivemq"
MQTT_USER = "ton_user"
MQTT_PASS = "ton_pass"

# --- CONNEXION BASE DE DONNÉES ---
client_db = MongoClient(MONGO_URI)
db = client_db["SmartMeter_PFE"]
collection = db["historique_energie"]

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connecté au Broker HiveMQ")
        client.subscribe("maison/compteur")
    else:
        print(f"❌ Erreur de connexion : {rc}")

def on_message(client, userdata, msg):
    try:
        # Décoder le message JSON envoyé par l'ESP32 ou le Web Client
        payload = msg.payload.decode()
        data = json.loads(payload)
        
        # Ajouter la date et l'heure précise du stockage
        data["timestamp"] = datetime.now()
        
        # Enregistrer dans la bonne collection
        collection.insert_one(data)
        print(f"💾 Donnée stockée dans historique_energie : {data}")
        
    except Exception as e:
        print(f"⚠️ Erreur de formatage : {e}")

# --- LANCEMENT ---
client = mqtt.Client()
client.username_pw_set(MQTT_USER, MQTT_PASS)
client.tls_set()

client.on_connect = on_connect
client.on_message = on_message

print("🚀 Lancement du stockage automatique...")
client.connect(MQTT_BROKER, 8883)
client.loop_forever() # Boucle infinie pour un fonctionnement 24h/24
