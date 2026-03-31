import json
import time
import paho.mqtt.client as mqtt

# --- AYARLAR ---
MQTT_BROKER = "localhost"
MQTT_TOPIC_DATA = "sera/sensorler"
MQTT_TOPIC_CMD = "sera/komutlar"
MQTT_TOPIC_VISION = "sera/kamera/analiz" # Yeni kulak

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except:
        return

    # A) EĞER MESAJ SENSÖRDEN GELİRSE (Su, pH, Sıcaklık)
    if msg.topic == MQTT_TOPIC_DATA:
        su_seviyesi = payload.get("water_level", 100)
        ph_degeri = payload.get("ph", 6.0)
        motor_durumu = payload.get("pump_status", 0)

        # Su Kontrolü
        if su_seviyesi < 90 and motor_durumu == 0:
            print("💧 BEYİN KARARI: Su kritik! Motor AÇILIYOR...")
            client.publish(MQTT_TOPIC_CMD, "SU_MOTORU_AC")
        
        elif su_seviyesi >= 100 and motor_durumu == 1:
            print("✅ BEYİN KARARI: Depo doldu. Motor KAPATILIYOR...")
            client.publish(MQTT_TOPIC_CMD, "SU_MOTORU_KAPAT")

        # pH Kontrolü
        if ph_degeri > 6.5:
            print("🧪 BEYİN KARARI: pH yüksek! Dengeleyici dozajlanıyor...")
            client.publish(MQTT_TOPIC_CMD, "PH_DOZAJLA")

    # B) EĞER MESAJ KAMERADAN GELİRSE (Görüntü İşleme) - YENİ!
    elif msg.topic == MQTT_TOPIC_VISION:
        aksiyon = payload.get("action_required", "Yok")
        hastalik = payload.get("disease_detected", "Yok")

        if "HASAT" in aksiyon:
            print("🍓 BEYİN KARARI: Mükemmel olgunluk görüldü. HASAT ROBOTU BAŞLATILIYOR!")
            client.publish(MQTT_TOPIC_CMD, "ROBOT_HASAT_BASLA")
        
        elif "İLAÇLAMA" in aksiyon:
            print(f"☣️ BEYİN KARARI: {hastalik} tespit edildi. İLAÇLAMA BAŞLATILIYOR!")
            client.publish(MQTT_TOPIC_CMD, "ILACLAMA_BASLAT")

def main():
    print("🧠 OTONOM KONTROL ÜNİTESİ v2 (Sensor + Vision) DEVREDE...")
    
    client = mqtt.Client()
    client.connect(MQTT_BROKER, 1883, 60)

    client.on_message = on_message
    
    # Hem sensörleri hem kamerayı dinle
    client.subscribe([(MQTT_TOPIC_DATA, 0), (MQTT_TOPIC_VISION, 0)])

    client.loop_forever()

if __name__ == "__main__":
    main()