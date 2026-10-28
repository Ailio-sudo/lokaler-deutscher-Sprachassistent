"""Sprachassistent: Hauptprogramm (Einstiegspunkt, gestartet über Sprachassistent.bat).

Zwei Betriebsarten (Auswahl beim Start in der Konsole):
  - Testmodus (nichts eingeben): Alle fünf Intent-Erkennungssysteme werden geladen; die grafische Oberfläche
    (Klasse Gui) zeigt Ergebnis und Zeitmessung jedes aktivierten Systems. Eingabe per Sprache oder Text.
  - Betriebsmodus (System wählen): Nur das gewählte System wird geladen; ein kleines Fenster (MiniGui)
    zeigt nur die Status-Animation. Der erkannte Befehl wird immer ausgeführt.

Ablauf einer Anfrage (Funktion Main -> text_verarbeitung):
  Wake Word «Hey Jarvis» -> Aufnahme und Transkription (ASR.py) -> Intent-Erkennung durch das gewählte System ->
  Parameter-Extraktion (ki_params.py; das KI-System liefert die Parameter selbst) -> Befehl ausführen
  (befehl_ausführen, Dateien im Ordner Befehle) -> Antwort per Sprachausgabe (TextToSpeech.py).

Die grafische Oberfläche läuft in einem eigenen Thread und erhält ihre Nachrichten über gui_queue (siehe Gui.ereignis).
Der Stopp-Knopf (in beiden Fenstern, auch Esc) beendet die aktuelle Anfrage sofort (siehe abbruch.py).
Beim Beenden werden alle geladenen Ollama-Modelle entladen.
"""

print("ASR Laden...")
from ASR import *   # liefert auch gui_queue und melde
print("Befehle Laden...")
from Befehle.bildschirmhelligkeit import *
from Befehle.e_mail import *
from Befehle.einkaufsliste import *
from Befehle.lautstarke import *
from Befehle.news import *
from Befehle.recherchieren import *
from Befehle.route import *
from Befehle.screenshot import *
from Befehle.searchfile import *
from Befehle.spotify_next import *
from Befehle.pause import *
from Befehle.play import *
from Befehle.spotify_playsong import *
from Befehle.spotify_previous import *
from Befehle.start_program import *
from Befehle.tag import *
from Befehle.timer import *
from Befehle.translator import *
from Befehle.uhrzeit import *
from Befehle.wetter import *
from Befehle.würfel import *
from TextToSpeech import *
import ollama
pygame.init()

# Standardbibliothek NACH den Star-Imports, damit nichts überschrieben wird
import math                          # für die Animationen
import os
import queue
import sys                           # für sys.setswitchinterval (siehe unten)
import threading
import tkinter as tk
from time import perf_counter        # für die Zeitmessung

import abbruch                       # gemeinsamer Abbruch-Zustand (Stopp-Knopf)
from ki_params import llm_params

# Gibt dem GUI-Thread öfter die Chance zu zeichnen, auch wenn ein Modell rechnet
sys.setswitchinterval(0.001)

# Globaler Zustand: methoden = Namen der aktuell aktivierten Systeme; do_befehl = erkannten Befehl wirklich ausführen?
methoden = ["Keyword Matching"] # Mögliche Systeme
# gui_queue und melde() kommen aus ASR.py (from ASR import *), damit ASR.py und diese Datei dieselbe Queue benutzen.
# Die Queue transportiert einzelne Ereignisse.
do_befehl = False
gui_bereit = threading.Event()   # wird gesetzt, sobald (Systeme geladen und) GUI offen ist


# ======================================================================
#  Abbruch (Stopp-Knopf)
# ======================================================================
_melde_original = melde


def melde(*args):
    """Wie ASR.melde, beendet aber eine abgebrochene Anfrage (jede Meldung ist ein Prüfpunkt)."""
    abbruch.pruefen()
    _melde_original(*args)


def stoppe_ausgabe():
    """Stoppt den Signalton (pygame). Die Sprachausgabe stoppt sich selbst (siehe TextToSpeech.py)."""
    try:
        pygame.mixer.stop()
        pygame.mixer.music.stop()
    except Exception:
        pass


def stopp_anfrage():
    """Wird vom Stopp-Knopf (und Esc) aufgerufen."""
    print("Stopp gedrückt")
    abbruch.stoppen()
    stoppe_ausgabe()


def regex_params(intent, text):
    """Bestimmt die Parameter zu einem erkannten Befehl.

    Der Name stammt aus einer früheren Version mit regulären Ausdrücken; die Funktion ruft inzwischen ki_params.llm_params auf
    (Parameter-Extraktion mit einem kleinen Sprachmodell).
    Rückgabe: Liste [Befehlsnummer, Parameter, ...].
    """
    return llm_params(intent, text)


# ======================================================================
#  Befehlsnamen (für die Anzeige)
# ======================================================================
# Anzeigenamen der Befehlsnummern (nur für die Anzeige in der GUI)
BEFEHLSNAMEN = {
    0: "Unbekannter Befehl",
    1: "Helligkeit ändern", 2: "Helligkeit abfragen", 3: "Helligkeit setzen",
    4: "E-Mails prüfen",
    5: "Einkaufsliste: hinzufügen", 6: "Einkaufsliste: vorlesen", 7: "Einkaufsliste: neu",
    8: "Lautstärke ändern", 9: "Lautstärke abfragen", 10: "Lautstärke setzen",
    11: "News", 12: "Recherchieren", 13: "Route", 14: "Screenshot", 15: "Datei suchen",
    16: "Nächster Titel", 17: "Pause", 18: "Play", 19: "Song abspielen", 20: "Vorheriger Titel",
    21: "Programm starten", 22: "Tag", 23: "Timer", 24: "Übersetzen",
    25: "Uhrzeit", 26: "Wetter", 27: "Würfel",
}


def befehl_beschreiben(befehl):
    """[26, 'Zürich'] -> '26: Wetter\\nParameter: Zürich'"""
    if isinstance(befehl, int):
        befehl = [befehl]
    try:
        nr = int(befehl[0])
        params = list(befehl[1:])
    except Exception:
        return f"Unerwartete Ausgabe: {befehl}"
    name = BEFEHLSNAMEN.get(nr, "Unbekannter Befehl")
    param_text = ", ".join(str(p) for p in params) if params else "keine"
    return f"{nr}: {name}\nParameter: {param_text}"


# ======================================================================
#  Systeme vorbereiten
# ======================================================================
# system_vorbereiten() führt die Imports der Systeme schon beim Start aus und macht einen Probelauf,
# damit der erste Befehl nicht lange dauert. Die Imports in text_verarbeitung sind danach nur noch
# ein Zugriff auf den Python-Import-Cache.
SYSTEME = [
    "Keyword Matching",
    "TF-IDF",
    "Word Embeddings",
    "Sentence Embeddings",
    "KI (gemma)"
]
WARMUP_TEXT = "Wie ist das Wetter in Zürich"

bereit = {}        # name -> True, sobald das System vorbereitet ist
ladezeiten = {}    # name -> Sekunden
_lade_locks = {name: threading.Lock() for name in SYSTEME}
_llm_lock = threading.Lock()
_llm_geladen = False


def llm_vorbereiten():
    """Lädt das Sprachmodell der Parameter-Extraktion einmal."""
    global _llm_geladen
    with _llm_lock:
        if _llm_geladen:
            return
        print("LLM zur Parameterextraktion wird geladen...")
        regex_params(1, "Mach 5 Prozent heller")
        _llm_geladen = True


def system_vorbereiten(name):
    """Importiert ein System und führt einen Probelauf aus (mehrfach aufrufbar, thread-sicher)."""
    with _lade_locks[name]:
        if name in bereit:
            return
        melde("prep_start", name)
        t0 = perf_counter()
        try:
            if name != "KI (gemma)":
                llm_vorbereiten()             # nur nötig, wenn die Parameter über regex_params laufen
            if name == "Keyword Matching":
                from systems.keyword_matching import if_else
                if_else(WARMUP_TEXT)
            elif name == "TF-IDF":
                from systems.tf_idf import predict_intent
                predict_intent(WARMUP_TEXT)
            elif name == "Word Embeddings":
                from systems.word_embeds import word_embeddings
                word_embeddings(WARMUP_TEXT)
            elif name == "Sentence Embeddings":
                from systems.sentence_embeds import sentence_embeddings
                sentence_embeddings(WARMUP_TEXT)
            elif name == "KI (gemma)":
                from systems.ki_gemma import ki_local
                ki_local(WARMUP_TEXT)
        except Exception as e:
            print(f"Vorbereiten von {name} fehlgeschlagen: {e}")
            melde("system_fehler", name, f"Laden fehlgeschlagen: {e}")
            return
        dauer = perf_counter() - t0
        bereit[name] = True
        ladezeiten[name] = dauer
        print(f"{name} bereit ({dauer:.2f} s)")
        melde("prep_done", name, dauer)


