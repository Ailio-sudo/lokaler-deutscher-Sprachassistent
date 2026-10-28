"""Sprachausgabe (Text-to-Speech) mit pyttsx3. Die Sprachausgabe läuft lokal über die installierten Windows-Stimmen."""
print("Lade pyttsx3...")
import pyttsx3
import abbruch
print("pyttsx3 geladen!")

def TTS(text):
    """Spricht den Text laut aus und blockiert, bis die Ausgabe beendet ist (oder gestoppt wurde).

    Parameter:
        text: Der vorzulesende Text (str).

    Verwendet die erste installierte Stimme "Hedda" mit der
    Sprechgeschwindigkeit 200.
    Wird die Anfrage über den Stopp-Knopf abgebrochen, endet die Ausgabe spätestens beim nächsten Wort.
    """
    nr = abbruch.meine_nr()
    if not abbruch.gueltig(nr):
        return

    #Text zu Sprache mit Windows Hedda
    engine = pyttsx3.init()
    engine.setProperty("rate", 200) # Geschwindigkeit
    engine.setProperty("voice", engine.getProperty("voices")[0].id)

    def bei_wort(name, location, length):
        # Läuft im Thread der Sprachausgabe; engine.stop() ist hier sicher
        if abbruch.aktuell() != nr:
            engine.stop()

    # pyttsx3.init() kann dieselbe Engine mehrfach liefern -> Callback danach wieder entfernen,
    # sonst würden alte Callbacks spätere Ausgaben stoppen
    token = engine.connect("started-word", bei_wort)
    try:
        print()
        engine.say(text)
        engine.runAndWait() #Spricht den Text direkt
    finally:
        try:
            engine.disconnect(token)
        except Exception:
            pass

if __name__ == "__main__":
    import time
    print("Start")
    zeit = time.time()
    TTS(input("Was soll gesagt werden?"))
    print("Fertig")
    print(time.time()-zeit)