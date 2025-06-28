import pandas as pd
import openmeteo_requests
from requests_cache import CachedSession
from retry_requests import retry
from datetime import timedelta
import time
import random

# Configuración del cliente API
cache_session = CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

def obtener_data_clima(base):
    url = "https://api.open-meteo.com/v1/forecast"
    results = []

    for index, row in base.iterrows():
        try:
            
            # Calcular rangos de fecha (día anterior y día posterior)
            current_date = pd.to_datetime(row['date'])
            start_date = (current_date - timedelta(days=1)).strftime('%Y-%m-%d')
            end_date = (current_date + timedelta(days=2)).strftime('%Y-%m-%d')
            target_date = current_date.strftime('%Y-%m-%d')
            
            params = {
                "latitude": row['lat'],
                "longitude": row['lon'],
                "start_date": start_date,
                "end_date": end_date,
                "hourly": ["temperature_2m","snow_depth", "relative_humidity_2m", "dew_point_2m", "apparent_temperature", "precipitation_probability", "precipitation", "rain", "showers", "snowfall", "weather_code", "pressure_msl", 
                        "surface_pressure", "cloud_cover", "cloud_cover_low", "cloud_cover_mid", "cloud_cover_high", "evapotranspiration", "visibility", "et0_fao_evapotranspiration", "vapour_pressure_deficit", "wind_speed_10m", "wind_speed_80m", 
                        "wind_speed_120m", "wind_speed_180m", "wind_direction_10m", "wind_direction_80m", "wind_direction_120m", "wind_direction_180m", "wind_gusts_10m", "temperature_80m", "temperature_120m", "temperature_180m", 
                        "soil_temperature_0cm", "soil_temperature_6cm", "soil_temperature_18cm", "soil_temperature_54cm", "soil_moisture_0_to_1cm", "soil_moisture_1_to_3cm", "soil_moisture_3_to_9cm", "soil_moisture_9_to_27cm", 
                        "soil_moisture_27_to_81cm", "uv_index", "uv_index_clear_sky", "is_day", "sunshine_duration", "wet_bulb_temperature_2m", "shortwave_radiation", "boundary_layer_height", "freezing_level_height", "convective_inhibition", 
                        "lifted_index", "cape", "total_column_integrated_water_vapour", "direct_radiation", "diffuse_radiation", "direct_normal_irradiance", "global_tilted_irradiance", "terrestrial_radiation", "terrestrial_radiation_instant", 
                        "global_tilted_irradiance_instant", "direct_normal_irradiance_instant", "diffuse_radiation_instant", "direct_radiation_instant", "shortwave_radiation_instant"],
                "timezone": "auto"
            }
            
            # Solicitud a la API
            responses = openmeteo.weather_api(url, params=params)
            response = responses[0]
            
            # Procesar datos
            hourly = response.Hourly()
            hourly_data = {
                "date": pd.date_range(
                    start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                    end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                    freq=pd.Timedelta(seconds=hourly.Interval()),
                    inclusive="left"
                )
            }
            
            # Añadir variables
            for i, var_name in enumerate(params["hourly"]):
                var = hourly.Variables(i)
                hourly_data[var_name] = var.ValuesAsNumpy()
            
            hourly_df = pd.DataFrame(data=hourly_data)
            hourly_df['date_corregida'] = hourly_df['date'] + timedelta(seconds=response.UtcOffsetSeconds())
            
            # Filtrar solo el día objetivo
            hourly_df['date_only'] = hourly_df['date'].dt.date
            target_date_only = pd.to_datetime(target_date).date()
            daily_df = hourly_df[hourly_df['date_only'] == target_date_only].copy()
            
            # Filtrar por hour_integer
            daily_df['hour'] = daily_df['date'].dt.hour
            matching_row = daily_df[daily_df['hour'] == row['hour_integer']]
            
            if not matching_row.empty:
                result_row = row.to_dict()
                for var in params["hourly"]:
                    result_row[f"weather_{var}"] = matching_row[var].values[0]
                result_row['hour_geo'] = matching_row['date_corregida'].dt.hour.values[0]
                result_row['alt'] = response.Elevation()
                results.append(result_row)
            else:
                print(f"No se encontró hora {row['hour_integer']} para fecha {target_date}")
        
        except Exception as e:
            print(f"Error procesando fila {index}: {str(e)}")
            continue

    a_predecir_completo = pd.DataFrame(results)

    return a_predecir_completo





