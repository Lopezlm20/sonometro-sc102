# Sistema de medición acústica con sonómetro CESVA SC102

Proyecto en Python para lectura, registro y procesamiento de datos provenientes del sonómetro CESVA SC102 a través del puerto serie.

Incluye tres herramientas principales:
- Lectura continua con promedio energético cada **1 minuto**
- Lectura continua con promedio energético cada **15 minutos**, sincronizado con reloj
- GUI para monitoreo manual y exportación a Excel

---

## 🧩 Características

✔ Lectura desde puerto serie (USB / tty)  
✔ Cálculo de valores en dB, incluyendo LAeq y LCeq por promedio energético  
✔ Publicación por MQTT (tópico `sonometro/datos`)  
✔ Reinicio automático del equipo cada 15 minutos para evitar acumulación  
✔ Interfaz gráfica con pausa, stop y guardado a Excel  
✔ Funciona en Windows y Linux
