from functools import lru_cache
import datetime as dt
import urllib.parse
import urllib.request
import urllib.error
import json


def get_forecast(latitude, longitude):
    """Función para obtener el pronóstico de las siguientes 8 horas para la
    ubicación espicificada. Toma como argumentos una latitud (-90, 90) y una
    longitud (-180, 180) WSG84. El pronóstico es una lista de diccionarios con
    las llaves: time, temperature, humidity y precipitation.
    """
    if (time_now := dt.datetime.now()).minute >= 45:
        time_now += dt.timedelta(hours=1)
    time_now = time_now.replace(minute=0, second=0, microsecond=0)
    return get_forecast_cached(latitude, longitude, hash(time_now))


@lru_cache(maxsize=512)
def get_forecast_cached(latitude, longitude, time_hash):
    """Función para obtener un pronóstico del clima usando el API Open-Meteo.
    Toma como argumentos una latitud, longitud y un hash que sirve para
    almacenar resultados en un caché. Retorna una lista de diccionarios con
    el pronóstico de las siguientes ocho horas para la ubicación especificada.
    El caché es un caché lru, la estrategia tomada en este módulo es usar un
    hash basado en la hora de tal forma que el resultado para una ubicación
    es válido durante los primeros 45 minutos de la hora en la que se obtuvo.
    """
    time_fmt = "%Y-%m-%dT%H:%M"
    url = "https://api.open-meteo.com/v1/forecast"
    data = {"latitude": latitude,
            "longitude": longitude,
            "forecast_days": 2,
            "timezone": "auto",
            "hourly":
            "temperature_2m,relativehumidity_2m,precipitation_probability",
            "current_weather": "true"}

    def get_json(data):
        data = urllib.parse.urlencode(data)
        with urllib.request.urlopen(url + "?" + data) as response:
            weather_data = response.read()
        return json.loads(weather_data)

    def extract_forecast(weather_data):
        time_now = dt.datetime.strptime(
            weather_data["current_weather"]["time"], time_fmt
        )
        if time_now.minute >= 45:
            time_now += dt.timedelta(hours=1)
        time_now = time_now.replace(minute=0)
        hw = weather_data["hourly"]
        idx = hw["time"].index(time_now.strftime(time_fmt))
        forecast = []
        for i in range(idx, idx + 8):
            forecast.append({
                "time": time_now.strftime("%d-%m %H:%M"),
                "temperature": hw["temperature_2m"][i],
                "humidity": hw["relativehumidity_2m"][i],
                "precipitation": hw["precipitation_probability"][i]
            })
            time_now += dt.timedelta(hours=1)
        return forecast

    return extract_forecast(get_json(data))
