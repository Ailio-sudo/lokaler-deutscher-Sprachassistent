"""Sprachausgabe (Text-to-Speech) mit pyttsx3. Die Sprachausgabe läuft lokal über die installierten Windows-Stimmen."""
print("Lade pyttsx3...")
import pyttsx3
print("pyttsx3 geladen!")

def TTS(text):
    """Spricht den Text laut aus und blockiert, bis die Ausgabe beendet ist.

    Parameter:
        text: Der vorzulesende Text (str).

    Verwendet die erste installierte Stimme "Hedda" mit der
    Sprechgeschwindigkeit 200.
    """
    #Text zu Sprache mit Windows Hedda
    engine = pyttsx3.init()
    engine.setProperty("rate", 200) # Geschwindigkeit
    engine.setProperty("voice", engine.getProperty("voices")[0].id)
    print()
    engine.say(text)
    engine.runAndWait() #Spricht den Text direkt

if __name__ == "__main__":
    import time
    print("Start")
    zeit = time.time()
    TTS(input("Was soll gesagt werden?"))
    print("Fertig")
    print(time.time()-zeit)

