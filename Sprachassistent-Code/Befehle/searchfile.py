"""Befehl 15: Dateisuche über die Windows-Suche."""
import pyautogui
import subprocess
import time
from Befehle.getparam import get_parameter
def searchfile(file_name=None):
    """Befehl 15: Öffnet die Windows-Suche mit dem Dateinamen.

    Parameter:
        file_name: Gesuchter Name (str). Ist er None, wird per get_parameter nachgefragt.
    Ablauf: Die Suche wird über PowerShell («search:query=...») gestartet; danach werden mit pyautogui die Tasten
    «Pfeil links» und «Enter» gedrückt. Während dieser Zeit sollte der Nutzer nichts eingeben.
    Rückgabe: Satz, dass die Ergebnisse angezeigt werden.
    """
    if file_name == None:
        return searchfile(get_parameter("Wie heisst das Dokument das du suchst?"))
    subprocess.run([
        'powershell', '-Command',
        f'Start-Process "search:query={file_name}"'
    ], shell=False)
    time.sleep(0.05)
    pyautogui.press("left")
    time.sleep(0.05)
    pyautogui.press("enter")

    return "Ergebnisse zu " + str(file_name) + " werden Angezeigt."

if __name__ == "__main__":
    searchfile("Xandra")
