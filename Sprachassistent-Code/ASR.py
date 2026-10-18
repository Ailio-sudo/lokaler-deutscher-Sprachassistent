"""Spracherkennung (ASR): Wake Word, Aufnahme und Transkription.

Ablauf einer Anfrage (siehe wait_and_Record):
  1. wait_for_wakeword(): hört fortlaufend am Mikrofon mit und wartet auf «Hey Jarvis» (openwakeword).
  2. listening(): spielt einen Signalton ab.
  3. Record(): nimmt auf, bis eine Sprechpause erkannt wird (speech_recognition),
     und transkribiert die Aufnahme mit faster-whisper (Deutsch).

Wichtig: Beim Import dieser Datei werden das Whisper-Modell und das Wake-Word-Modell geladen
und der Mikrofon-Stream geöffnet. Das kann einige Sekunden dauern.
Das Mikrofon wird über MICROPHONE_INDEX in user_data.py gewählt. Ist dort None eingetragen,
wird beim ersten Start nachgefragt und die Auswahl in user_data.py gespeichert.
"""
import os
import numpy as numpy
import pyaudio
# Unterdrückt die Willkommensmeldung von pygame in der Konsole
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame
from pathlib import Path
from user_data import MICROPHONE_INDEX
print("CPU für Speech To Text")
from faster_whisper import WhisperModel
# Transkriptionsmodell (faster-whisper): Modell «small», Ausführung auf der CPU mit int8-Quantisierung
model = WhisperModel("small", device="cpu", compute_type="int8")


import queue
# Nachrichten an die grafische Oberfläche; sprachassistent.py liest sie aus und zeigt sie an
gui_queue = queue.Queue()
def melde(typ, *daten): #Wird genutzt um Kommunikation zwischen GUI zu ermöglichen. Dadurch kann das GUI eine animation Abspielen wenn beispielsweise Transkribiert wird
    """Schickt eine Nachricht an die grafische Oberfläche (über gui_queue).

    Parameter:
        typ: Art der Nachricht, z. B. "zustand" (die GUI zeigt dann die passende Animation).
        *daten: weitere Werte der Nachricht, z. B. der Name des Zustands.
    """
    gui_queue.put((typ, *daten))

print("Lade Speech Recognition")
import speech_recognition as sr
print("Lade Wakeword...")
import openwakeword
from openwakeword.model import Model

# OpenWakeWord-Modelle herunterladen
openwakeword.utils.download_models(model_names=["hey_jarvis"])

# "Hey Jarvis"-Modell laden r"models\hey_venno.onnx"
oww_model = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")

# PyAudio-Instanz für den Mikrofon-Zugriff (sprachassistent.py ruft beim Beenden pyaudio_PyAudio.terminate() auf)
pyaudio_PyAudio = pyaudio.PyAudio()

print("Öffne PyAudio Stream")



if MICROPHONE_INDEX == None: #Mikrofon Index abfragen wenn noch nicht gespeichert in user data.py
    for i in range(pyaudio_PyAudio.get_device_count()):
        print(
            f"Index: {i}, "
            f"Name: {pyaudio_PyAudio.get_device_info_by_index(i)['name']}, "
        )
    while True:
        try:
            audio_device = int(input("Das Mikrofon mit welchem Index willst du verwenden? (Kann später in user_data.py geändert werden)"))

            # Mikrofon Index in user_data.py speichern
            user_data_path = Path(__file__).resolve().parent/"user_data.py"
            with open(user_data_path, "r", encoding="utf-8") as file:
                user_data = file.read()
            user_data = user_data.replace("MICROPHONE_INDEX = None", f"MICROPHONE_INDEX = {audio_device}")
            with open(user_data_path, "w", encoding="utf-8") as file:
                file.write(user_data)
            print("Für zukünftige Nutzung gespeichert!")
            break
        except Exception as e:
            print("Bitte nur den Index des Mikrofons angeben.")
            #print(e)
else:
    print(f"Nutze Mikrofon mit Index {MICROPHONE_INDEX}")
    audio_device = MICROPHONE_INDEX


