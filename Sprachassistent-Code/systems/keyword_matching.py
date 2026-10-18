"""Keyword Matching: Intent-Erkennung über Schlüsselwörter (in der Arbeit auch «If-Else-System» genannt).

Die Eingabe wird in Kleinbuchstaben umgewandelt und der Reihe nach mit Listen von Schlüsselwörtern verglichen.
Die Schlüsselwörter müssen nicht ganze Wörter sein: geprüft wird, ob das Schlüsselwort irgendwo im Satz vorkommt
(«w in t»). Dadurch passen auch verschiedene Wortformen, es sind aber auch unbeabsichtigte Treffer möglich.
Die Reihenfolge der Prüfungen ist wichtig: Gruppen, die weiter oben stehen, werden bevorzugt.
"""

def if_else(text):
    """Ordnet einem Satz die Befehlsnummer zu.

    Parameter:
        text: Der (transkribierte) Satz des Nutzers.

    Rückgabe: Befehlsnummer als int (1 bis 27), oder 0, wenn kein Schlüsselwort passt (unbekannter Befehl).
    Beispiele: if_else("Wie spät ist es?") -> 25, if_else("Mach den Bildschirm heller") -> 1.
    """
    t = text.lower() #Grossbuchstaben -> kleinbuchstaben
    #Prüft für jeden Intent ob ein Keyword enthalten ist, beispiel Helligkeit:

    # Helligkeit: 3 = setzen, 2 = abfragen, 1 = ändern (Standard, wenn nichts Genaueres erkannt wird: 2)
    if any(w in t for w in ["hell", "dunkel", "dunkler", "dünkler"]): #Prüft ob ein Keywort im Satz vorkommt, True -> ein Befehl der mit Helligkeit arbeitet wird gewählt
        if any(w in t for w in ["setz", "auf", "stell"]): return 3 # Prüft ob der Nutzer die Helligkeit auf einen Wert setzen will
        if any(w in t for w in ["wie", "aktuelle", "zeig", "was"]): return 2 # Prüft ob der Nutzer die Helligkeit anzeigen lassen will
        if any(w in t for w in ["heller", "mehr hell", "erhöhe", "hellen", "änder", "dunkler", "dünkler", "reduziere", "dunkel", "runter", "tief", "dimm"]): return 1 #Prüft ob der Nutzer die Helligkeit um einen Wert verändern will
        return 2 # Befehl 2 falls kein Befehl genau erkannt, da kein Parameter benötigt
    # Lautstärke: 10 = setzen, 9 = abfragen, 8 = ändern (lauter und leiser ergeben beide 8; Standard: 9)
    elif any(w in t for w in ["laut", "leise", "volume", "ton", "audio", "sound", "schall", "läuter", "stumm"]):
        if any(w in t for w in ["setz", "auf", "stell"]): return 10
        if any(w in t for w in ["wie", "aktuelle", "zeig", "was"]): return 9
        if any(w in t for w in ["lauter", "erhöh", "mehr", "hoch", "läuter"]): return 8
        if any(w in t for w in ["leiser", "reduzier", "weniger", "runter", "dämpf", "tiefer", "änder", "erhöhe"]): return 8
        return 9
    # 4 = E-Mails prüfen
    elif any(w in t for w in ["mail", "postfach", "inbox", "posteingang"]): return 4
    # Einkaufsliste: 7 = leeren, 6 = vorlesen, 5 = hinzufügen (Standard: 6)
    elif any(w in t for w in ["einkauf", "supermarkt", "shop", "liste", "produkt", "zettel"]):
        if any(w in t for w in ["lösch", "leer", "neu", "reset", "clear", "zurücksetzen", "entferne"]): return 7
        if any(w in t for w in ["lies", "lesen", "steht", "zeig", "was ist drauf", "was ist drin"]): return 6
        if any(w in t for w in ["füge", "hinzu", "add", "dazu", "trage", "notiere", "merke", "schreibe", "setz"]): return 5
        return 6
    # 11 = News
    elif any(w in t for w in ["news", "nachrichten", "schlagzeile", "neuigkeiten", "srf", "was ist passiert", "was gibt es neues", "tagesschau", "presse", "meldungen"]): return 11
    # 13 = Route berechnen
    elif any(w in t for w in ["route", "navi", "weg von", "weg zu", "weg nach", "fahre von", "distanz", "wie komme", "weit ist", "wie weit", "wie lange", "anfahrt", "richtung", "wegbeschreibung", "strecke"]): return 13
    # 14 = Screenshot
    elif any(w in t for w in ["screenshot", "bild", "snipping", "capture", "aufnahme", "schnappschuss", "foto"]): return 14
    # 15 = Datei suchen
    elif any(w in t for w in ["datei", "dokument", "pdf", "word", "ordner", "notizen"]): return 15
    # Musiksteuerung: 17 = Pause, 18 = fortsetzen, 16 = nächster Titel, 20 = vorheriger Titel, sonst 19 = Lied abspielen
    elif any(w in t for w in ["musik", "lied", "song", "pause", "weiter", "stopp", "nächste", "vorherige", "spiel", "play", "track", "album", "künstler", "interpret", "wiedergabe", "überspringen"]):
        if any(w in t for w in ["pause", "beenden", "stop", "pausieren", "anhalten"]): return 17
        if any(w in t for w in ["weiter", "fortsetzen", "play"]): return 18
        if any(w in t for w in ["skip", "überspringen", "nächst", "folgend"]): return 16
        if any(w in t for w in ["vorherig", "zurück", "letzter"]): return 20
        return 19
    # 21 = Programm starten
    elif any(w in t for w in ["öffne", "starte", "ausführen"]): return 21
    # 25 = Uhrzeit
    elif any(w in t for w in ["uhr", "wie spät", "zeit", "minute", "stunde"]): return 25
    # 22 = Tag und Datum
    elif any(w in t for w in ["datum", "tag", "heute"]): return 22
    # 23 = Timer
    elif any(w in t for w in ["timer", "alarm", "countdown"]): return 23
    # 24 = Übersetzen
    elif any(w in t for w in ["übersetz", "translate", "wie sagt man", "wie heißt", "was heisst"]): return 24
    # 26 = Wetter
    elif any(w in t for w in ["wetter", "temperatur", "regen", "schnee", "sonnig", "bewölkt", "regnen", "wie warm", "wie kalt", "niederschlag", "sturm", "wind", "humidity", "feuchtigkeit"]): return 26
    # 27 = Würfeln
    elif any(w in t for w in ["würfel", "würfle", "zufall", "zufäll"]): return 27
    # 12 = Recherchieren (wird als Letztes geprüft; die Schlüsselwörter wie «wie», «was» oder «wer» sind sehr allgemein)
    elif any(w in t for w in ["recherch", "wer", "wie", "was", "wo", "warum", "suche", "informationen"]): return 12
    # Kein Schlüsselwort gefunden: 0 = unbekannter Befehl
    return 0



if __name__ == "__main__":
    # Skript zur Bestimmung der Keywords
    from training_data import dataset

    for data in dataset.values():
        intent = int(data["intent"])

        if not 1 <= intent <= 27:
            continue

        for text in data["examples"]:
            erkannt = if_else(text)

            if erkannt != intent:
                print(f"Fehler: '{text}'")
                print(f"Erwartet: Intent {intent}, ")
                print(f"Erkannt: Intent {erkannt}")
                print("")