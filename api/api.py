import logging
from fastapi import FastAPI
from pydantic import BaseModel
from catboost import CatBoostClassifier  # Importar CatBoost
import pandas as pd
from datetime import datetime, timezone, timedelta
import numpy as np
import weather as we

app = FastAPI()
model = CatBoostClassifier()  # Crear instancia vacía
model.load_model("./modelo_catboost3.cbm")  # Cargar el modelo entrenado

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


class Ubicacion(BaseModel):
    lat: float
    lon: float
    lead: int

@app.post("/predecir")
def predecir(ubicacion: Ubicacion):
    try:
        logging.info(f"Petición recibida: lat={ubicacion.lat}, lon={ubicacion.lon}, lead={ubicacion.lead}")
        
        hoy = datetime.now().astimezone(timezone.utc) + timedelta(hours=ubicacion.lead)
        hora_actual = hoy.hour
        minuto_actual = hoy.minute
        half_day = 'AM' if hora_actual < 12 else 'PM'
        hour_integer = hora_actual + 1 if minuto_actual >= 30 else hora_actual
        hour_integer = min(hour_integer, 23)

        base = pd.DataFrame([{
            'Ambiente': 'afuera',
            'alt': '13',
            'lat': ubicacion.lat,
            'lon': ubicacion.lon,
            'Half_of_day': half_day,
            'hour': hora_actual,
            'minute': minuto_actual,
            'month': hoy.month,
            'day': hoy.day,
            'month(text)': hoy.strftime('%b'),
            'date': hoy.date(),
            'hour_integer': hour_integer,
            'id': 0
        }])

        base['date'] = pd.to_datetime(base['date'])
        df = we.obtener_data_clima(base)
        logging.info("Datos meteorológicos obtenidos correctamente")

        hour_geo = df['hour_geo']
        precipitation_prob = (df['weather_rain'] + df['weather_snowfall'] + df['weather_showers']) / 3.0 

        df.drop(columns=[
            'hour', 'minute', 'day', 'date', 'id',
            'weather_precipitation_probability',
            'weather_boundary_layer_height',
            'weather_total_column_integrated_water_vapour','hour_geo'
        ], inplace=True)
        df.drop(columns=['lat','lon','month(text)'], inplace=True)
        df['season'] = df['month'].apply(lambda x: 'summer' if x in [12,1,2] else 'fall' if x in [3,4,5] else 'winter' if x in [6,7,8] else 'spring') 
        df.drop(columns=['month'], inplace=True)

        pred = model.predict_proba(df)
        logging.info("Predicción realizada correctamente")

        prob_df = pd.DataFrame({
            'prob_1st': pred.max(axis=1),
            'class_1st': model.classes_[pred.argmax(axis=1)],
            'prob_2nd': np.sort(pred, axis=1)[:, -2],
            'class_2nd': model.classes_[np.argsort(pred, axis=1)[:, -2]],
            'temperature': df['weather_temperature_2m'],
            'humidity': df['weather_relative_humidity_2m'],
            'apparent_temperature': df['weather_apparent_temperature'],
            'weather_wind_speed_10m': df['weather_wind_speed_10m'],
            'hour_integer': df['hour_integer'],
            'minute': minuto_actual,
            'hour_geo': hour_geo,
            'alt': df['alt'],
            'precipitation_prob': precipitation_prob,
            'precipitation': df['weather_precipitation']
        })

        return prob_df.iloc[0].to_dict()
    
    except Exception as e:
        logging.error(f"Error durante la predicción: {e}", exc_info=True)
        return {"error": "Ocurrió un error durante la predicción"}