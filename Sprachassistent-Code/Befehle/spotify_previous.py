"""Befehl 20: Zum vorherigen Titel wechseln (Medientaste)."""
import keyboard

def previous_track():
    """Befehl 20: Simuliert die Medientaste «previous track». Liefert keinen Text zurück."""
    keyboard.press("previous track")

if __name__ == "__main__":
    print(previous_track())