def vorbereiten_starten(namen, fertig=None):
    """Bereitet die Systeme nacheinander im Hintergrund vor. 'fertig' (Event) wird am Ende gesetzt."""
    def lauf():
        try:
            for n in namen:
                system_vorbereiten(n)
        finally:
            if fertig is not None:
                fertig.set()
    threading.Thread(target=lauf, daemon=True).start()


# ======================================================================
#  Zeitmessung: Intent-Erkennung und Parameter-Extraktion getrennt
# ======================================================================
def messen_intent_params(name, intent_fn, text):
    """Führt «regex_params(intent_fn(), text)» aus, misst aber beide Schritte getrennt.
    Fehler in einem System ergeben [0] (und eine Fehlermeldung in der GUI)."""
    melde("system_start", name)
    try:
        melde("phase", name, "intent")
        t0 = perf_counter()
        intent = intent_fn()
        t_intent = perf_counter() - t0

        melde("phase", name, "parameter")     # nicht Teil der Messung
        t1 = perf_counter()
        befehl = regex_params(intent, text)
        t_params = perf_counter() - t1
    except Exception as e:
        melde("system_fehler", name, str(e))
        return [0]
    melde("system_done", name, befehl, (t_intent, t_params, t_intent + t_params))
    return befehl


def messen_gesamt(name, system_fn):
    """Wie messen_intent_params, aber für das KI-System (gemma), das Intent und Parameter in EINEM Aufruf liefert."""
    melde("system_start", name)
    try:
        melde("phase", name, "gesamt")
        t0 = perf_counter()
        befehl = system_fn()
        t_gesamt = perf_counter() - t0
    except Exception as e:
        melde("system_fehler", name, str(e))
        return [0]
    melde("system_done", name, befehl, (None, None, t_gesamt))
    return befehl


# ======================================================================
#  Ollama-Modelle entladen
# ======================================================================

def _modellname(m):
    """Liest den Modellnamen aus einem Eintrag von ollama.ps() (Schlüssel «model» oder «name»); None, wenn keiner vorhanden ist."""
    for key in ("model", "name"):
        try:
            wert = m[key]
        except Exception:
            wert = None
        if wert:
            return wert
    return None


def modelle_entladen():
    """Entlädt ALLE aktuell in Ollama geladenen Modelle (nicht nur vordefinierte Namen)."""
    try:
        antwort = ollama.ps()
        modelle = antwort.get("models", []) or []
    except Exception as e:
        print("Konnte laufende Ollama-Modelle nicht abfragen:", e)
        return
    for m in modelle:
        name = _modellname(m)
        if not name:
            continue
        try:
            print("Entlade", name)
            ollama.chat(model=name, messages=[], keep_alive=0)
        except Exception as e:
            print(f"Entladen von {name} fehlgeschlagen: {e}")


# ======================================================================
#  Textverarbeitung
# ======================================================================
def _text_verarbeitung(text):
    """Verarbeitet einen Satz vollständig: Intent erkennen, Parameter bestimmen und (falls gewünscht) den Befehl ausführen.

    Läuft in einem Worker-Thread (gestartet von text_verarbeitung). Nach einem Stopp löst die nächste
    Meldung (melde) abbruch.Abbruch aus und beendet die Funktion.

    Parameter:
        text: Der Satz (transkribiert oder eingetippt). Ist er leer oder None, wird nur eine Rückfrage ausgegeben.
    Ablauf: Jedes aktivierte System (Liste «methoden») verarbeitet den Satz nacheinander und die GUI erhält Nachrichten
    zu Zustand und Dauer. Tritt bei einem System ein Fehler auf, gilt für dieses der Befehl [0].
    Nur wenn genau ein System aktiv ist und «do_befehl» gesetzt ist, wird der erkannte Befehl ausgeführt (befehl_ausführen),
    die Antwort angezeigt und vorgelesen. Befehle ohne Rückgabetext werden nicht vorgelesen.
    """
    # Leere Nachricht (ASR.Record() liefert None, wenn nichts verstanden wurde)
    if not text:
        output = "Ich konnte dich nicht verstehen. Bitte wiederhole deine Nachricht."
        print(output)
        melde("zustand", "idle")
        if do_befehl:
            melde("ausgabe", output)               # erst anzeigen, dann sprechen
            TTS(output)
        return

    t_gesamt = perf_counter()                      # Gesamtzeit
    melde("input", text)
    melde("runde_start", list(methoden))
    melde("zustand", "verarbeiten")

    # Ausgewählte Systeme verwenden
    befehle = []
    if "Keyword Matching" in methoden:
        from systems.keyword_matching import if_else
        #print("Gewähltes Modell: Keyword Matching")
        befehle.append(("Keyword Matching", messen_intent_params("Keyword Matching", lambda: if_else(text), text)))
    if "TF-IDF" in methoden:
        from systems.tf_idf import predict_intent
        #print("Gewähltes Modell: TF-IDF")
        befehle.append(("TF-IDF", messen_intent_params("TF-IDF", lambda: predict_intent(text)[0], text)))
    if "Word Embeddings" in methoden:
        from systems.word_embeds import word_embeddings
        #print("Gewähltes Modell: Word Embeddings")
        befehle.append(("Word Embeddings", messen_intent_params("Word Embeddings", lambda: int(word_embeddings(text)[0]), text)))
        #print(" Word Embeds ", text, word_embeddings(text))
    if "Sentence Embeddings" in methoden:
        from systems.sentence_embeds import sentence_embeddings
        #print("Sentence Embeds", text, sentence_embeddings(text))
        befehle.append(("Sentence Embeddings", messen_intent_params("Sentence Embeddings", lambda: int(sentence_embeddings(text)[0]), text)))
    if "KI (gemma)" in methoden:
        from systems.ki_gemma import ki_local
        print("Gewähltes Modell: KI (gemma)")
        befehle.append(("KI (gemma)", messen_gesamt("KI (gemma)", lambda: ki_local(text))))

    print("Von Modellen erkannte Befehle:", befehle)
    print("Transkribierter Text:", text)

    # Befehl ausführen, wenn nur ein System aktiv ist
    if len(methoden) == 1 and do_befehl:
        befehl = befehle[0][1]
        melde("zustand", "ausfuehren")
        if befehl == [0]:
            output = "Dies scheint kein gültiger Befehl zu sein!"
        else:
            try:
                output = befehl_ausführen(befehl)
            except Exception as e:
                output = f"Fehler beim Ausführen des Befehls: {e}"

        # Ausgabe zuerst im Fenster anzeigen, damit man während der Sprachausgabe mitlesen kann
        melde("ausgabe", str(output) if output is not None else "(keine Sprachausgabe)")
        # Ausgabe über TTS
        if output is not None:
            TTS(output)
    else:
        melde("ausgabe", None)                     # keine Ausführung -> Hinweistext im Fenster
        output = befehle

    print(output)
    melde("zustand", "idle")
    melde("fertig", perf_counter() - t_gesamt)


def _lauf(nr, text):
    """Rumpf des Worker-Threads: ordnet den Thread der Anfrage zu und fängt Abbruch und Fehler ab."""
    abbruch.anfrage_setzen(nr)
    try:
        _text_verarbeitung(text)
    except abbruch.Abbruch:
        pass
    except Exception:
        import traceback
        traceback.print_exc()
        if abbruch.gueltig():
            _melde_original("zustand", "idle")


def _abgebrochen():
    """Meldet der GUI, dass die Anfrage abgebrochen wurde (Aufruf im Aufrufer-Thread, nicht im Worker)."""
    stoppe_ausgabe()
    melde("abgebrochen")
    melde("zustand", "idle")
    print("Anfrage abgebrochen")


