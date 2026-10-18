"""Hilfsfunktion für Rückfragen: Wenn einem Befehl ein Parameter fehlt, fragt er den Nutzer per Sprache."""
from ASR import Record
from TextToSpeech import TTS

def get_parameter(frage):
    """Stellt dem Nutzer eine Frage per Sprachausgabe und gibt die gesprochene Antwort als Text zurück.

    Parameter:
        frage: Die Frage, die vorgelesen wird (str).
    Rückgabe: Der erkannte Text (str) oder None, wenn nichts erkannt wurde (siehe ASR.Record).
    """
    TTS(frage)
    ausgabe = Record()
    print("Erkannter Parameter: ", ausgabe)
    return ausgabe
