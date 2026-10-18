"""Befehl 25: Uhrzeit ansagen."""
from datetime import datetime

def uhrzeit():
    """Befehl 25: Gibt die aktuelle Uhrzeit als Satz zurück (z. B. «Es ist 14 Uhr 5.»)."""
    return f"Es ist {datetime.now().hour} Uhr {round(datetime.now().minute)}."

if __name__ == "__main__":
    print(uhrzeit())