def text_verarbeitung(text):
    """Startet die Verarbeitung in einem Worker-Thread und kehrt bei Stopp sofort zurück.

    Der Worker läuft nach einem Stopp ggf. noch kurz im Hintergrund weiter (ein bereits rechnendes Modell
    lässt sich nicht unterbrechen); seine Meldungen werden aber verworfen und sein Ergebnis nicht mehr verwendet.
    """
    nr = abbruch.aktuell()
    worker = threading.Thread(target=_lauf, args=(nr, text), daemon=True)
    worker.start()
    while worker.is_alive():
        worker.join(0.05)
        if abbruch.aktuell() != nr:
            _abgebrochen()
            return


# ======================================================================
#  GUI
# ======================================================================
# Farbpalette der Oberfläche (dunkles Design); FRAME_MS = Zeit zwischen zwei Bildern der Animation
F = {
    "bg": "#0f1117", "card": "#181b24", "card2": "#1f2330", "rand": "#2b3042",
    "text": "#e6e8ee", "sub": "#8a90a2", "weiss": "#ffffff",
    "accent": "#4f8cff", "ok": "#3ddc97", "warn": "#ffb84d", "err": "#ff5d6c",
    "listen": "#3ddc97", "trans": "#b48cff",
}
FRAME_MS = 15   # ~60 FPS


def mische(c1, c2, t):
    """Mischt zwei Hex-Farben (t=0 -> c1, t=1 -> c2)."""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(x + (y - x) * t) for x, y in zip(a, b))


def zeit_format(sekunden):
    """Wissenschaftliche Notation mit 4 signifikanten Stellen, z. B. 3.214e-06 s."""
    return f"{sekunden:.3e} s"


STOPP_PLATZ = dict(relx=1.0, rely=1.0, x=-10, y=-10, anchor="se")   # Position unten rechts in der Status-Animation


def stopp_knopf(root, eltern):
    """Erstellt den roten Stopp-Knopf (Esc löst ihn ebenfalls aus). Er wird erst bei Aktivität angezeigt
    (siehe Gui.setze_zustand)."""
    btn = tk.Button(eltern, text="■ Stopp", command=stopp_anfrage, bg=F["err"], fg="white",
                    activebackground=mische(F["err"], "#ffffff", 0.2), activeforeground="white",
                    relief="flat", font=("Segoe UI", 10, "bold"), padx=14, pady=4,
                    cursor="hand2")
    root.bind("<Escape>", lambda e: stopp_anfrage())
    return btn


class Tooltip:
    """Kleiner Hilfetext beim Darüberfahren mit der Maus."""

    def __init__(self, widget, text):
        self.widget, self.text, self.tip = widget, text, None
        widget.bind("<Enter>", self.zeige, add="+")
        widget.bind("<Leave>", self.verstecke, add="+")

    def zeige(self, _e=None):
        """Zeigt den Hilfetext unterhalb des Widgets an."""
        if self.tip:
            return
        x = self.widget.winfo_rootx() + 16
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=self.text, bg=F["rand"], fg=F["text"], font=("Segoe UI", 9),
                 padx=9, pady=5, justify="left", wraplength=340).pack()

    def verstecke(self, _e=None):
        """Entfernt den Hilfetext wieder."""
        if self.tip:
            self.tip.destroy()
            self.tip = None


class Haken(tk.Frame):
    """Eigene Checkbox: weißer Rahmen und weißer Haken.
    Mit an_aus=("aktiviert", "deaktiviert") zeigt sie daneben einen grünen/roten Statustext."""

    def __init__(self, parent, var, command=None, text="", bg=F["card"], fg=F["text"],
                 an_aus=None):
        super().__init__(parent, bg=bg)
        self.var, self.command, self.aktiv = var, command, True
        self.fg, self.an_aus = fg, an_aus
        self.canvas = tk.Canvas(self, width=22, height=22, bg=bg, highlightthickness=0,
                                cursor="hand2")
        self.canvas.pack(side="left")
        self.label = None
        if text or an_aus:
            self.label = tk.Label(self, text=text, bg=bg, fg=fg, cursor="hand2", anchor="w",
                                  font=("Segoe UI", 10, "bold" if an_aus else "normal"),
                                  width=11 if an_aus else 0)
            self.label.pack(side="left", padx=(6, 0))
            self.label.bind("<Button-1>", self.klick)
        self.canvas.bind("<Button-1>", self.klick)
        var.trace_add("write", lambda *_: self.zeichne())
        self.zeichne()

    def klick(self, _e=None):
        """Schaltet den Haken um (nur wenn das Element aktiv ist) und ruft die angegebene Funktion auf."""
        if not self.aktiv:
            return
        self.var.set(not self.var.get())
        if self.command:
            self.command()

    def setze_aktiv(self, aktiv):
        """Aktiviert oder deaktiviert das Element. Ein deaktiviertes Element reagiert nicht auf Klicks und wird abgedunkelt."""
        self.aktiv = aktiv
        if self.label and not self.an_aus:
            self.label.config(fg=self.fg if aktiv else F["rand"])
        self.zeichne()

    def zeichne(self):
        """Zeichnet Rahmen und Haken neu und passt den Statustext an."""
        c = self.canvas
        c.delete("all")
        an = self.var.get()
        farbe = F["weiss"] if self.aktiv else F["rand"]
        c.create_rectangle(3, 3, 19, 19, outline=farbe, width=2)
        if an:
            c.create_line(6, 11, 10, 15, 16, 6, fill=farbe, width=3,
                          capstyle="round", joinstyle="round")
        if self.an_aus and self.label:
            self.label.config(text=self.an_aus[0] if an else self.an_aus[1],
                              fg=F["ok"] if an else F["err"])


def spinner_werte(jetzt):
    """Glatte, zeitbasierte Spinner-Animation: rotierender Bogen mit pulsierender Länge."""
    start = -(jetzt * 280) % 360
    extent = 50 + 190 * (0.5 + 0.5 * math.sin(jetzt * 3.2))
    return start, extent


