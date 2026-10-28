"""Gemeinsamer Abbruch-Zustand für Stopp-Knopf, Aufnahme, Transkription und Sprachausgabe.

Jeder Stopp erhöht einen Zähler. Eine Anfrage (Worker-Thread, Aufnahme, Sprachausgabe) merkt sich die
Nummer, mit der sie gestartet wurde; ist der Zähler inzwischen höher, gilt sie als abgebrochen.
"""
import threading


class Abbruch(BaseException):
    """Beendet eine abgebrochene Anfrage. Erbt absichtlich von BaseException, damit
    «except Exception» in den Systemen und Befehlen sie nicht verschluckt."""


_nr = 0
_lokal = threading.local()      # Nummer der Anfrage des jeweiligen Threads


def aktuell():
    """Aktueller Zählerstand."""
    return _nr


def stoppen():
    """Wird vom Stopp-Knopf aufgerufen: macht alle laufenden Anfragen ungültig."""
    global _nr
    _nr += 1


def anfrage_setzen(nr):
    """Legt für den aktuellen Thread fest, zu welcher Anfrage er gehört."""
    _lokal.nr = nr


def anfrage_loeschen():
    """Entfernt die Zuordnung wieder (der Thread gilt danach immer als gültig)."""
    if hasattr(_lokal, "nr"):
        del _lokal.nr


def meine_nr():
    """Nummer der Anfrage des aktuellen Threads (ohne Zuordnung: aktueller Zählerstand)."""
    return getattr(_lokal, "nr", _nr)


def gueltig(nr=None):
    """True, solange die Anfrage nicht gestoppt wurde."""
    return (meine_nr() if nr is None else nr) == _nr


def pruefen(nr=None):
    """Löst Abbruch aus, wenn die Anfrage gestoppt wurde."""
    if not gueltig(nr):
        raise Abbruch()