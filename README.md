# 🌱 Project Gaia: AI-Driven Hydroponic Digital Twin

Bu proje, modern bir topraksız tarım (hydroponic) sisteminin uçtan uca simülasyonunu ve otonom yönetimini içerir.

## 🚀 Özellikler

* **Dijital İkiz (Digital Twin):** Gerçek fizik kurallarına dayalı sera simülasyonu.
* **IoT Altyapısı:** MQTT (Mosquitto) ve InfluxDB ile gerçek zamanlı veri akışı.
* **Otonom Karar Mekanizması:** Sensör verilerine göre motor ve pH kontrolü (`brain.py`).
* **Yapay Zeka Tahmini:** Linear Regression ile su tüketim tahmini (`ml_service.py`).
* **Görüntü İşleme (Computer Vision):** YOLO mimarisi ile sanal ürün olgunluk ve hastalık tespiti.
* **API Gateway:** FastAPI ile dış dünyaya açılan modern REST API.

## 🛠️ Kurulum

1. Gereksinimleri yükleyin:
   ```bash
   pip install -r requirements.txt