class SystemKarte:
    """Eine Karte pro System mit Spinner, Live-Zeit, Endzeit und Ergebnis."""

    def __init__(self, parent, name, aktiv, on_toggle):
        self.name = name
        self.zustand = "ungeladen"   # ungeladen, laden, bereit, wartet, laeuft, fertig, fehler
        self.in_runde = False
        self.t_start = 0.0
        self.dauer = None
        self.ladezeit = None
        self._zeit_text = ""
        self.var = tk.BooleanVar(value=aktiv)

        self.frame = tk.Frame(parent, bg=F["card"], highlightthickness=1,
                              highlightbackground=F["rand"])
        kopf = tk.Frame(self.frame, bg=F["card"])
        kopf.pack(fill="x", padx=12, pady=(10, 2))

        # Symbol-Canvas: alle Elemente einmal anlegen, später nur umschalten (flüssiger)
        self.canvas = c = tk.Canvas(kopf, width=30, height=30, bg=F["card"],
                                    highlightthickness=0)
        c.pack(side="left")
        self.i_ring = c.create_oval(4, 4, 26, 26, outline=F["rand"], width=3)
        self.i_arc = c.create_arc(4, 4, 26, 26, start=90, extent=90, style="arc",
                                  outline=F["accent"], width=3)
        self.i_punkt = c.create_oval(11, 11, 19, 19, fill=F["ok"], outline="")
        self.i_voll = c.create_oval(3, 3, 27, 27, fill=F["ok"], outline="")
        self.i_text = c.create_text(15, 15, text="✓", fill=F["bg"],
                                    font=("Segoe UI", 12, "bold"))
        self.i_gestrichelt = c.create_oval(5, 5, 25, 25, outline=F["sub"], width=2,
                                           dash=(3, 3))

        mitte = tk.Frame(kopf, bg=F["card"])
        mitte.pack(side="left", fill="x", expand=True, padx=10)
        self.name_lbl = tk.Label(mitte, text=name, font=("Segoe UI", 12, "bold"),
                                 bg=F["card"], fg=F["text"], anchor="w")
        self.name_lbl.pack(fill="x")
        self.sub_lbl = tk.Label(mitte, text="", font=("Segoe UI", 9),
                                bg=F["card"], fg=F["sub"], anchor="w")
        self.sub_lbl.pack(fill="x")

        self.check = Haken(kopf, self.var, command=lambda: on_toggle(name),
                           an_aus=("aktiviert", "deaktiviert"), bg=F["card"], fg=F["text"])
        self.check.pack(side="right", padx=(8, 0))
        Tooltip(self.check, "Wenn aktiviert, erkennt dieses System bei der nächsten Eingabe "
                            "den Befehl. Mindestens ein System muss aktiviert bleiben.")
        self.zeit_lbl = tk.Label(kopf, text="", font=("Consolas", 14, "bold"),
                                 bg=F["card"], fg=F["sub"], width=13, anchor="e")
        self.zeit_lbl.pack(side="right")
        Tooltip(self.zeit_lbl, "Gesamtdauer dieses Systems (Intent + Parameter).")

        unten = tk.Frame(self.frame, bg=F["card"])
        unten.pack(fill="x", padx=(54, 12), pady=(0, 8))
        self.split_lbl = tk.Label(unten, text="", font=("Consolas", 9), justify="left",
                                  anchor="ne", bg=F["card"], fg=F["sub"])
        self.split_lbl.pack(side="right", anchor="n", padx=(10, 0))
        Tooltip(self.split_lbl, "Intent = Erkennung, welcher Befehl gemeint ist. "
                                "Parameter = Extraktion der Werte (z. B. Ort, Zahl, Titel).")
        self.ergebnis = tk.Label(unten, text="", font=("Consolas", 10), justify="left",
                                 anchor="w", bg=F["card"], fg=F["text"], wraplength=330)
        self.ergebnis.pack(side="left", fill="x", expand=True)

        self.setze("ungeladen")
        self.dimmen()

    def dimmen(self):
        """Stellt den Namen heller oder dunkler dar, je nachdem, ob das System aktiviert ist."""
        self.name_lbl.config(fg=F["text"] if self.var.get() else F["sub"])

    def _symbol(self):
        """Zeigt das zum aktuellen Zustand passende Symbol (Ring, Punkt, Haken, Ausrufezeichen ...)."""
        c, z = self.canvas, self.zustand
        for i in (self.i_ring, self.i_arc, self.i_punkt, self.i_voll, self.i_text,
                  self.i_gestrichelt):
            c.itemconfigure(i, state="hidden")
        if z in ("laeuft", "laden"):
            c.itemconfigure(self.i_ring, state="normal")
            c.itemconfigure(self.i_arc, state="normal",
                            outline=F["accent"] if z == "laeuft" else F["warn"])
        elif z == "fertig":
            c.itemconfigure(self.i_voll, state="normal", fill=F["ok"])
            c.itemconfigure(self.i_text, state="normal", text="✓")
        elif z == "fehler":
            c.itemconfigure(self.i_voll, state="normal", fill=F["err"])
            c.itemconfigure(self.i_text, state="normal", text="!")
        elif z == "wartet":
            c.itemconfigure(self.i_gestrichelt, state="normal")
        elif z == "bereit":
            c.itemconfigure(self.i_ring, state="normal")
            c.itemconfigure(self.i_punkt, state="normal")
        else:
            c.itemconfigure(self.i_ring, state="normal")

    def _setze_zeit(self, text, farbe):
        """Aktualisiert den Zeittext und seine Farbe (Text nur bei Änderung, damit die Anzeige nicht flackert)."""
        if text != self._zeit_text:
            self._zeit_text = text
            self.zeit_lbl.config(text=text)
        self.zeit_lbl.config(fg=farbe)

    def setze(self, zustand, dauer=None):
        """Setzt den Zustand der Karte («ungeladen», «laden», «bereit», «wartet», «laeuft», «fertig», «fehler»).
        Bei «fertig» wird zusätzlich die Dauer in Sekunden angezeigt.
        """
        self.zustand = zustand
        if zustand in ("laden", "laeuft"):
            self.t_start = perf_counter()
        texte = {
            "ungeladen": "nicht geladen",
            "laden": "lädt & wärmt auf …",
            "wartet": "wartet …",
            "laeuft": "überlegt …",
            "fehler": "Fehler",
            "fertig": "fertig",
        }
        if zustand == "bereit":
            text = f"bereit (Ladezeit {self.ladezeit:.1f} s)" if self.ladezeit else "bereit"
        else:
            text = texte.get(zustand, "")
        self.sub_lbl.config(text=text)
        if zustand == "fertig":
            self.dauer = dauer
            if dauer is not None:
                self._setze_zeit(zeit_format(dauer), F["ok"])
            else:
                self._setze_zeit("–", F["sub"])
        elif zustand in ("bereit", "wartet", "ungeladen"):
            self._setze_zeit("", F["sub"])
        self._symbol()

    def setze_split(self, zeiten):
        """zeiten = (t_intent, t_params, t_gesamt) oder None."""
        if zeiten is None:
            text = "Intent:    –\nParameter: –"
        elif zeiten[0] is None:
            text = "Intent + Parameter:\nein Aufruf (nicht trennbar)"
        else:
            text = (f"Intent:    {zeit_format(zeiten[0])}\n"
                    f"Parameter: {zeit_format(zeiten[1])}")
        self.split_lbl.config(text=text)

    def tick(self, jetzt):
        """Wird bei jedem Bild aufgerufen: dreht den Spinner weiter und zeigt die laufende Zeit."""
        if self.zustand in ("laeuft", "laden"):
            start, extent = spinner_werte(jetzt)
            self.canvas.itemconfigure(self.i_arc, start=start, extent=extent)
            farbe = F["accent"] if self.zustand == "laeuft" else F["warn"]
            self._setze_zeit(f"{jetzt - self.t_start:.1f} s", farbe)


class Splash:
    """Ladebildschirm: zeigt, welche Systeme gerade geladen werden."""

    def __init__(self, root, namen):
        self.namen = namen
        self.status = {n: ("wartet", None) for n in namen}   # (zustand, startzeit/dauer)
        self.frame = tk.Frame(root, bg=F["bg"])
        self.frame.pack(fill="both", expand=True)

        tk.Label(self.frame, text="Systeme werden geladen …", font=("Segoe UI", 20, "bold"),
                 bg=F["bg"], fg=F["text"]).pack(pady=(50, 8))
        self.spinner = tk.Canvas(self.frame, width=80, height=80, bg=F["bg"],
                                 highlightthickness=0)
        self.spinner.pack(pady=22)
        self.spinner.create_oval(8, 8, 72, 72, outline=F["rand"], width=5)
        self.arc = self.spinner.create_arc(8, 8, 72, 72, start=90, extent=90, style="arc",
                                           outline=F["accent"], width=5)

        self.balken = tk.Canvas(self.frame, width=440, height=8, bg=F["card"],
                                highlightthickness=0)
        self.balken.pack()
        self.fuell = self.balken.create_rectangle(0, 0, 0, 8, fill=F["accent"], outline="")

        liste = tk.Frame(self.frame, bg=F["bg"])
        liste.pack(pady=16)
        self.zeilen = {}
        for n in namen:
            zeile = tk.Frame(liste, bg=F["bg"])
            zeile.pack(fill="x", pady=3)
            ico = tk.Label(zeile, text="○", width=2, font=("Segoe UI", 12),
                           bg=F["bg"], fg=F["sub"])
            ico.pack(side="left")
            tk.Label(zeile, text=n, width=22, anchor="w", font=("Segoe UI", 11),
                     bg=F["bg"], fg=F["text"]).pack(side="left")
            st = tk.Label(zeile, text="wartet", width=18, anchor="w", font=("Consolas", 10),
                          bg=F["bg"], fg=F["sub"])
            st.pack(side="left")
            self.zeilen[n] = (ico, st)

    def tick(self):
        """Liest die Lade-Nachrichten aus gui_queue, aktualisiert Liste und Fortschrittsbalken und dreht den Spinner."""
        try:
            while True:
                e = gui_queue.get_nowait()
                if e[0] == "prep_start" and e[1] in self.status:
                    self.status[e[1]] = ("laedt", perf_counter())
                elif e[0] == "prep_done" and e[1] in self.status:
                    self.status[e[1]] = ("fertig", e[2])
                elif e[0] == "system_fehler" and e[1] in self.status:
                    self.status[e[1]] = ("fehler", None)
        except queue.Empty:
            pass

        jetzt = perf_counter()
        start, extent = spinner_werte(jetzt)
        self.spinner.itemconfigure(self.arc, start=start, extent=extent)

        fertig = 0
        for n, (zustand, wert) in self.status.items():
            ico, st = self.zeilen[n]
            if zustand == "laedt":
                ico.config(text="◔", fg=F["warn"])
                st.config(text=f"lädt … {jetzt - wert:.1f} s", fg=F["warn"])
            elif zustand == "fertig":
                fertig += 1
                ico.config(text="✓", fg=F["ok"])
                st.config(text=f"bereit · {wert:.1f} s", fg=F["ok"])
            elif zustand == "fehler":
                fertig += 1
                ico.config(text="✗", fg=F["err"])
                st.config(text="Fehler", fg=F["err"])
        self.balken.coords(self.fuell, 0, 0, 440 * fertig / max(1, len(self.namen)), 8)