def get_data_training(df):
    url = "https://historical-forecast-api.open-meteo.com/v1/forecast"
    results = []
    total_filas = len(df)  # Total de filas a procesar

    for index, row in df.iterrows():
        try:
            print(f"\nProcesando fila {index+1} de {total_filas} - {((index+1)/total_filas)*100:.1f}% completado")
            # Pausa aleatoria entre 1 y 3 segundos
            sleep_time = random.uniform(2, 5)
            print(f"Sleep time elegido: {(sleep_time):.1f} segundos")
            time.sleep(sleep_time)
            
            # Calcular rangos de fecha (día anterior y día posterior)
            current_date = pd.to_datetime(row['date'])
            start_date = (current_date - timedelta(days=1)).strftime('%Y-%m-%d')
            end_date = (current_date + timedelta(days=1)).strftime('%Y-%m-%d')
            target_date = current_date.strftime('%Y-%m-%d')
            
            params = {
                "latitude": row['lat'],
                "longitude": row['lon'],
                "start_date": start_date,
                "end_date": end_date,
                "hourly": ["temperature_2m","snow_depth", "relative_humidity_2m", "dew_point_2m", "apparent_temperature", "precipitation_probability", "precipitation", "rain", "showers", "snowfall", "weather_code", "pressure_msl", 
                           "surface_pressure", "cloud_cover", "cloud_cover_low", "cloud_cover_mid", "cloud_cover_high", "evapotranspiration", "visibility", "et0_fao_evapotranspiration", "vapour_pressure_deficit", "wind_speed_10m", "wind_speed_80m", 
                           "wind_speed_120m", "wind_speed_180m", "wind_direction_10m", "wind_direction_80m", "wind_direction_120m", "wind_direction_180m", "wind_gusts_10m", "temperature_80m", "temperature_120m", "temperature_180m", 
                           "soil_temperature_0cm", "soil_temperature_6cm", "soil_temperature_18cm", "soil_temperature_54cm", "soil_moisture_0_to_1cm", "soil_moisture_1_to_3cm", "soil_moisture_3_to_9cm", "soil_moisture_9_to_27cm", 
                           "soil_moisture_27_to_81cm", "uv_index", "uv_index_clear_sky", "is_day", "sunshine_duration", "wet_bulb_temperature_2m", "shortwave_radiation", "boundary_layer_height", "freezing_level_height", "convective_inhibition", 
                           "lifted_index", "cape", "total_column_integrated_water_vapour", "direct_radiation", "diffuse_radiation", "direct_normal_irradiance", "global_tilted_irradiance", "terrestrial_radiation", "terrestrial_radiation_instant", 
                           "global_tilted_irradiance_instant", "direct_normal_irradiance_instant", "diffuse_radiation_instant", "direct_radiation_instant", "shortwave_radiation_instant"],
                # "models": ["best_match", "ecmwf_aifs025_single", "ecmwf_ifs025", "cma_grapes_global", "bom_access_global", "kma_seamless", "kma_ldps", "kma_gdps", "gfs_seamless", "gfs_global", "gfs_graphcast025", "jma_seamless", 
                #         "jma_gsm", "icon_seamless", "icon_global", "gem_seamless", "gem_global", "meteofrance_seamless", "meteofrance_arpege_world", "knmi_seamless", "dmi_seamless", "ukmo_global_deterministic_10km", "ukmo_seamless"],
                "timezone": "auto"
            }
            
            # Solicitud a la API
            responses = openmeteo.weather_api(url, params=params)
            response = responses[0]
            
            # Procesar datos
            hourly = response.Hourly()
            hourly_data = {
                "date": pd.date_range(
                    start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                    end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                    freq=pd.Timedelta(seconds=hourly.Interval()),
                    inclusive="left"
                )
            }
            
            # Añadir variables
            for i, var_name in enumerate(params["hourly"]):
                var = hourly.Variables(i)
                hourly_data[var_name] = var.ValuesAsNumpy()
            
            hourly_df = pd.DataFrame(data=hourly_data)
            hourly_df['date_corregida'] = hourly_df['date'] + timedelta(seconds=response.UtcOffsetSeconds())
            
            # Filtrar solo el día objetivo
            hourly_df['date_only'] = hourly_df['date'].dt.date
            target_date_only = pd.to_datetime(target_date).date()
            daily_df = hourly_df[hourly_df['date_only'] == target_date_only].copy()
            
            # Filtrar por hour_integer
            daily_df['hour'] = daily_df['date'].dt.hour
            matching_row = daily_df[daily_df['hour'] == row['hour_integer']]
            
            if not matching_row.empty:
                result_row = row.to_dict()
                for var in params["hourly"]:
                    result_row[f"weather_{var}"] = matching_row[var].values[0]
                result_row['hour_geo'] = matching_row['date_corregida'].dt.hour.values[0]
                result_row['alt'] = response.Elevation()
                results.append(result_row)
            else:
                print(f"No se encontró hora {row['hour_integer']} para fecha {target_date}")
        
        except Exception as e:
            print(f"Error procesando fila {index}: {str(e)}")
            continue

    final_df = pd.DataFrame(results)

    return final_df