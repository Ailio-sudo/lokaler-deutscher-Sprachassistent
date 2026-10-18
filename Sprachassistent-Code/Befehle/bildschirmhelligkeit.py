"""Befehle 1-3: Bildschirmhelligkeit ändern, abfragen und setzen (Bibliothek screen_brightness_control, Bildschirm 0)."""
import screen_brightness_control as sbc
from Befehle.getparam import get_parameter
def get_brightness():
    """Befehl 2: Gibt die aktuelle Helligkeit des Bildschirms 0 als Satz zurück (Wert in Prozent)."""
    return "Die aktuelle Bildschirmhelligkeit ist " + str(sbc.get_brightness(display=0)[0])

def set_brightness(value=None):
    """Befehl 3: Setzt die Helligkeit auf einen Wert in Prozent.

    Parameter:
        value: Zielwert (wird mit int() umgewandelt und auf 0 bis 100 begrenzt). Ist er None, wird per get_parameter nachgefragt.
    Rückgabe: Nichts (None); der Befehl liefert daher keine Sprachausgabe.
    """
    if value == None:
        return set_brightness(get_parameter("Auf welche Helligkeit willst du den Bildschirm setzen?"))
    value = int(value)
    if value > 100: value = 100
    if value < 0: value = 0
    sbc.set_brightness(value, display=0)
    return f"Ich habe um Helligkeit geändert {value} gesetzt."

def change_brightness(delta=None):
    """Befehl 1: Ändert die Helligkeit relativ zum aktuellen Wert.

    Parameter:
        delta: Änderung in Prozentpunkten (positiv = heller, negativ = dunkler). Ist sie None, wird per get_parameter nachgefragt.
    Rückgabe: Nichts (None); die neue Helligkeit wird über set_brightness gesetzt und auf 0 bis 100 begrenzt.
    """
    if delta == None:
        return change_brightness(get_parameter("Um welchen Wert willst du die Helligkeit verändern?"))
    set_brightness(sbc.get_brightness(display=0)[0] + delta)
    return f"Ich habe um Helligkeit geändert {delta}."