class Gui:
    """Hauptfenster des Testmodus: links Statusanzeige (mit Stopp-Knopf), Eingabe/Ausgabe, Texteingabe und Schalter «Befehl ausführen»,
    rechts eine Karte pro System mit Schalter, Dauer und Ergebnis.
    """
    ZUSTAENDE = {
        "idle": ("Bereit", "Sage „Hey Jarvis“ zum Starten"),
        "zuhoeren": ("Ich höre zu …", "Wakeword erkannt – sprich jetzt"),
        "transkribieren": ("Transkribiere …", "Sprache wird in Text umgewandelt"),
        "verarbeiten": ("Systeme überlegen …", "Der Befehl wird erkannt"),
        "ausfuehren": ("Führe Befehl aus …", "Ausführung & Sprachausgabe"),
    }

    def __init__(self, root, systeme, on_systeme, on_text, on_do_befehl):
        """Baut das Fenster auf.

        Parameter:
            root: Tk-Hauptfenster.
            systeme: Namen aller Systeme (eine Karte pro System).
            on_systeme: Funktion, die beim (De-)Aktivieren eines Systems aufgerufen wird (bekommt den Namen).
            on_text: Funktion, die mit einem eingetippten Satz aufgerufen wird.
            on_do_befehl: Funktion, die aufgerufen wird, wenn «Erkannten Befehl ausführen» umgeschaltet wird (bekommt True/False).
        """
        self.root = root
        self.on_text = on_text
        self.zustand = "idle"
        self.zustand_start = perf_counter()

        root.title("Sprachassistent – Testmodus")
        root.geometry("1120x700")
        root.minsize(1000, 660)
        root.configure(bg=F["bg"])

        def abschnitt(eltern, text, hinweis):
            tk.Label(eltern, text=text, font=("Segoe UI", 11, "bold"), bg=F["bg"],
                     fg=F["text"], anchor="w").pack(fill="x", pady=(10, 0))
            tk.Label(eltern, text=hinweis, font=("Segoe UI", 9), bg=F["bg"], fg=F["sub"],
                     anchor="w", justify="left", wraplength=430).pack(fill="x")

        kopf = tk.Frame(root, bg=F["bg"])
        kopf.pack(fill="x", padx=20, pady=(12, 0))
        tk.Label(kopf, text="Sprachassistent", font=("Segoe UI", 18, "bold"),
                 bg=F["bg"], fg=F["text"]).pack(side="left")
        tk.Label(kopf, text="Testmodus – vergleiche, wie gut und wie schnell die Systeme sind",
                 font=("Segoe UI", 10), bg=F["bg"], fg=F["sub"]).pack(side="left",
                                                                      padx=14, pady=(7, 0))

        inhalt = tk.Frame(root, bg=F["bg"])
        inhalt.pack(fill="both", expand=True, padx=20, pady=(0, 14))
        inhalt.columnconfigure(0, weight=2, uniform="spalte")
        inhalt.columnconfigure(1, weight=3, uniform="spalte")
        inhalt.rowconfigure(0, weight=1)
        links = tk.Frame(inhalt, bg=F["bg"])
        links.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        rechts = tk.Frame(inhalt, bg=F["bg"])
        rechts.grid(row=0, column=1, sticky="nsew")

        # ----- Linke Spalte -----
        # Status-Animation
        status_rahmen = tk.Frame(links, bg=F["card"], highlightthickness=1,
                                 highlightbackground=F["rand"])
        status_rahmen.pack(fill="x", pady=(8, 0))
        self.status_canvas = tk.Canvas(status_rahmen, height=124, bg=F["card"],
                                       highlightthickness=0)
        self.status_canvas.pack(fill="x")
        self.stopp_btn = stopp_knopf(root, self.status_canvas)   # Stopp-Knopf (nur sichtbar bei Aktivität)
        Tooltip(self.status_canvas, "Zeigt, was der Assistent gerade macht: warten, zuhören, "
                                    "transkribieren, Befehl erkennen oder ausführen.")

        # Erkannter Text (markiert, zentriert)
        abschnitt(links, "Erkannter Text & Ausgabe",
                  "Oben steht, was der Assistent verstanden hat (gesprochen oder getippt), "
                  "unten seine Antwort – sie erscheint schon vor der Sprachausgabe. "
                  "Darunter steht die Gesamtzeit.")
        box_bg = mische(F["accent"], F["bg"], 0.85)
        box = tk.Frame(links, bg=box_bg, highlightthickness=2, highlightbackground=F["accent"])
        box.pack(fill="x", pady=(4, 0))
        tk.Label(box, text="EINGABE", font=("Segoe UI", 8, "bold"), bg=box_bg,
                 fg=F["accent"]).pack(pady=(6, 0))
        self.input_lbl = tk.Label(box, text="Noch kein Text erkannt", font=("Segoe UI", 13, "bold"),
                                  bg=box_bg, fg=F["sub"], wraplength=400, justify="center",
                                  height=2)
        self.input_lbl.pack(fill="x", padx=10, pady=(0, 4))
        tk.Frame(box, bg=F["accent"], height=1).pack(fill="x", padx=24)
        tk.Label(box, text="AUSGABE", font=("Segoe UI", 8, "bold"), bg=box_bg,
                 fg=F["ok"]).pack(pady=(5, 0))
        self.ausgabe_txt = tk.Text(box, height=3, width=36, wrap="word",
                                   font=("Segoe UI", 12, "bold"), bg=box_bg, fg=F["sub"],
                                   relief="flat", highlightthickness=0, bd=0, cursor="arrow",
                                   padx=10, pady=2)
        self.ausgabe_txt.tag_configure("mitte", justify="center")
        self.ausgabe_txt.pack(fill="x", padx=10, pady=(0, 8))
        Tooltip(self.ausgabe_txt, "Antwort des Assistenten (wird auch vorgelesen). "
                                  "Bei langen Texten mit dem Mausrad scrollen.")
        self.setze_ausgabe("Noch keine Ausgabe", F["sub"])
        self.gesamt_lbl = tk.Label(links, text="", font=("Consolas", 11, "bold"),
                                   bg=F["bg"], fg=F["text"])
        self.gesamt_lbl.pack(pady=(4, 0))

        # Texteingabe
        abschnitt(links, "Manuelle Texteingabe",
                  "Tippe einen Befehl ein statt zu sprechen und drücke Enter oder „Senden“.")
        eingabe = tk.Frame(links, bg=F["bg"])
        eingabe.pack(fill="x", pady=(4, 0))
        self.entry = tk.Entry(eingabe, font=("Segoe UI", 11), bg=F["card2"], fg=F["text"],
                              insertbackground=F["text"], relief="flat",
                              highlightthickness=1, highlightbackground=F["rand"],
                              highlightcolor=F["accent"])
        self.entry.pack(side="left", fill="x", expand=True, ipady=7, padx=(0, 10))
        self.entry.bind("<Return>", lambda e: self.senden())
        tk.Button(eingabe, text="Senden", command=self.senden, bg=F["accent"], fg="white",
                  activebackground=mische(F["accent"], "#ffffff", 0.2), activeforeground="white",
                  relief="flat", font=("Segoe UI", 10, "bold"), padx=18, pady=6,
                  cursor="hand2").pack(side="left")

        # Befehle ausführen
        abschnitt(links, "Befehle ausführen",
                  "Führt den erkannten Befehl wirklich aus und spricht die Antwort. "
                  "Nur möglich, wenn genau ein System aktiviert ist.")
        self.do_var = tk.BooleanVar(value=False)
        self.do_cb = Haken(links, self.do_var, text="Erkannten Befehl ausführen",
                           command=lambda: on_do_befehl(self.do_var.get()),
                           bg=F["bg"], fg=F["text"])
        self.do_cb.pack(anchor="w", pady=(4, 0))

        # ----- Rechte Spalte: Systemkarten -----
        tk.Label(rechts, text="Systeme", font=("Segoe UI", 11, "bold"), bg=F["bg"],
                 fg=F["text"], anchor="w").pack(fill="x", pady=(10, 0))
        tk.Label(rechts, text="Aktiviere oder deaktiviere die Systeme. Aktivierte Systeme "
                              "erkennen denselben Text nacheinander, jeweils mit Zeitmessung. "
                              "Mindestens eines muss aktiviert bleiben.",
                 font=("Segoe UI", 9), bg=F["bg"], fg=F["sub"], anchor="w", justify="left",
                 wraplength=620).pack(fill="x", pady=(0, 4))
        self.karten = {}
        for name in systeme:
            karte = SystemKarte(rechts, name, name in methoden, on_systeme)
            if name in bereit:                      # bereits geladen (Splash)
                karte.ladezeit = ladezeiten.get(name)
                karte.setze("bereit")
            karte.frame.pack(fill="x", pady=3)
            self.karten[name] = karte

        self.tick()

    # --- Eingabe -------------------------------------------------------
    def senden(self):
        """Liest den eingetippten Satz aus dem Eingabefeld, leert es und übergibt den Satz an on_text."""
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, tk.END)
        self.on_text(text)

    # --- Zustand -------------------------------------------------------
    def setze_ausgabe(self, text, farbe):
        """Zeigt den Antworttext im Ausgabefeld (zentriert) in der angegebenen Farbe."""
        t = self.ausgabe_txt
        t.config(state="normal")
        t.delete("1.0", tk.END)
        t.insert("1.0", text, "mitte")
        t.config(state="disabled", fg=farbe)
        t.yview_moveto(0)

    def setze_zustand(self, zustand):
        """Setzt den Zustand der Status-Animation (siehe ZUSTAENDE), merkt sich den Startzeitpunkt
        und zeigt den Stopp-Knopf nur an, wenn der Assistent nicht im Zustand «idle» ist."""
        self.zustand = zustand
        self.zustand_start = perf_counter()
        if zustand == "idle":
            self.stopp_btn.place_forget()
        else:
            self.stopp_btn.place(**STOPP_PLATZ)

    def ereignis(self, e):
        """Verarbeitet eine Nachricht aus gui_queue. Eine Nachricht ist ein Tupel (Typ, Daten...). Bekannte Typen:
          zustand (Name) - Zustand der Status-Animation
          input (Text) - erkannter oder eingegebener Satz
          ausgabe (Text oder None) - Antwort des Assistenten
          runde_start (Liste der aktiven Systeme) - neue Verarbeitung beginnt
          system_start (Name) / phase (Name, "intent", "parameter" oder "gesamt") - ein System rechnet
          prep_start (Name) / prep_done (Name, Dauer) - ein System wird geladen
          system_done (Name, Befehl, Zeiten) / system_fehler (Name, Text) - Ergebnis eines Systems
          abgebrochen - die Anfrage wurde mit dem Stopp-Knopf beendet
          fertig (Gesamtdauer) - Verarbeitung abgeschlossen
        """
        typ = e[0]
        if typ == "zustand":
            self.setze_zustand(e[1])
        elif typ == "input":
            self.input_lbl.config(text=f"„{e[1]}“", fg=F["weiss"])
        elif typ == "ausgabe":
            if e[1] is None:
                self.setze_ausgabe("Keine Ausgabe – „Befehle ausführen“ ist aus oder es sind "
                                   "mehrere Systeme aktiviert", F["sub"])
            else:
                self.setze_ausgabe(e[1], F["weiss"])
        elif typ == "runde_start":
            self.gesamt_lbl.config(text="")
            self.setze_ausgabe("–", F["sub"])
            for name, k in self.karten.items():
                k.ergebnis.config(text="")
                k.split_lbl.config(text="")
                k.dauer = None
                if name in e[1]:
                    k.in_runde = True
                    if k.zustand != "laden":
                        k.setze("wartet")
                elif k.zustand not in ("ungeladen", "laden"):
                    k.setze("bereit")
        elif typ == "system_start":
            k = self.karten[e[1]]
            if k.zustand != "laden":
                k.setze("laeuft")
        elif typ == "phase":
            k = self.karten[e[1]]
            if k.zustand == "laeuft":
                k.sub_lbl.config(text={"intent": "erkennt Intent …",
                                       "parameter": "extrahiert Parameter …",
                                       "gesamt": "überlegt …"}[e[2]])
        elif typ == "prep_start":
            self.karten[e[1]].setze("laden")
        elif typ == "prep_done":
            k = self.karten[e[1]]
            k.ladezeit = e[2]
            k.setze("laeuft" if k.in_runde else "bereit")
        elif typ == "system_done":
            k = self.karten[e[1]]
            k.in_runde = False
            k.setze("fertig", e[3][2] if e[3] else None)
            k.setze_split(e[3])
            k.ergebnis.config(text=befehl_beschreiben(e[2]), fg=F["text"])
        elif typ == "system_fehler":
            k = self.karten[e[1]]
            k.in_runde = False
            k.setze("fehler")
            k._setze_zeit("–", F["err"])
            k.ergebnis.config(text=f"Fehler: {e[2]}", fg=F["err"])
        elif typ == "abgebrochen":
            self.gesamt_lbl.config(text="Abgebrochen")
            self.setze_ausgabe("Anfrage abgebrochen", F["warn"])
            for k in self.karten.values():
                if k.zustand in ("wartet", "laeuft"):
                    k.in_runde = False
                    k.setze("bereit")
                    k.ergebnis.config(text="")
                    k.split_lbl.config(text="")
        elif typ == "fertig":
            self.gesamt_lbl.config(text=f"Gesamtzeit: {zeit_format(e[1])}")
            fertige = [k for k in self.karten.values() if k.dauer is not None]
            if len(fertige) >= 2:
                langsam = max(fertige, key=lambda k: k.dauer)
                schnell = min(fertige, key=lambda k: k.dauer)
                langsam._setze_zeit(zeit_format(langsam.dauer), F["warn"])
                langsam.sub_lbl.config(text="fertig · langsamstes")
                schnell.sub_lbl.config(text="fertig · schnellstes")

    # --- Animationen ---------------------------------------------------
    def zeichne_status(self, jetzt):
        """Zeichnet die Animation für den aktuellen Zustand (warten, zuhören, transkribieren, verarbeiten, ausführen) samt Titel und Zeit."""
        c = self.status_canvas
        c.delete("all")
        cx, cy = 70, 62
        z = self.zustand
        titel, untertitel = self.ZUSTAENDE[z]
        verstrichen = jetzt - self.zustand_start

        if z == "idle":
            puls = 0.5 + 0.5 * math.sin(jetzt * 1.8)
            farbe = mische(F["rand"], F["sub"], puls)
            c.create_oval(cx - 26, cy - 26, cx + 26, cy + 26, outline=farbe, width=3)
            c.create_oval(cx - 7, cy - 7, cx + 7, cy + 7, fill=farbe, outline="")
        elif z == "zuhoeren":
            for i in range(3):
                phase = (jetzt * 0.9 + i / 3) % 1
                r = 24 + phase * 34
                c.create_oval(cx - r, cy - r, cx + r, cy + r,
                              outline=mische(F["listen"], F["card"], phase), width=3)
            c.create_oval(cx - 24, cy - 24, cx + 24, cy + 24, fill=F["listen"], outline="")
            c.create_rectangle(cx - 5, cy - 13, cx + 5, cy + 4, fill=F["card"], outline="")
            c.create_arc(cx - 11, cy - 7, cx + 11, cy + 13, start=180, extent=180,
                         style="arc", outline=F["card"], width=3)
            c.create_line(cx, cy + 13, cx, cy + 18, fill=F["card"], width=3)
        elif z == "transkribieren":
            for i in range(9):
                h = 6 + 24 * abs(math.sin(jetzt * 4 + i * 0.6))
                x = cx - 48 + i * 12
                c.create_rectangle(x, cy - h, x + 7, cy + h, fill=F["trans"], outline="")
        elif z == "verarbeiten":
            for i in range(14):
                ang = jetzt * 5 - i * 0.3
                s = 7 - i * 0.4
                x, y = cx + 30 * math.cos(ang), cy + 30 * math.sin(ang)
                c.create_oval(x - s, y - s, x + s, y + s,
                              fill=mische(F["accent"], F["card"], i / 15), outline="")
        else:  # ausfuehren
            r = 20 + 6 * math.sin(jetzt * 6)
            c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=F["ok"], outline="")
            c.create_oval(cx - r - 10, cy - r - 10, cx + r + 10, cy + r + 10,
                          outline=mische(F["ok"], F["card"], 0.6), width=2)

        farbe_titel = {"zuhoeren": F["listen"], "transkribieren": F["trans"],
                       "verarbeiten": F["accent"], "ausfuehren": F["ok"]}.get(z, F["text"])
        c.create_text(145, 42, text=titel, anchor="w", fill=farbe_titel,
                      font=("Segoe UI", 18, "bold"))
        c.create_text(145, 68, text=untertitel, anchor="w", fill=F["sub"],
                      font=("Segoe UI", 10))
        if z != "idle":
            c.create_text(145, 92, text=f"{verstrichen:.1f} s", anchor="w", fill=F["sub"],
                          font=("Consolas", 11))

    def tick(self):
        """Wird alle FRAME_MS Millisekunden aufgerufen: verarbeitet neue Nachrichten, zeichnet die Animation und aktualisiert die Karten."""
        try:
            while True:
                self.ereignis(gui_queue.get_nowait())
        except queue.Empty:
            pass
        jetzt = perf_counter()
        self.zeichne_status(jetzt)
        for k in self.karten.values():
            k.tick(jetzt)
        self.root.after(FRAME_MS, self.tick)


