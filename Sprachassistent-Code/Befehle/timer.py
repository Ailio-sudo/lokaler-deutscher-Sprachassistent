"""Befehl 23: Timer. Nach Ablauf erscheint eine Windows-Benachrichtigung mit Ton (winotify)."""
from winotify import Notification,audio
import time
import threading
if __name__ == "__main__":
    from getparam import get_parameter
def timer_back(zeit=None):
    """Befehl 23: Stellt einen Timer.

    Parameter:
        zeit: Dauer in Sekunden. Ist sie None, wird per get_parameter nachgefragt.
    Der Timer läuft in einem Hintergrund-Thread (Daemon) und endet daher mit dem Programm.
    Rückgabe: Bestätigungssatz mit einem Hinweis auf «Bitte nicht stören».
    """
    if zeit == None:
        return timer_back(int(get_parameter("Wieviele Sekunden soll der Timer Dauern?")))
    def timer():
        toast = Notification(app_id="Sprachassistent",
                            title="TIMER VORBEI",
                            msg="Dein " + str(zeit) + " Sekunden Timer ist vorbei!",
                            icon=r"")
        toast.set_audio(audio.Mail, loop=False)
        time.sleep(zeit)
        toast.show()
    threading.Thread(target=timer, daemon=True).start()
    return f"Ich habe einen {zeit} Sekunden timer gestellt. Stell sicher das 'Bitte Nicht Stören' deaktiviert ist!"

if __name__ == "__main__":
    timer_back()
    time.sleep(1000000)
