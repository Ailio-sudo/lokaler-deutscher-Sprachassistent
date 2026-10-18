"""Befehl 26: Aktuelles Wetter einer Stadt über die Open-Meteo-Schnittstellen (Geocoding und Vorhersage, Internet nötig)."""
import requests
from user_data import STANDARD_STADT

if STANDARD_STADT == None:
    print("Lege die persönliche Standard Stadt fest in user_data.")
    print("Da keine Festgelegt ist wird Berlin genommen")
    STANDARD_STADT = "Berlin"

def is_rain(weathercode):
    """Gibt True zurück, wenn der Wettercode (WMO-Code) Regen bedeutet (Codes 51, 53, 55, 61, 63, 65, 80, 81, 82)."""
    rain_codes = [51, 53, 55, 61, 63, 65, 80, 81, 82]
    return weathercode in rain_codes

def get_weather(city = STANDARD_STADT):
    """Befehl 26: Gibt Temperatur, Wind, Regen und Luftfeuchtigkeit der Stadt als Satz zurück.

    Parameter:
        city: Stadtname. Vorgabe ist STANDARD_STADT aus user_data.py.
    Rückgabe: Satz mit den Wetterdaten oder «Stadt nicht gefunden».
    Bekanntes Problem (siehe README, Abschnitt «Bekannte Probleme»): Die Funktion weist STANDARD_STADT innerhalb der Funktion einen Wert zu. Dadurch ist der Name dort lokal,
    und schon die Prüfung «if STANDARD_STADT == None» löst einen UnboundLocalError aus (so getestet).
    """

    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
    geo_data = requests.get(geo_url).json()

    if "results" not in geo_data:
        return "Stadt nicht gefunden"

    lat = geo_data["results"][0]["latitude"]
    lon = geo_data["results"][0]["longitude"]
    name = geo_data["results"][0]["name"]

    weather_url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current_weather=true"
        "&hourly=relative_humidity_2m"
        "&timezone=auto"
    )

    weather_data = requests.get(weather_url).json()

    current = weather_data["current_weather"]
    humidity = str(weather_data["hourly"]["relative_humidity_2m"][0])

    rain = is_rain(current["weathercode"])

    temperature = str(current["temperature"])
    windspeed = str(current["windspeed"])

    regen_text = "Es regnet" if rain else "Es regnet nicht"

    return f"In {name} sind es {temperature.replace('.', ',')} Grad Celsius. Es herrschen Windgeschwindigkeiten von {windspeed.replace('.', ',')} Kilometern pro Stunde. {regen_text} und die Feuchtigkeit beträgt {humidity.replace('.', ',')} Prozent."

if __name__ == "__main__":
    print(get_weather("Wetzikon"))