class MiniGui(Gui):
    """Minimales Fenster für den Ein-System-Modus: Status-Animation, Stopp-Knopf
    und ein kleines Feld für die manuelle Texteingabe."""

    def __init__(self, root, on_text):
        # bewusst kein Gui.__init__: keine Karten, Texte oder Schalter
        self.root = root
        self.on_text = on_text
        self.zustand = "idle"
        self.zustand_start = perf_counter()
        self.karten = {}                      # leer, damit Gui.tick() wiederverwendet werden kann

        root.title("Sprachassistent")
        root.geometry("470x210")              # etwas höher wegen des Eingabefelds
        root.resizable(False, False)
        root.configure(bg=F["bg"])

        rahmen = tk.Frame(root, bg=F["card"], highlightthickness=1,
                          highlightbackground=F["rand"])
        rahmen.pack(fill="both", expand=True, padx=14, pady=(14, 6))
        self.status_canvas = tk.Canvas(rahmen, height=124, bg=F["card"], highlightthickness=0)
        self.status_canvas.pack(fill="both", expand=True)
        self.stopp_btn = stopp_knopf(root, self.status_canvas)

        # Manuelle Texteingabe
        eingabe = tk.Frame(root, bg=F["bg"])
        eingabe.pack(fill="x", padx=14, pady=(0, 12))
        self.entry = tk.Entry(eingabe, font=("Segoe UI", 11), bg=F["card2"], fg=F["text"],
                              insertbackground=F["text"], relief="flat",
                              highlightthickness=1, highlightbackground=F["rand"],
                              highlightcolor=F["accent"])
        self.entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))
        self.entry.bind("<Return>", lambda e: self.senden())
        tk.Button(eingabe, text="Senden", command=self.senden, bg=F["accent"], fg="white",
                  activebackground=mische(F["accent"], "#ffffff", 0.2), activeforeground="white",
                  relief="flat", font=("Segoe UI", 10, "bold"), padx=14, pady=4,
                  cursor="hand2").pack(side="left")

        self.tick()

    # senden() wird von Gui geerbt: liest self.entry, leert es und ruft self.on_text(text) auf

    def ereignis(self, e):
        """Beachtet nur Nachrichten vom Typ «zustand»; alle anderen werden in diesem Fenster ignoriert."""
        if e[0] == "zustand":
            self.setze_zustand(e[1])

