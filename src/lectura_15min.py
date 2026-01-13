import serial
import time
import pandas as pd
import re
import nest_asyncio
import paho.mqtt.client as mqtt
import json
import math

nest_asyncio.apply()

ser = serial.Serial('/dev/ttyACM0', 57600, timeout=1)


ahora = time.localtime()
minutos = ahora.tm_min
segundos = ahora.tm_sec
espera_minutos = (15 - (minutos % 15)) % 15
espera_segundos = espera_minutos * 60 - segundos
if espera_segundos > 0:
    time.sleep(espera_segundos)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "sonometro")
client.connect("192.168.0.220", 1883)
client.loop_start() #Sin esto se muere por la larga espera de intervalo ya que piensa que esta inactivo

try:

    ser.write(b'1\r')  # PLAY
    intervalo = 900  # segundos
    reinicio_cada = 900  # segundos (15 minutos)
    segundos_muertos = 3

    accumulated_data = {}
    start_time = time.time()
    current_interval = 0

    while True:
        response = ""
        while time.time() - start_time < intervalo * (current_interval + 1):
            time.sleep(1)
            response += ser.read_all().decode('ascii')
            ser.flushInput()

        lineas = response.strip().split('\n')
        datos_divididos = [linea.split() for linea in lineas]
        df = pd.DataFrame(datos_divididos)
        df = df.iloc[13:]
        df = df.dropna(how="all")
        df = df.applymap(lambda x: re.sub(r'\s*\"', '', str(x)))
        df = df.applymap(lambda x: re.sub(r'\s*LC1', 'LC', str(x)))
        df = df.applymap(lambda x: re.sub(r'\s*LA1', 'LA', str(x)))

        datos = {}

        for i, row in df.iterrows():
            if len(row) >= 6:
                parametro = row[0]
                parametro1 = row[2]
                parametro2 = row[4]

                valor1 = row[1]
                valor2 = row[3]
                valor3 = row[5]

                if valor1 != 'None' and valor1 != []:
                    datos.setdefault(parametro, []).append(valor1)
                if valor2 != 'None' and valor2 != []:
                    datos.setdefault(parametro1, []).append(valor2)
                if valor3 != 'None' and valor3 != []:
                    datos.setdefault(parametro2, []).append(valor3)

        for key, value in datos.items():
            for val in value:
                try:
                    num = float(val)
                    if key in ['LAt', 'LCt']:
                        accumulated_data[key] = [num] #siempre reemplaza el ultimo valor
                    else:
                        accumulated_data.setdefault(key, []).append(num)
                except ValueError:
                    pass

        if time.time() - start_time >= intervalo * (current_interval + 1):
            parametros_interes = ['LA', 'LAF', 'LAFmax', 'LAFmin', 'LAS', 'LASmax', 'LASmin', 'LAt', 'LC', 'LCF', 'LCFmax', 'LCFmin', 'LCpeak', 'LCt']
            datos_interes = {}

            for k in parametros_interes:
                muestras = accumulated_data.get(k, [])
                
                if muestras:
                    if k in ['LAt', 'LCt']:
                        datos_interes[k] = [round(muestras[-1], 2)] #Ultimo valor tal cual viene
                    else:
                        try:
                            leq = 10 * math.log10(sum([10 ** (x / 10) for x in muestras]) / len(muestras))
                            datos_interes[k] = [round(leq, 2)]
                        except:
                            datos_interes[k] = []
                else:
                    datos_interes[k] = []

            datos_interes['t'] = time.strftime('%H:%M:%S', time.gmtime(intervalo * (current_interval + 1)))
            #print("Publicando:", datos_interes)
            client.publish("sonometro/datos", json.dumps(datos_interes))

            accumulated_data = {}
            current_interval += 1

            # Cada 15 minutos, mandar STOP, esperar 3 segundos y volver a PLAY
            if (intervalo * current_interval) % reinicio_cada == 0:
                print("Reiniciando sonómetro...")  # Consola
                client.publish("sonometro/datos", json.dumps({
                    "estado": "reinicio",
                    "mensaje": "Reiniciando sonómetro para limpiar LAt y LCt",
                    "timestamp": time.strftime('%H:%M:%S')
                }))
                ser.write(b'0\r')  # STOP
                time.sleep(segundos_muertos)
                ser.write(b'1\r')  # PLAY
                #print("Reinicio completado.")
finally:
    ser.write(b'0\r')
    time.sleep(2)
    ser.close()
    client.loop_stop()
    client.disconnect()