#Audiostream öffnen und Mikrofon vorbereiten
# Stream für die Wake-Word-Erkennung: 16 kHz, Mono, 16 Bit; 1280 Samples (80 ms) pro Lesevorgang
stream = pyaudio_PyAudio.open(
    rate=16000,
    channels=1,
    format=pyaudio.paInt16,
    input=True,
    input_device_index=audio_device,
    frames_per_buffer=1280
)
# Mikrofon für die Aufnahme der eigentlichen Anfrage (speech_recognition, ebenfalls 16 kHz)
sr_Microphone = sr.Microphone(device_index=audio_device, sample_rate=16000)

def listening():
    """Spielt den Signalton (sounds/listening.mp3) ab, damit der Nutzer weiss, dass der Assistent zuhört."""
    # Signalton nach Wakeword-Erkennung
    pygame.init()
    pygame.mixer.music.load(str(Path(__file__).resolve().parent / "sounds" / "listening.mp3"))
    pygame.mixer.music.set_volume(0.6)
    pygame.mixer.music.play()

def Record():
    """Nimmt eine Äusserung auf und wandelt sie in Text um.

    Die Aufnahme endet automatisch nach einer Sprechpause (pause_threshold). Sie wird als
    sounds/aufnahme.wav gespeichert (wird bei jeder Aufnahme überschrieben) und mit faster-whisper
    auf Deutsch transkribiert. Die Funktion blockiert, bis die Aufnahme beendet und transkribiert ist.
    Sie wird auch für Rückfragen der Befehle verwendet (siehe Befehle/getparam.py).

    Rückgabe:
        Den erkannten Text (str) oder None, wenn kein Text erkannt wurde.
    """
    # Sprache aufnehmen und erkennen
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 1.5 # Pause zwischen Wörtern

    recognizer.non_speaking_duration = 1.5 # Aufnahmezeit nachdem der Nutzer aufhörte zu sprechen

    # Zuhören solange Nutzer spricht
    with sr_Microphone as microphone:
        audio = recognizer.listen(microphone)

    #Audio speichern
    aufnahme_path = Path(__file__).resolve().parent/"sounds/aufnahme.wav"
    with open(aufnahme_path, "wb") as aufnahme:
        aufnahme.write(audio.get_wav_data())
    melde("zustand", "transkribieren") # Zustand dem GUI melden
    print("Transkribiere")
    # Sprache transkribieren
    segments, info = model.transcribe(aufnahme_path, language="de")
    text = " ".join(segment.text.strip() for segment in list(segments))
    return text if text.strip() != "" else None


def wait_for_wakeword():
    """Blockiert, bis das Wake Word «Hey Jarvis» erkannt wird.

    Liest dazu fortlaufend Audio-Blöcke (1280 Samples, 80 ms bei 16 kHz) vom Mikrofon und übergibt sie
    dem Wake-Word-Modell. Überschreitet der Score den Schwellenwert 0.28, kehrt die Funktion zurück.
    """
    oww_model.reset() # Wakeword-Score zurücksetzen
    while True:
        # Mikrofon-Audio auslesen
        audio = numpy.frombuffer(stream.read(1280), dtype=numpy.int16)
        # Wakeword prediction abgeben
        prediction = oww_model.predict(audio)["hey_jarvis"]
        # Wakeword-Schwellenwert
        if prediction > 0.28:
            print("Wake Word erkannt:", prediction)
            return

def wait_and_Record():
    """Wartet auf das Wake Word, gibt den Signalton aus und nimmt danach die Anfrage auf.

    Rückgabe:
        Den transkribierten Text (str) oder None, wenn kein Text erkannt wurde (siehe Record).
    """
    print("...running...")
    wait_for_wakeword()
    melde("zustand", "zuhoeren") # Zustand dem GUI melden
    listening() # Signalton
    return Record() # Sprache aufnehmen und transkribieren

# Direkter Start der Datei: nur Wake Word und Transkription testen (Ergebnis wird ausgegeben)
if __name__ == "__main__":
    # Hauptschleife
    while True:
        print(wait_and_Record())

