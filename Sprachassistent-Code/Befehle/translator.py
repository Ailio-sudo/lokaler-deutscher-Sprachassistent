"""Befehl 24: Text übersetzen (Bibliotheken deep_translator und langdetect)."""
from deep_translator import GoogleTranslator
from langdetect import detect
import pycountry
from Befehle.getparam import get_parameter
def lang_name(code):
    """Gibt den deutschen Namen einer Sprache zurück (z. B. «en» -> «Englisch»).
    Der englische Sprachname aus pycountry wird mit GoogleTranslator ins Deutsche übersetzt.
    Bekanntes Problem (siehe README, Abschnitt «Bekannte Probleme»): Ist der Sprachcode unbekannt, tritt vor der Prüfung auf None ein Fehler auf.
    """
    lang = pycountry.languages.get(alpha_2=code)

    deutschlang = GoogleTranslator(
        source="en",
        target="de"
    ).translate(lang.name)
    return deutschlang if lang else code

def translate(text = None, target_lang="de"):
    """Befehl 24: Übersetzt einen Text.

    Parameter:
        text: Zu übersetzender Text. Ist er None, wird per get_parameter nachgefragt.
        target_lang: Zielsprache als Sprachcode (Standard «de»).
    Die Ausgangssprache wird mit langdetect erkannt; die Übersetzung erfolgt mit deep_translator.GoogleTranslator.
    Rückgabe: Satz «Auf <Sprache> heisst das: <Übersetzung>».
    """
    if text == None:
        return translate(get_parameter("Was möchtest du übersetzen"), target_lang)
    source_lang = detect(text)

    translated = GoogleTranslator(
        source=source_lang,
        target=target_lang
    ).translate(text)

    return f"Auf {lang_name(target_lang)} heisst das: {translated}"
if __name__ == "__main__":
    print(translate("Wat te dragen?"))
