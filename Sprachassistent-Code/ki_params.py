"""Parameter-Extraktion mit einem kleinen lokalen Sprachmodell (Ollama, Modell MODELL_SMALL aus user_data.py).

Die Intent-Erkennungssysteme Keyword Matching, TF-IDF, Word Embeddings und Sentence Embeddings bestimmen nur die
Befehlsnummer. Die dazugehörigen Parameter (z. B. Ort, Zahl, Songtitel) werden hier aus dem Satz geholt.
Das KI-System (systems/ki_gemma.py) liefert die Parameter dagegen selbst mit.
"""
import json
import ollama
import zahlwort2num
from user_data import MODELL_SMALL as MODELL


def ersetze_zahlwoerter(text):
    """Ersetzt Zahlwörter durch Ziffern (z. B. «fünf» -> 5).

    Hintergrund (laut Kommentar im Code): Kleine Sprachmodelle haben Schwierigkeiten mit Zahlwörtern oder geben
    das Zahlwort statt der Zahl als Parameter zurück. Wörter, die sich nicht umwandeln lassen, bleiben unverändert.
    Rückgabe: der Text mit einem Leerzeichen nach jedem Wort.
    """
    # Zahlwörter zu Zahlen umwandeln (zwei -> 2)
    # Da kleine KI-Modelle schwierigkeiten haben oder das Zahlwort statt der Zahl als Parameter zurückgeben
    splitten = []
    for wort in text.split():
        try:
            splitten.append(zahlwort2num.convert(wort))
        except Exception:
            splitten.append(wort)
    output = ""
    for wort in splitten:
        output += str(wort) + " "
    return output


