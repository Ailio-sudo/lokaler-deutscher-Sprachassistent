"""Befehl 22: Wochentag und Datum ansagen."""
from datetime import datetime
import locale

# Wochentage auf Deutsch ausgeben (Windows-Ländereinstellung «de_DE»)
locale.setlocale(locale.LC_TIME, "de_DE")

def tag():
    """Befehl 22: Gibt Wochentag und aktuelles Datum als Satz zurück (z. B. «Heute ist Freitag der 16.10.2026»)."""
    return f"Heute ist {datetime.now().strftime('%A')} der {datetime.now().strftime('%d.%m.%Y')}"

if __name__ == "__main__":
    print(tag())
