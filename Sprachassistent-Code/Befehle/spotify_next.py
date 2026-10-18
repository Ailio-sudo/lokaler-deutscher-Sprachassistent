"""Befehl 16: Zum nächsten Titel wechseln (Medientaste)."""
import keyboard

def next_track():
    """Befehl 16: Simuliert die Medientaste «next track». Liefert keinen Text zurück."""
    keyboard.press("next track")
if __name__ == "__main__":
    print(next_track())
