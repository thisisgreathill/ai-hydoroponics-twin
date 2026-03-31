import time
import json
import random
import math
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# --- AYARLAR ---
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_DATA = "sera/sensorler"
MQTT_TOPIC_CMD = "sera/komutlar"

INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "my-super-secret-auth-token"
INFLUX_ORG = "my-org"
INFLUX_BUCKET = "hydro_data"

class DigitalTwinSera:
    def __init__(self):
        self.temp = 22.0
        self.humidity = 60.0
        self.ph = 6.0
        self.water_level = 100.0
        self.hour = 0
        self.pump_status = False

    def update_physics(self):
        self.hour += 0.5
        if self.hour >= 24: self.hour = 0

        # Fiziksel değişimler
        if not self.pump_status:
            self.water_level -= 0.1 
        else:
            self.water_level += 2.0 

        self.ph += random.uniform(0.005, 0.01)

        # Basit Sıcaklık simülasyonu
        day_factor = math.sin((self.hour - 6) * math.pi / 12)
        self.temp = 20 + (5 * day_factor) + random.uniform(-0.5, 0.5)

    def apply_command(self, command):
        """YENİ KOMUTLAR EKLENDİ"""
        if command == "SU_MOTORU_AC":
            self.pump_status = True
        elif command == "SU_MOTORU_KAPAT":
            self.pump_status = False
        elif command == "PH_DOZAJLA":
            self.ph -= 0.5 
            print("🧪 Simülasyon: pH Düşürücü Enjekte Edildi.")
        
        # --- YENİ AKSİYONLAR ---
        elif command == "ROBOT_HASAT_BASLA":
            print("\n🤖 SİMÜLASYON: Robot kollar çalıştı. Çilekler toplandı!")
            print("📦 SİMÜLASYON: Paketleme ünitesine gönderildi.\n")
        
        elif command == "ILACLAMA_BASLAT":
            self.humidity += 5 # İlaç sıvıdır, nemi artırır
            print("\n🚿 SİMÜLASYON: İlaçlama nozulları aktif. Püskürtme yapılıyor...\n")

    def get_data(self):
        return {
            "temperature": round(self.temp, 2),
            "humidity": round(self.humidity, 2),
            "ph": round(self.ph, 2),
            "water_level": round(self.water_level, 2),
            "pump_status": 1 if self.pump_status else 0
        }

sera = DigitalTwinSera()

def on_message(client, userdata, msg):
    komut = msg.payload.decode()
    print(f"📩 SİMÜLASYON EMRİ ALDI: {komut}")
    sera.apply_command(komut)

def main():
    print("🌱 DIGITAL TWIN v3 (Full Control) BAŞLATILIYOR...")
    
    mqtt_client = mqtt.Client()
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.subscribe(MQTT_TOPIC_CMD)
    mqtt_client.loop_start() 

    db_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    write_api = db_client.write_api(write_options=SYNCHRONOUS)

    while True:
        sera.update_physics()
        data = sera.get_data()

        mqtt_client.publish(MQTT_TOPIC_DATA, json.dumps(data))

        point = Point("sera_olcumleri") \
            .field("temperature", data["temperature"]) \
            .field("ph", data["ph"]) \
            .field("water_level", data["water_level"]) \
            .field("pump_status", data["pump_status"])
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)

        print(f"📡 Veri: Su={data['water_level']:.1f}L | pH={data['ph']:.2f}")
        time.sleep(1)

if __name__ == "__main__":
    main()