# Beschreibung der Befehle, deren Parameter per Sprachmodell extrahiert werden.
# Schlüssel = Befehlsnummer. Pro Befehl:
#   "system_prompt": Anweisung an das Modell (Aufgabe, Regeln, Beispiele)
#   "schema":        JSON-Schema, das die Form der Antwort vorgibt
#   "keys":          Namen der Parameter in der Reihenfolge, in der sie an den Befehl weitergegeben werden
befehle_mit_parameter = {

    1: {
        "system_prompt": (
            "You extract exactly one parameter from a German voice command "
            "(speech-to-text output, may contain transcription errors).\n\n"
            "TASK: Determine by how many percentage points the screen "
            "brightness should CHANGE, relative to its current level.\n\n"
            "RULES:\n"
            "- Return an integer between -100 and 100 (never 0).\n"
            "- Brighter / heller -> positive value.\n"
            "- Darker / dunkler -> negative value.\n"
            "- Always a whole percentage point, never a decimal.\n"
            "- If no number is given: use 10 for brighter, -10 for darker.\n\n"
            "EXAMPLES:\n"
            "Input: \"mach den bildschirm heller\" -> {\"wert\": 10}\n"
            "Input: \"bildschirm um 20 prozent dunkler machen\" -> {\"wert\": -20}\n"
            "Input: \"erhöhe die helligkeit um 5\" -> {\"wert\": 5}\n"
            "Input: \"mach 1 dunkler\" -> {\"wert\": -1}\n"
        ),
        "schema": {
            "type": "object",
            "properties": {"wert": {"type": "integer", "minimum": -100, "maximum": 100}},
            "required": ["wert"],
        },
        "keys": ["wert"],
    },

    3: {
        "system_prompt": (
            "You extract exactly one parameter from a German voice command "
            "(speech-to-text output, may contain transcription errors).\n\n"
            "TASK: Determine the ABSOLUTE brightness level the user wants to "
            "set the screen to, in percent (0-100).\n\n"
            "RULES:\n"
            "- Return an integer between 0 and 100.\n"
            "- \"maximum\"/\"voll\" -> 100, \"minimum\"/\"aus\" -> 0.\n"
            "- If no specific level is mentioned, return null. Never guess.\n\n"
            "EXAMPLES:\n"
            "Input: \"stelle die helligkeit auf 50 prozent\" -> {\"wert\": 50}\n"
            "Input: \"helligkeit auf maximum\" -> {\"wert\": 100}\n"
            "Input: \"mach den bildschirm ganz dunkel\" -> {\"wert\": 0}\n"
            "Input: \"ändere die helligkeit\" -> {\"wert\": null}\n"
        ),
        "schema": {
            "type": "object",
            "properties": {"wert": {"type": ["integer", "null"], "minimum": 0, "maximum": 100}},
            "required": ["wert"],
        },
        "keys": ["wert"],
    },

    5: {
        "system_prompt": (
            "You extract exactly one parameter from a German voice command "
            "(speech-to-text output, may contain transcription errors).\n\n"
            "TASK: Extract the single item the user wants to add to their "
            "shopping list.\n\n"
            "RULES:\n"
            "- Return the item exactly as named, capitalised like a German "
            "noun (first letter uppercase).\n"
            "- If several items are mentioned, return only the first one.\n"
            "- If no item is recognisable, return null.\n\n"
            "EXAMPLES:\n"
            "Input: \"füge milch zur einkaufsliste hinzu\" -> {\"artikel\": \"Milch\"}\n"
            "Input: \"schreib äpfel auf die liste\" -> {\"artikel\": \"Äpfel\"}\n"
            "Input: \"öffne die einkaufsliste\" -> {\"artikel\": null}\n"
        ),
        "schema": {
            "type": "object",
            "properties": {"artikel": {"type": ["string", "null"]}},
            "required": ["artikel"],
        },
        "keys": ["artikel"],
    },

    8: {
        "system_prompt": (
            "You extract exactly one parameter from a German voice command "
            "(speech-to-text output, may contain transcription errors).\n\n"
            "TASK: Determine by how many percentage points the volume "
            "should CHANGE, relative to its current level.\n\n"
            "RULES:\n"
            "- Return an integer between -100 and 100 (never 0).\n"
            "- Louder / lauter -> positive value.\n"
            "- Quieter / leiser -> negative value.\n"
            "- Always a whole percentage point, never a decimal.\n"
            "- If no number is given: use 10 for louder, -10 for quieter.\n\n"
            "EXAMPLES:\n"
            "Input: \"mach lauter\" -> {\"wert\": 10}\n"
            "Input: \"lautstärke um 15 prozent leiser\" -> {\"wert\": -15}\n"
            "Input: \"mach 1 leiser\" -> {\"wert\": -1}\n"
        ),
        "schema": {
            "type": "object",
            "properties": {"wert": {"type": "integer", "minimum": -100, "maximum": 100}},
            "required": ["wert"],
        },
        "keys": ["wert"],
    },

    10: {
        "system_prompt": (
            "You extract exactly one parameter from a German voice command "
            "(speech-to-text output, may contain transcription errors).\n\n"
            "TASK: Determine the ABSOLUTE volume level the user wants, in "
            "percent (0-100).\n\n"
            "RULES:\n"
            "- Return an integer between 0 and 100.\n"
            "- \"maximum\"/\"voll\" -> 100, \"stumm\"/\"aus\" -> 0.\n"
            "- If no specific level is mentioned, return null. Never guess.\n\n"
            "EXAMPLES:\n"
            "Input: \"stelle die lautstärke auf 30\" -> {\"wert\": 30}\n"
            "Input: \"schalte auf stumm\" -> {\"wert\": 0}\n"
            "Input: \"ändere die lautstärke\" -> {\"wert\": null}\n"
        ),
        "schema": {
            "type": "object",
            "properties": {"wert": {"type": ["integer", "null"], "minimum": 0, "maximum": 100}},
            "required": ["wert"],
        },
        "keys": ["wert"],
    },

    11: {
        "system_prompt": (
            "You extract exactly one parameter from a German voice command "
            "(speech-to-text output, may contain transcription errors).\n\n"
            "TASK: Extract how many news items the user wants to see.\n\n"
            "RULES:\n"
            "- Return a positive integer if a number is mentioned.\n"
            "- If no number is mentioned, return null.\n\n"
            "EXAMPLES:\n"
            "Input: \"zeig mir 5 nachrichten\" -> {\"anzahl\": 5}\n"
            "Input: \"was gibt es neues\" -> {\"anzahl\": null}\n"
            "Input: \"gib mir die drei wichtigsten news\" -> {\"anzahl\": 3}\n"
        ),
        "schema": {
            "type": "object",
            "properties": {"anzahl": {"type": ["integer", "null"], "minimum": 1}},
            "required": ["anzahl"],
        },
        "keys": ["anzahl"],
    },

    13: {
        "system_prompt": (
            "You extract three parameters from a German voice command about "
            "navigation (speech-to-text output, may contain transcription "
            "errors).\n\n"
            "TASK: Extract the starting point, the destination, and the "
            "mode of transport.\n\n"
            "RULES:\n"
            "- \"start\": the place the route begins at. null if not "
            "mentioned (in that case the current location is used later).\n"
            "- \"ziel\": the destination place. null if not mentioned.\n"
            "- \"fortbewegungsmittel\": exactly one of \"Auto\", \"Fahrrad\", "
            "\"Gehen\", \"LKW\". If not mentioned, default to \"Auto\".\n\n"
            "EXAMPLES:\n"
            "Input: \"navigiere von zürich nach bern mit dem auto\" -> "
            "{\"start\": \"Zürich\", \"ziel\": \"Bern\", \"fortbewegungsmittel\": \"Auto\"}\n"
            "Input: \"wie komme ich zu fuss zum bahnhof\" -> "
            "{\"start\": null, \"ziel\": \"Bahnhof\", \"fortbewegungsmittel\": \"Gehen\"}\n"
            "Input: \"route zum flughafen\" -> "
            "{\"start\": null, \"ziel\": \"Flughafen\", \"fortbewegungsmittel\": \"Auto\"}\n"
        ),
        "schema": {
            "type": "object",
            "properties": {
                "start": {"type": ["string", "null"]},
                "ziel": {"type": ["string", "null"]},
                "fortbewegungsmittel": {"type": "string", "enum": ["Auto", "Fahrrad", "Gehen", "LKW"]},
            },
            "required": ["start", "ziel", "fortbewegungsmittel"],
        },
        "keys": ["start", "ziel", "fortbewegungsmittel"],
    },

    15: {
        "system_prompt": (
            "You extract exactly one parameter from a German voice command "
            "(speech-to-text output, may contain transcription errors).\n\n"
            "TASK: Extract the exact file name the user wants to search "
            "for.\n\n"
            "RULES:\n"
            "- Copy the file name EXACTLY as it appears in the text, "
            "including its extension if one is mentioned (e.g. \".pdf\").\n"
            "- Do not translate, correct, or reformat it.\n"
            "- If no file name is recognisable, return null.\n\n"
            "EXAMPLES:\n"
            "Input: \"suche die datei rechnung_2024.pdf\" -> {\"dateiname\": \"rechnung_2024.pdf\"}\n"
            "Input: \"finde urlaubsfoto\" -> {\"dateiname\": \"urlaubsfoto\"}\n"
            "Input: \"such mal eine datei\" -> {\"dateiname\": null}\n"
        ),
        "schema": {
            "type": "object",
            "properties": {"dateiname": {"type": ["string", "null"]}},
            "required": ["dateiname"],
        },
        "keys": ["dateiname"],
    },

    19: {
        "system_prompt": (
            "You extract two parameters from a German voice command about "
            "playing music (speech-to-text output, may contain "
            "transcriptobjection errors).\n\n"
            "TASK: Extract the song title and the artist name.\n\n"
            "RULES:\n"
            "- \"song\": the title of the song, exactly as mentioned. null "
            "if not mentioned.\n"
            "- \"künstler\": the artist/band name, exactly as mentioned. "
            "null if not mentioned.\n\n"
            "EXAMPLES:\n"
            "Input: \"spiele shape of you von ed sheeran\" -> "
            "{\"song\": \"Shape of You\", \"künstler\": \"Ed Sheeran\"}\n"
            "Input: \"spiel was von coldplay\" -> "
            "{\"song\": null, \"künstler\": \"Coldplay\"}\n"
            "Input: \"spiel bohemian rhapsody\" -> "
            "{\"song\": \"Bohemian Rhapsody\", \"künstler\": null}\n"
        ),
        "schema": {
            "type": "object",
            "properties": {
                "song": {"type": ["string", "null"]},
                "künstler": {"type": ["string", "null"]},
            },
            "required": ["song", "künstler"],
        },
        "keys": ["song", "künstler"],
    },

    21: {
        "system_prompt": (
            "You extract exactly one parameter from a German voice command "
            "(speech-to-text output, may contain transcription errors).\n\n"
            "TASK: Extract the name of the program/app the user wants to "
            "open.\n\n"
            "RULES:\n"
            "- Return the program name exactly as mentioned.\n"
            "- If no program is recognisable, return null.\n\n"
            "EXAMPLES:\n"
            "Input: \"öffne den taschenrechner\" -> {\"programm\": \"Taschenrechner\"}\n"
            "Input: \"starte spotify\" -> {\"programm\": \"Spotify\"}\n"
            "Input: \"mach das mal auf\" -> {\"programm\": null}\n"
        ),
        "schema": {
            "type": "object",
            "properties": {"programm": {"type": ["string", "null"]}},
            "required": ["programm"],
        },
        "keys": ["programm"],
    },

    23: {
        "system_prompt": (
            "You extract three parameters from a German voice command about "
            "setting a timer (speech-to-text output, may contain "
            "transcription errors).\n\n"
            "TASK: Extract hours, minutes, and seconds SEPARATELY, exactly "
            "as stated for each unit. Do NOT convert between units "
            "(e.g. do not turn 90 minutes into 1 hour 30 minutes).\n\n"
            "RULES:\n"
            "- \"stunden\": number of hours mentioned, 0 if none mentioned.\n"
            "- \"minuten\": number of minutes mentioned, 0 if none mentioned.\n"
            "- \"sekunden\": number of seconds mentioned, 0 if none mentioned.\n\n"
            "EXAMPLES:\n"
            "Input: \"stelle einen timer auf 10 minuten\" -> "
            "{\"stunden\": 0, \"minuten\": 10, \"sekunden\": 0}\n"
            "Input: \"timer für 1 stunde und 30 sekunden\" -> "
            "{\"stunden\": 1, \"minuten\": 0, \"sekunden\": 30}\n"
            "Input: \"90 minuten timer\" -> "
            "{\"stunden\": 0, \"minuten\": 90, \"sekunden\": 0}\n"
        ),
        "schema": {
            "type": "object",
            "properties": {
                "stunden": {"type": "integer", "minimum": 0},
                "minuten": {"type": "integer", "minimum": 0},
                "sekunden": {"type": "integer", "minimum": 0},
            },
            "required": ["stunden", "minuten", "sekunden"],
        },
        "keys": ["stunden", "minuten", "sekunden"],
    },

    24: {
        "system_prompt": (
            "You extract two parameters from a German voice command about "
            "translation (speech-to-text output, may contain transcription "
            "errors).\n\n"
            "TASK: 1) the text that should be translated, 2) the target "
            "language. NEVER translate the text yourself.\n\n"
            "RULES:\n"
            "- \"text\": return the text to be translated EXACTLY unchanged, "
            "in whatever language it was said in. null if no text is given.\n"
            "- \"zielsprache_code\": the ISO-639-1 code of the language the "
            "user wants to translate INTO. Recognise phrases like "
            "\"ins Englische\", \"auf Englisch\", \"ins Französische\". The "
            "source language of the text is irrelevant and must never be "
            "used as the target. null if no target language is mentioned.\n\n"
            "EXAMPLES:\n"
            "Input: \"übersetze guten morgen ins englische\" -> "
            "{\"text\": \"guten morgen\", \"zielsprache_code\": \"en\"}\n"
            "Input: \"wie sagt man hallo auf französisch\" -> "
            "{\"text\": \"hallo\", \"zielsprache_code\": \"fr\"}\n"
            "Input: \"übersetze das\" -> "
            "{\"text\": null, \"zielsprache_code\": null}\n"
        ),
        "schema": {
            "type": "",
            "properties": {
                "text": {"type": ["string", "null"]},
                "zielsprache_code": {"type": ["string", "null"]},
            },
            "required": ["text", "zielsprache_code"],
        },
        "keys": ["text", "zielsprache_code"],
    },

    26: {
        "system_prompt": (
            "You extract exactly one parameter from a German voice command "
            "(speech-to-text output, may contain transcription errors).\n\n"
            "TASK: Extract the place for which the user wants the weather.\n\n"
            "RULES:\n"
            "- Return the place name exactly as mentioned.\n"
            "- If no place is mentioned, return null (in that case the "
            "current location is used later).\n\n"
            "EXAMPLES:\n"
            "Input: \"wie ist das wetter in berlin\" -> {\"ort\": \"Berlin\"}\n"
            "Input: \"wird es morgen regnen\" -> {\"ort\": null}\n"
            "Input: \"wetter zürich\" -> {\"ort\": \"Zürich\"}\n"
        ),
        "schema": {
            "type": "object",
            "properties": {"ort": {"type": ["string", "null"]}},
            "required": ["ort"],
        },
        "keys": ["ort"],
    },
}