def window(mini=False):
    """Erstellt und betreibt das Tk-Fenster (läuft in einem eigenen Thread, startet die Tk-Hauptschleife).

    Parameter:
        mini: True = kleines Fenster nur mit Status-Animation (Betriebsmodus); False = Testmodus mit Ladebildschirm
              (Splash) und danach dem vollständigen Fenster (Gui).
    Beim Schliessen des Fensters werden die Ollama-Modelle entladen, der Audiostream beendet und das Programm beendet.
    """
    global methoden, do_befehl
    fenster = tk.Tk()
    fenster.title("Sprachassistent" if mini else "Sprachassistent – Testmodus")
    fenster.geometry("470x210" if mini else "1120x700")
    fenster.configure(bg=F["bg"])


    def fenster_schliessen():
        """Beendet das Programm sauber: Modelle entladen, Audiostream schliessen, Prozess beenden."""
        print("\nBeende Programm")
        modelle_entladen()
        print("Beende Audioaufnahme")
        stream.stop_stream()
        stream.close()
        pyaudio_PyAudio.terminate()
        os._exit(0)

    fenster.protocol("WM_DELETE_WINDOW", fenster_schliessen)

    if mini:                                  # Ein-System-Modus: System ist schon geladen
        def text_senden_mini(text):
            """Verarbeitet einen eingetippten Satz in einem eigenen Thread."""
            threading.Thread(target=text_verarbeitung, args=(text,), daemon=True).start()

        MiniGui(fenster, text_senden_mini)
        gui_bereit.set()
        fenster.mainloop()
        return

    def starte_gui():
        """Verwirft übrig gebliebene Lade-Nachrichten und öffnet das Hauptfenster (Gui) anstelle des Ladebildschirms."""
        # Reste aus der Queue verwerfen (Ladeereignisse)
        try:
            while True:
                gui_queue.get_nowait()
        except queue.Empty:
            pass

        def systeme_geaendert(name):
            """Wird aufgerufen, wenn ein System (de-)aktiviert wird. Mindestens ein System bleibt aktiv.
            Aktualisiert die Liste «methoden». «Befehl ausführen» ist nur bei genau einem aktiven System möglich.
            """
            global methoden, do_befehl
            ausgewaehlt = [s for s, k in gui.karten.items() if k.var.get()]
            if not ausgewaehlt:                   # mindestens eines muss aktiv bleiben
                gui.karten[name].var.set(True)
                return
            methoden = ausgewaehlt
            gui.karten[name].dimmen()
            if gui.karten[name].var.get() and name not in bereit:
                vorbereiten_starten([name])       # Sicherheitsnetz, falls Laden fehlschlug
            if len(ausgewaehlt) == 1:
                gui.do_cb.setze_aktiv(True)
            else:
                gui.do_var.set(False)
                gui.do_cb.setze_aktiv(False)
                do_befehl = False
            print("Ausgewählte Systeme:", methoden, "| do_befehl:", do_befehl)

        def setze_do_befehl(wert):
            """Merkt sich, ob der erkannte Befehl wirklich ausgeführt werden soll (globale Variable do_befehl)."""
            global do_befehl
            do_befehl = wert
            print("do_befehl:", do_befehl)

        def text_senden(text):
            """Verarbeitet einen eingetippten Satz in einem eigenen Thread, damit die Oberfläche nicht blockiert."""
            threading.Thread(target=text_verarbeitung, args=(text,), daemon=True).start()

        gui = Gui(fenster, list(SYSTEME), systeme_geaendert, text_senden, setze_do_befehl)
        gui_bereit.set()

    # 1) Zuerst alle Systeme laden (Ladebildschirm), 2) dann das echte GUI öffnen
    print("Systeme werden geladen ...")
    geladen = threading.Event()
    splash = Splash(fenster, list(SYSTEME))
    vorbereiten_starten(list(SYSTEME), geladen)

    def splash_tick():
        """Aktualisiert den Ladebildschirm; sobald alle Systeme geladen sind, wird er durch das Hauptfenster ersetzt."""
        splash.tick()
        if geladen.is_set():
            splash.frame.destroy()
            print("Alle Systeme geladen.")
            starte_gui()
        else:
            fenster.after(FRAME_MS, splash_tick)

    splash_tick()
    fenster.mainloop()


