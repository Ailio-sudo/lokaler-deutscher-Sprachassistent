"""Befehle 5-7: Einkaufsliste in der Datei einkaufsliste.json (im selben Ordner).

Aufbau der JSON-Datei: {"einkaufsliste": [aktuelle Artikel], "einkaufslisten_alt": [frühere Listen]}.
Beim Leeren wird die aktuelle Liste zuerst nach «einkaufslisten_alt» kopiert (Sicherung).
"""
import json
from Befehle.getparam import get_parameter
from pathlib import Path

einkaufsliste_path = Path(Path(__file__).resolve().parent/"einkaufsliste.json")

def einkaufsliste_add(item=None):
    """Befehl 5: Fügt einen Artikel an die aktuelle Einkaufsliste an.

    Parameter:
        item: Der Artikel (str). Ist er None, soll per get_parameter nachgefragt werden.
    Rückgabe: Bestätigungssatz.
    Bekanntes Problem (siehe README, Abschnitt «Bekannte Probleme»): Der Import von get_parameter ist in dieser Datei auskommentiert, und beim Nachfragen
    wird der Rückgabesatz der inneren Funktion als Artikel gespeichert.
    """
    if item == None:
        return einkaufsliste_add(get_parameter("Was willst du zur Einkaufsliste hinzufügen?"))
    with open(einkaufsliste_path, "r") as file:
        einkaufsliste = json.load(file)
    einkaufsliste["einkaufsliste"].append(item)
    with open(einkaufsliste_path, "w") as file:
        json.dump(einkaufsliste, file, indent=4)
    return f"Ich habe {item} zur Einkaufsliste hinzugefügt."

def einkaufsliste_lesen():
    """Befehl 6: Liest die aktuelle Einkaufsliste als Satz vor («Auf der Einkaufsliste sind A, B und C»).
    Rückgabe: Text; bei leerer Liste «Die Einkaufsliste ist leer».
    """
    with open(einkaufsliste_path, "r") as file:
        einkaufsliste = json.load(file)
    if len(einkaufsliste["einkaufsliste"]) == 0:
        return "Die Einkaufsliste ist leer"
    elif len(einkaufsliste["einkaufsliste"]) == 1:
        return "Auf der Einkaufsliste ist "+ einkaufsliste["einkaufsliste"][0]+ "."
    else:
        ausgabe = "Auf der Einkaufsliste sind "
        for produkt in einkaufsliste["einkaufsliste"][:-2]:
            ausgabe += str(produkt + ", ")
        ausgabe += str(einkaufsliste["einkaufsliste"][-2] + " und " + einkaufsliste["einkaufsliste"][-1])
        return ausgabe

def einkaufsliste_neu():
    """Befehl 7: Leert die Einkaufsliste. Die bisherige Liste wird vorher als Sicherung zu «einkaufslisten_alt» kopiert.
    Rückgabe: Bestätigungssatz.
    """
    with open(einkaufsliste_path, "r") as file:
        einkaufsliste = json.load(file)
    einkaufsliste["einkaufslisten_alt"].append(einkaufsliste["einkaufsliste"].copy())
    einkaufsliste["einkaufsliste"].clear()
    with open(einkaufsliste_path, "w") as file:
        json.dump(einkaufsliste, file, indent=4)
    return "Ich habe die Einkaufsliste geleert."

def alte_einkaufslisten_löschen():
    """Löscht die gesicherten alten Einkaufslisten dauerhaft, aber erst nach Bestätigung mit «y» in der Konsole.
    Gehört nicht zu den 27 Sprachbefehlen, sondern ist eine Hilfsfunktion für die Pflege der Datei.
    """
    if input("Bist du sicher das du die Alten Einkaufslisten löschen willst (y/n)") == "y":
        with open(einkaufsliste_path, "r") as file:
            einkaufsliste = json.load(file)
        einkaufsliste["einkaufslisten_alt"].clear()
        with open(einkaufsliste_path, "w") as file:
            json.dump(einkaufsliste, file, indent=4)
    else:
        print("Die Alten Einkaufslisten wurden NICHT gelöscht")


if __name__ == "__main__":
    einkaufsliste_add("Chips")
    print(einkaufsliste_lesen())