def ollama_request(intent, text):
    """Fragt das kleine Sprachmodell nach den Parametern eines Befehls.

    Parameter:
        intent: Befehlsnummer (muss in befehle_mit_parameter vorkommen).
        text: Der (bereits aufbereitete) Satz des Nutzers.

    Das Modell antwortet im JSON-Format, das durch das Schema des Befehls vorgegeben ist. Die Antwort
    wird eingelesen; der Wert «unbekannt» wird zu None.
    Rückgabe: Dictionary mit den Parametern (Schlüssel siehe «keys» des Befehls) oder ein leeres Dictionary,
    wenn die Antwort nicht als JSON gelesen werden konnte.
    """
    spec = befehle_mit_parameter[intent]

    response = ollama.chat(
        model=MODELL,
        messages=[
            {"role": "system", "content": spec["system_prompt"]},
            {"role": "user", "content": f"Input: \"{text}\"\nOutput JSON:"},
        ],
        format=spec["schema"],
        think=False,
        keep_alive=-1,
        options={
            "temperature": 0,
            "top_p": 0.1,
            "repeat_penalty": 1.1,
            "num_predict": 128,
            "seed": 42,
        },
    )

    parameter = response["message"]["content"].strip().replace("```json", "").replace("```", "").strip()
    try:
        result = json.loads(parameter)
        if isinstance(result, dict):
            for key, value in result.items():
                if isinstance(value, str) and value.lower() == "unbekannt":
                    result[key] = None
            return result
        return {}
    except Exception:
        print(f"Fehler bei KI Params:(input) {parameter}")
        return {}


