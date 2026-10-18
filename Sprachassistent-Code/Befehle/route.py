"""Befehl 13: Entfernung und Fahrdauer zwischen zwei Orten über die OpenRouteService-Cloud-API.

Benötigt einen API-Key (ORS_KEY in user_data.py). Ohne Key gibt der Befehl nur einen Hinweistext zurück.
"""
import openrouteservice
from Befehle.getparam import get_parameter
from user_data import ORS_KEY

if ORS_KEY  == None:
    print(r"Folge den Anweisungen in Sprachassistent-Code\user_data.py für OpenRouteService um diesen Befehl zu nutzen.")
    def route(start=None, ziel=None, vehicle="Auto"):
        """Ersatzfunktion ohne API-Key: gibt nur den Hinweistext zurück."""
        return r"Folge den Anweisungen in Sprachassistent-Code\user_data.py für OpenRouteService um diesen Befehl zu nutzen."
else:
    client = openrouteservice.Client(key=ORS_KEY)

    def koordinaten(ort):
        """Sucht die Koordinaten eines Ortes (erster Treffer der Geocoding-Suche).
        Rückgabe: Liste [Längengrad, Breitengrad], oder ein Text mit der Fehlermeldung, wenn der Ort nicht gefunden wurde oder ein Fehler auftrat.
        """
        try:
            return  openrouteservice.geocode.pelias_search(client, ort, size=1)["features"][0]["geometry"]["coordinates"]
        except IndexError:
            return str(ort) + " konnte ich nicht finden. Bitte wiederhole den Namen."
        except Exception as exception:
            print("Fehler koordinaten: " + str(exception))
            return "Fehler"

    def vehicle_to_keyword(vehicle = None):
        """Übersetzt den deutschen Fahrzeugnamen in das OpenRouteService-Profil (foot-walking, cycling-regular, driving-hgv, sonst driving-car)."""
        if vehicle == "Gehen":
            return "foot-walking"
        elif vehicle == "Fahrrad":
            return "cycling-regular"
        elif vehicle == "LKW":
            return "driving-hgv"
        else: #Auto als Standard-Fortbewegungsmittel
            return "driving-car"

    def route(start=None, ziel=None, vehicle="Auto"):
        """Befehl 13: Berechnet Distanz und Dauer zwischen Start und Ziel und gibt sie als Satz zurück.

        Parameter:
            start, ziel: Orte (str). Fehlt einer, wird per get_parameter nachgefragt; wird ein Ort nicht gefunden, wird der Name erneut abgefragt.
            vehicle: «Auto» (Standard), «Gehen», «Fahrrad» oder «LKW»; wirkt sich auf die Formulierung der Antwort aus.
        """
        if vehicle == None:
            vehicle = "Auto"
        if start == None:
            return route(get_parameter("Was ist der Startort?"), ziel, vehicle)
        if ziel == None:
            return route(start, get_parameter("Was ist der Zielort?"), vehicle)
        coords = (koordinaten(start),koordinaten(ziel))
        if not isinstance(coords[0], list):
            return route(get_parameter(coords[0]), ziel, vehicle)
        if not isinstance(coords[1], list):
            return route(start, get_parameter(coords[1]), vehicle)
        routes = client.directions(coords, profile=vehicle_to_keyword(vehicle))
        Distanz =routes["routes"][0]["summary"]["distance"]
        Zeit = routes["routes"][0]["summary"]["duration"]
        time_stunden = int(Zeit // 3600)
        time_minuten = int((Zeit % 3600) // 60)

        stunden_text = "Stunde" if time_stunden == 1 else "Stunden"
        minuten_text = "Minute" if time_minuten == 1 else "Minuten"
        if vehicle == "Gehen":
            part = "Zu Fuss"
        else:
            part = "Mit dem " + str(vehicle)
        if time_stunden:
            return (
                f"Von {start} nach {ziel} sind es etwa {round(Distanz/1000, 1)} Kilometer. " + part +  f" brauchst du ungefähr {time_stunden} {stunden_text} und {time_minuten} {minuten_text}."
            )
        else:
            return (
                f"Von {start} nach {ziel} sind es etwa {round(Distanz/1000, 1)} Kilometer. " + part + f" brauchst du ungefähr {time_minuten} {minuten_text}."
            )