def befehl_ausführen(befehlinformationen):  # [befehlnummer, parameter]
    """Führt einen erkannten Befehl aus.

    Parameter:
        befehlinformationen: Liste [Befehlsnummer, Parameter 1, Parameter 2, ...] (siehe ki_params.llm_params).
    Sind Parameter vorhanden, werden sie an die Befehlsfunktion weitergegeben; sonst wird sie ohne Argumente aufgerufen
    und nutzt ihre Standardwerte oder fragt selbst nach (Befehle/getparam.py).
    Rückgabe: Der Antworttext des Befehls (wird vorgelesen) oder None, wenn der Befehl keinen Text liefert.
    Bei einer unbekannten Nummer: «Unbekannter Befehl». Die Nummern entsprechen BEFEHLSNAMEN.
    """
    # Befehlsnummer dem passenden Befehl zuordnen
    print(befehlinformationen)
    befehl = befehlinformationen[0]

    # 1 = change_brightness
    if befehl == 1:
        if len(befehlinformationen) > 1:
            return change_brightness(befehlinformationen[1])
        return change_brightness()

    # 2 = get_brightness
    elif befehl == 2:
        return get_brightness()

    # 3 = set_brightness
    elif befehl == 3:
        if len(befehlinformationen) > 1:
            return set_brightness(befehlinformationen[1])
        return set_brightness()

    # 4 = check_emails
    elif befehl == 4:
        return check_emails()

    # 5 = einkaufsliste_add
    elif befehl == 5:
        if len(befehlinformationen) > 1:
            return einkaufsliste_add(befehlinformationen[1])
        return einkaufsliste_add()

    # 6 = einkaufsliste_lesen
    elif befehl == 6:
        return einkaufsliste_lesen()

    # 7 = einkaufsliste_neu
    elif befehl == 7:
        return einkaufsliste_neu()

    # 8 = change_volume
    elif befehl == 8:
        if len(befehlinformationen) > 1:
            return change_volume(befehlinformationen[1])
        return change_volume()

    # 9 = get_volume
    elif befehl == 9:
        return get_volume()

    # 10 = set_volume
    elif befehl == 10:
        if len(befehlinformationen) > 1:
            return set_volume(befehlinformationen[1])
        return set_volume()

    # 11 = news
    elif befehl == 11:
        if len(befehlinformationen) > 1:
            return news(befehlinformationen[1])
        return news()

    # 12 = recherchieren
    elif befehl == 12:
        if len(befehlinformationen) > 1:
            return recherchieren(befehlinformationen[1])
        return recherchieren()

    # 13 = route
    elif befehl == 13:
        if len(befehlinformationen) > 3:
            return route(befehlinformationen[1], befehlinformationen[2], befehlinformationen[3])
        elif len(befehlinformationen) > 2:
            return route(befehlinformationen[1], befehlinformationen[2])
        return route()

    # 14 = screenshot
    elif befehl == 14:
        return screenshot()

    # 15 = searchfile
    elif befehl == 15:
        if len(befehlinformationen) > 1:
            return searchfile(befehlinformationen[1])
        return searchfile()

    # 16 = next_track
    elif befehl == 16:
        return next_track()

    # 17 = pause
    elif befehl == 17:
        return pause()

    # 18 = play
    elif befehl == 18:
        return play()

    # 19 = play_song
    elif befehl == 19:
        if len(befehlinformationen) > 2:
            return play_song(befehlinformationen[1], befehlinformationen[2])
        elif len(befehlinformationen) > 1:
            return play_song(befehlinformationen[1])
        return play_song()

    # 20 = previous_track
    elif befehl == 20:
        return previous_track()

    # 21 = start_program
    elif befehl == 21:
        if len(befehlinformationen) > 1:
            return start_program(befehlinformationen[1])
        return start_program()

    # 22 = tag
    elif befehl == 22:
        return tag()

    # 23 = timer_back
    elif befehl == 23:
        if len(befehlinformationen) > 1:
            return timer_back(befehlinformationen[1])
        return timer_back()

    # 24 = translate
    elif befehl == 24:
        if len(befehlinformationen) > 2:
            return translate(
                befehlinformationen[1],
                befehlinformationen[2]
            )
        elif len(befehlinformationen) > 1:
            return translate(befehlinformationen[1])
        return translate()

    # 25 = uhrzeit
    elif befehl == 25:
        return uhrzeit()

    # 26 = get_weather
    elif befehl == 26:
        if len(befehlinformationen) > 1:
            return get_weather(befehlinformationen[1])
        return get_weather()

    # 27 = würfel
    elif befehl == 27:
        return würfel()

    else:
        return "Unbekannter Befehl"


def Main(system = None):
    """Startet den Sprachassistenten und läuft in einer Endlosschleife (Wake Word -> Aufnahme -> Verarbeitung).

    Parameter:
        system: None = Testmodus mit GUI und allen Systemen; sonst Name eines Systems aus SYSTEME (Betriebsmodus mit Mini-Fenster).
    Beendet wird mit Strg+C oder durch Schliessen des Fensters; dabei werden Ollama-Modelle entladen und der Audiostream geschlossen.
    """
    # None = Testmodus mit GUI, sonst gewähltes System (mit Mini-Fenster, das nur die Animationen zeigt)
    global do_befehl
    global methoden

    # Systemauswahl setzen
    if system != None:
        do_befehl = True
        methoden = [system]

    try:
        if system == None:
            # GUI im Testmodus starten
            thread = threading.Thread(target=window, daemon=True)
            thread.start()
            gui_bereit.wait()                 # warten, bis alle Systeme geladen sind und das GUI offen ist
        else:
            # Nur das gewählte System vorab laden, dann Mini-Fenster mit Animationen öffnen
            print(f"System '{system}' wird geladen ...")
            system_vorbereiten(system)
            threading.Thread(target=window, kwargs={"mini": True}, daemon=True).start()
            gui_bereit.wait()

        print("Bereit. Sag 'Hey Jarvis' um zu starten")

        while True:
            # Wakeword -> Aufnahme -> Verarbeitung
            print("...running...")
            wait_for_wakeword()
            # Aufnahme der aktuellen Anfrage zuordnen: ein Stopp ab jetzt bricht Zuhören/Transkribieren ab
            abbruch.anfrage_setzen(abbruch.aktuell())
            text = None
            aufnahme_abgebrochen = False
            try:
                melde("zustand", "zuhoeren")
                listening()                    # Signalton
                text = Record()                # Aufnahme + Transkription
            except abbruch.Abbruch:            # Stopp während Zuhören/Transkribieren
                aufnahme_abgebrochen = True
            finally:
                abbruch.anfrage_loeschen()
            if aufnahme_abgebrochen:
                stoppe_ausgabe()
                melde("abgebrochen")
                melde("zustand", "idle")
                print("Aufnahme abgebrochen")
                continue
            text_verarbeitung(text)

    except KeyboardInterrupt:
        print("\nBeende Programm")

    finally:
        # KI-Modelle entladen
        modelle_entladen()

        # Audioaufnahme beenden
        print("Beende Audioaufnahme")
        stream.stop_stream()
        stream.close()
        pyaudio_PyAudio.terminate()


if __name__ == "__main__":
    # System auswählen oder Testmodus starten
    print("Verfügbare Systeme:")
    for i, n in enumerate(SYSTEME, 1):
        print(f"  {i}: {n}")
    auswahl = input("Welches System (Nummer oder Name, nichts = Testmodus): ").strip()

    if auswahl == "":
        auswahl = None
    elif auswahl.isdigit() and 1 <= int(auswahl) <= len(SYSTEME):
        auswahl = SYSTEME[int(auswahl) - 1]
    elif auswahl not in SYSTEME:
        raise SystemExit(f"Unbekanntes System: {auswahl}")

    Main(auswahl)
    #print(befehl_ausführen([3, 0]))