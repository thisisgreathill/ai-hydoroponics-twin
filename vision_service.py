import time
import json
import random
import paho.mqtt.client as mqtt

# --- AYARLAR ---
MQTT_BROKER = "localhost"
MQTT_TOPIC_VISION = "sera/kamera/analiz"

class PlantVisionAI:
    def __init__(self):
        self.plant_type = "Çilek (Albion Türü)"
        self.day = 0
        self.ripeness = 0  # 0: Yeşil, 100: Tam Kırmızı
        self.disease = "Yok"
        self.disease_prob = 0.0  # Hastalık ihtimali

    def analyze_frame(self):
        """Kameradan gelen görüntüyü (simüle) işler"""
        
        # 1. Büyüme Simülasyonu (Hızlandırılmış: Her döngü 1 sanal gün)
        self.day += 1
        
        # Olgunlaşma (Güneşli günlerde artar)
        growth_spur = random.uniform(2, 5)
        self.ripeness += growth_spur
        if self.ripeness > 100: self.ripeness = 100

        # 2. Renk Tespiti (Pixel Analizi Simülasyonu)
        color_detected = "Yeşil"
        if self.ripeness > 30: color_detected = "Beyaz-Yeşil"
        if self.ripeness > 60: color_detected = "Turuncu-Kırmızı"
        if self.ripeness > 90: color_detected = "Tam Kırmızı"

        # 3. Hastalık Tespiti (Anomaly Detection)
        # Bazen yaprakta leke oluşsun
        if self.disease == "Yok":
            if random.random() < 0.05: # %5 ihtimalle hastalık başlasın
                self.disease = "Külleme (Mantari)"
                self.disease_prob = random.uniform(0.70, 0.99) # AI Güven Skoru
        
        # 4. Sonuç JSON'ı Oluştur
        result = {
            "camera_id": "CAM_01",
            "detected_object": self.plant_type,
            "ripeness_percentage": round(self.ripeness, 1),
            "dominant_color": color_detected,
            "disease_detected": self.disease,
            "ai_confidence": round(self.disease_prob, 2) if self.disease != "Yok" else 0.99,
            "action_required": "Yok"
        }

        # 5. Karar Mekanizması
        if self.ripeness >= 95 and self.disease == "Yok":
            result["action_required"] = "🍓 HASAT ET (Mükemmel Olgunluk)"
        elif self.disease != "Yok":
            result["action_required"] = "⚠️ İLAÇLAMA YAP (Hastalık Tespit Edildi)"

        # Döngü sıfırlama (Çilek çürümesin, yeni fide ekilsin)
        if self.ripeness >= 100 or self.disease != "Yok":
            time.sleep(2) # Sonucu biraz ekranda tut
            self.reset_plant()

        return result

    def reset_plant(self):
        print("\n--- 🌱 YENİ FİDE DİKİLDİ (Sanal Döngü) ---\n")
        self.day = 0
        self.ripeness = 0
        self.disease = "Yok"

def main():
    print("👁️ BİLGİSAYARLI GÖRÜ SİSTEMİ (COMPUTER VISION) BAŞLATILIYOR...")
    print("Mimarisi: YOLOv8 Object Detection Simülasyonu")
    
    client = mqtt.Client()
    client.connect(MQTT_BROKER, 1883, 60)

    ai = PlantVisionAI()

    while True:
        data = ai.analyze_frame()
        
        # MQTT'ye gönder (Brain veya Dashboard görsün)
        payload = json.dumps(data)
        client.publish(MQTT_TOPIC_VISION, payload)

        # Log Bas
        status_icon = "🟢"
        if data["disease_detected"] != "Yok": status_icon = "☣️"
        if "HASAT" in data["action_required"]: status_icon = "🍓"

        print(f"{status_icon} [KAMERA 01] Algılandı: {data['detected_object']} | Renk: {data['dominant_color']} ({data['ripeness_percentage']}%) | Hastalık: {data['disease_detected']}")
        
        if data["action_required"] != "Yok":
            print(f"   >>> 📢 KARAR: {data['action_required']}")

        time.sleep(2) # Her 2 saniyede bir kare işle

if __name__ == "__main__":
    main()