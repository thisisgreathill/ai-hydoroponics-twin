from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient
import json
import threading

# --- AYARLAR ---
app = FastAPI(title="Project Gaia API", version="2.0.0")

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_CMD = "sera/komutlar"
MQTT_TOPIC_VISION = "sera/kamera/analiz"

INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "my-super-secret-auth-token"
INFLUX_ORG = "my-org"
INFLUX_BUCKET = "hydro_data"

# Global Hafıza (Kamera Sonuçları İçin)
LATEST_VISION_DATA = {"status": "Veri bekleniyor..."}

# --- YARDIMCI İŞLEMLER ---
def on_vision_message(client, userdata, msg):
    global LATEST_VISION_DATA
    try:
        LATEST_VISION_DATA = json.loads(msg.payload.decode())
    except:
        pass

def start_mqtt_listener():
    """Arka planda MQTT dinleyen servis"""
    client = mqtt.Client()
    client.on_message = on_vision_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(MQTT_TOPIC_VISION)
    client.loop_start()

# Uygulama başlarken dinleyiciyi çalıştır
start_mqtt_listener()

def get_latest_sensor_data():
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    query_api = client.query_api()
    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -1m)
      |> filter(fn: (r) => r["_measurement"] == "sera_olcumleri")
      |> last()
    '''
    result = query_api.query(org=INFLUX_ORG, query=query)
    data = {}
    for table in result:
        for record in table.records:
            data[record.get_field()] = record.get_value()
    client.close()
    return data

class KomutModel(BaseModel):
    komut: str

# --- ENDPOINTLER ---

@app.get("/")
def read_root():
    return {"mesaj": "Project Gaia API v2 - Vision Supported"}

@app.get("/durum")
def oku_sensorler():
    return get_latest_sensor_data()

@app.get("/kamera")
def oku_kamera():
    """En son yapay zeka analizini getirir"""
    return LATEST_VISION_DATA

@app.post("/kontrol")
def gonder_komut(istek: KomutModel):
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.publish(MQTT_TOPIC_CMD, istek.komut)
    client.disconnect()
    return {"durum": "Komut Gönderildi", "komut": istek.komut}