def llm_params(intent, text):
    """Bestimmt zu einer erkannten Befehlsnummer die Parameter und gibt die vollständige Befehlsliste zurück.

    Parameter:
        intent: Befehlsnummer (0 bis 27), vom Intent-Erkennungssystem bestimmt.
        text: Der Satz des Nutzers.

    Rückgabe: Liste [Befehlsnummer, Parameter 1, Parameter 2, ...].
      - Befehl 12 (recherchieren): der ganze Satz wird als Parameter übergeben (kein Modellaufruf).
      - Befehle ohne Parameter: nur [Befehlsnummer].
      - Befehl 23 (Timer): Stunden, Minuten und Sekunden werden zu Sekunden zusammengerechnet.
      - sonst: die Werte in der Reihenfolge der «keys» des Befehls. Nicht gefundene Parameter sind None.
    """
    #print("Extrahiere Parameter mit LLM")
    if intent == 12:
        return [intent, text]
    if intent not in befehle_mit_parameter:
        return [intent]

    spec = befehle_mit_parameter[intent]
    daten = ollama_request(intent, ersetze_zahlwoerter(text))

    if intent == 23:
        try:
            sekunden = (
                int(float(daten.get("stunden") or 0) * 3600)
                + int(float(daten.get("minuten") or 0) * 60)
                + int(float(daten.get("sekunden") or 0))
            )
            return [23, sekunden]
        except Exception:
            return [23]

    werte = [daten.get(k) for k in spec["keys"]]
    return [intent] + werte


# Direkter Start der Datei: kleiner Test der Parameter-Extraktion
if __name__ == "__main__":
    print(llm_params(8, "MACH 1 prozent leiser"))
