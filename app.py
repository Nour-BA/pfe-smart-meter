import streamlit as st
import paho.mqtt.client as mqtt

st.title("Test de réception MQTT")

# On utilise le session_state pour garder la trace de la connexion
if 'msg_recu' not in st.session_state:
    st.session_state.msg_recu = "Aucun message pour l'instant"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        st.success("✅ Streamlit est maintenant connecté à HiveMQ !")
        client.subscribe("maison/compteur")
    else:
        st.error(f"❌ Échec de connexion. Code retour: {rc}")

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    st.session_state.msg_recu = payload
    st.balloons() # Petit effet visuel quand on reçoit la donnée

# Initialisation automatique
client = mqtt.Client()
client.username_pw_set(st.secrets["MQTT_USER"], st.secrets["MQTT_PASS"])
client.tls_set()

try:
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(st.secrets["MQTT_BROKER"], 8883)
    client.loop_start()
except Exception as e:
    st.error(f"Erreur fatale : {e}")

st.write("Dernière donnée reçue :")
st.info(st.session_state.msg_recu)
