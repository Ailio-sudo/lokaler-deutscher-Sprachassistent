"""Befehle 8-10: Systemlautstärke ändern, abfragen und setzen (Bibliothek pycaw, Standard-Lautsprecher)."""
from pycaw.pycaw import AudioUtilities
from Befehle.getparam import get_parameter
# Lautstärkeregler des Standard-Lautsprechers (der erste Teil dieser Datei zeigt die ausprobierten Varianten)
devices = AudioUtilities.GetSpeakers()

volume = devices.EndpointVolume

def get_volume():
    """Befehl 9: Gibt die aktuelle Systemlautstärke als Satz zurück (Prozent)."""
    return "Die aktuelle Lautstärke beträgt " + str(int(volume.GetMasterVolumeLevelScalar()*100)) + " prozent."

def set_volume(lautstärke=None):
    """Befehl 10: Setzt die Systemlautstärke in Prozent (Wert wird auf 0 bis 100 begrenzt).

    Parameter:
        lautstärke: Zielwert; wird mit int() umgewandelt. Ist er keine Zahl, wird ein Fehlertext zurückgegeben.
    Rückgabe: Nichts (None) bei Erfolg, sonst ein Fehlertext.
    """
    if lautstärke == None:
        return set_volume(get_parameter("Auf welche Lautstärke?"))
    try:
        lautstärke=int(lautstärke)
    except:
        return "Fehler beim ausführen: " + str(lautstärke) + " ist keine Zahl"
    if lautstärke > 100:
        lautstärke = 100
    if lautstärke < 0:
        lautstärke = 0
    volume.SetMasterVolumeLevelScalar(lautstärke/100, None)

def change_volume(delta=None):
    """Befehl 8: Ändert die Lautstärke relativ zum aktuellen Wert.

    Parameter:
        delta: Änderung in Prozentpunkten (positiv = lauter, negativ = leiser).
    Rückgabe: Nichts (None), die neue Lautstärke wird über set_volume gesetzt.
    """
    if delta == None:
        delta = 10
    set_volume(volume.GetMasterVolumeLevelScalar()*100 + delta)

if __name__ == "__main__":
    change_volume(-30)
    print(get_volume())
