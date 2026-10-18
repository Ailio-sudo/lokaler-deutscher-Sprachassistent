"""Befehl 12: Zu einer Frage im Internet recherchieren und die Antwort von einem lokalen Sprachmodell zusammenfassen lassen.

Die Suche läuft über DuckDuckGo (Paket ddgs), die Zusammenfassung über Ollama mit dem Modell MODELL_SMALL aus user_data.py.
"""
from ddgs import DDGS
import ollama
import time
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from user_data import MODELL_SMALL
MODEL = MODELL_SMALL
def recherchiere(frage, max_results=15):
    """Sucht im Internet nach der Frage.

    Parameter:
        frage: Suchanfrage (str).
        max_results: Maximale Anzahl Treffer (Standard 15).
    Rückgabe: Liste von Treffern (Dictionaries mit «title» und «body»). Bei Fehlern wird bis zu 5-mal mit 0.5 s
    Pause neu versucht; danach wird der Text «Ich habe dazu nichts gefunden.» statt einer Liste zurückgegeben.
    """
    for i in range(5):
        try:
            with DDGS() as ddgs:
                return list(ddgs.text(frage, max_results=max_results))
        except:
            print("Nichts gefunden warte 0.5 Sekunden - Try ", i)
            time.sleep(0.5)
    print("Keine Quellen Gefunden")
    return False


def fasse_zusammen(frage, treffer, model=MODEL):
    """Lässt das Sprachmodell die Frage anhand der Treffer beantworten.

    Parameter:
        frage: Die Frage des Nutzers.
        treffer: Liste der Suchtreffer (siehe recherchiere).
        model: Ollama-Modell. Bei None wird ein bereits geladenes Modell gewählt (gemma4:e4b, sonst qwen2.5:1.5b-instruct).
    Der Prompt verlangt eine kurze, gesprochene Antwort auf Deutsch, die nur auf den gegebenen Quellen beruht.
    Rückgabe: Die Antwort als Text.
    """
    if model == None:
        running_models = ollama.ps()
        #print("Running Models: ", running_models["models"])
        if "gemma4:e4b" in str(running_models["models"]):
            model = "gemma4:e4b"
            print("Chose gemma4:e4b")
        elif "qwen2.5:1.5b-instruct" in str(running_models["models"]):
            model = "qwen2.5:1.5b-instruct"
            print("Chose qwen2.5:1.5b-instruct")
        else:
            print("Fehler: Kein Modell läuft - Wählt " + MODEL)
            model = "qwen2.5:1.5b-instruct"
            print("Chose qwen2.5:1.5b-instruct")
    kontext = "\n\n".join(f"Quelle: {t['title']}\n{t['body']}" for t in treffer)

    prompt = f"""
Beantworte die folgende Frage auf Deutsch, kurz und in natürlicher
gesprochener Sprache (max. 2-3 Sätze).

Verwende ausschließlich die Informationen aus den gegebenen Quellen.
Erfinde keine Informationen. Sind in den Quellen keine Informationen zu finden, sage "Ich konnte dazu keine nützlichen Informationen finden", beziehe dich nie direkt auf die Quellen in deiner Antwort.

Frage:
{frage}

Informationen:
{kontext}

Antwort:
"""

    response = ollama.chat(
        model=model,
        messages=[{"role": "user",
                "content": prompt}],
        think=False if model == MODELL_SMALL else True,
        keep_alive=-1,
        options={"temperature": 0,
            "top_p": 0.1,
            "repeat_penalty": 1.1,
            "num_predict": 1280})
    return response["message"]["content"].strip()


def recherchieren(frage):
    """Befehl 12: Recherchiert zum Thema und gibt eine kurze Antwort zurück.

    Parameter:
        frage: Thema bzw. ganze Frage des Nutzers.
    Rückgabe: Antworttext des Sprachmodells oder eine Meldung, wenn nichts gefunden wurde.
    Bekanntes Problem (siehe README, Abschnitt «Bekannte Probleme»): Liefert recherchiere() den Text statt einer Liste, wird dieser Text wie eine Trefferliste behandelt.
    """
    print("Frage:", frage)
    treffer = recherchiere(frage)
    if not treffer:
        return "Dazu konnte ich leider nichts finden."
    return fasse_zusammen(frage, treffer)


