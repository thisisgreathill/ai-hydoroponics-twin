import time
import json
import numpy as np
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta

# --- AYARLAR ---
MQTT_BROKER = "localhost"
MQTT_TOPIC_PREDICTION = "sera/tahminler"

INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "my-super-secret-auth-token"
INFLUX_ORG = "my-org"
INFLUX_BUCKET = "hydro_data"

def main():
    print("🧠 YAPAY ZEKA TAHMİN MOTORU (ML ENGINE) BAŞLATILIYOR...")
    
    # MQTT Bağlantısı
    mqtt_client = mqtt.Client()
    mqtt_client.connect(MQTT_BROKER, 1883, 60)

    # InfluxDB Bağlantısı
    db_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    query_api = db_client.query_api()

    # Model: Linear Regression
    model = LinearRegression()

    while True:
        # 1. VERİ TOPLA: Son 5 dakikalık su verisini çek
        query = f'''
        from(bucket: "{INFLUX_BUCKET}")
          |> range(start: -5m)
          |> filter(fn: (r) => r["_measurement"] == "sera_olcumleri")
          |> filter(fn: (r) => r["_field"] == "water_level")
          |> filter(fn: (r) => r["_value"] < 100) 
        '''
        # Not: <100 filtresi ekledik ki motor çalışırkenki ani yükselişleri (doldurma anını) hesaba katıp kafası karışmasın.
        
        result = query_api.query(org=INFLUX_ORG, query=query)
        
        data_points = []
        timestamps = []

        # Veriyi işle
        for table in result:
            for record in table.records:
                # Zamanı sayısal bir değere (timestamp) çeviriyoruz ki matematik yapabilelim
                ts = record.get_time().timestamp()
                val = record.get_value()
                timestamps.append([ts]) # Scikit-learn 2D array ister
                data_points.append(val)

        # Eğer yeterli veri varsa (en az 10 nokta) analize başla
        if len(data_points) > 10:
            X = np.array(timestamps)
            y = np.array(data_points)

            # 2. MODELİ EĞİT (Makine Öğrenmesi)
            # Model, zaman (X) ile su seviyesi (y) arasındaki ilişkiyi öğrenir.
            model.fit(X, y)

            # Eğim (Slope): Saniyede kaç litre su gidiyor?
            tuketim_hizi = model.coef_[0] # Negatif bir sayı çıkacaktır
            
            # 3. GELECEĞİ TAHMİN ET
            # Su ne zaman 0 olacak? (y = mx + b formülünden x'i buluyoruz)
            # 0 = (hız * zaman) + sabit -> zaman = -sabit / hız
            intercept = model.intercept_
            
            if tuketim_hizi < -0.0001: # Eğer su azalıyorsa
                bitis_zamani_timestamp = (0 - intercept) / tuketim_hizi
                su_an = time.time()
                kalan_saniye = bitis_zamani_timestamp - su_an
                
                kalan_dakika = kalan_saniye / 60
                
                # Tahmini yayınla
                tahmin_mesaji = {
                    "kalan_sure_dk": round(kalan_dakika, 1),
                    "tuketim_hizi_dk": round(tuketim_hizi * 60, 3) * -1, # Pozitif yapalım okunsun
                    "mesaj": f"Tahmini {round(kalan_dakika, 1)} dakika sonra su bitecek."
                }
                
                print(f"🔮 TAHMİN: Su {kalan_dakika:.1f} dakika sonra bitecek. (Hız: {tahmin_mesaji['tuketim_hizi_dk']:.3f} L/dk)")
                
                mqtt_client.publish(MQTT_TOPIC_PREDICTION, json.dumps(tahmin_mesaji))
            else:
                print("ℹ️ Su seviyesi sabit veya artıyor (Motor çalışıyor olabilir). Tahmin yapılmıyor.")

        else:
            print("⏳ Veri toplanıyor... (Yeterli geçmiş yok)")

        # Her 5 saniyede bir yeniden hesapla
        time.sleep(5)

if __name__ == "__main__":
    main()