# Maturaarbeit: Lokaler deutschsprachiger Sprachassistent und Vergleich von fünf Intent-Erkennungssystemen

Dieses Projekt enthält einen lokalen Sprachassistenten für Windows (27 Sprachbefehle) und die Auswertung, mit der fünf Verfahren zur
Intent-Erkennung verglichen wurden: **Keyword Matching, TF-IDF, Word Embeddings, Sentence Embeddings und ein Sprachmodell (KI)**.
Der Stand dieser Dokumentation: Oktober 2026. 

## Ablauf einer Sprachanfrage

1. **Wake Word:** «Hey Jarvis» (openwakeword) – `ASR.py`
2. **Aufnahme und Transkription:** speech_recognition beendet die Aufnahme nach einer Sprechpause, faster-whisper (Modell «small», CPU) wandelt sie in Text um – `ASR.py`. Wird kein Text erkannt, gibt `Record()` **None** zurück.
3. **Intent-Erkennung:** das gewählte System bestimmt die Befehlsnummer (0 = unbekannt, 1–27) – Ordner `systems/`
4. **Parameter-Extraktion:** ein kleines Sprachmodell (qwen2.5:1.5b-instruct über Ollama) holt die Parameter aus dem Satz – `ki_params.py`. Das KI-System (gemma4:e4b) liefert Befehl und Parameter in einem Schritt (`systems/ki_gemma.py`).
5. **Befehlsausführung:** `befehl_ausführen()` in `sprachassistent.py` ruft die passende Funktion im Ordner `Befehle/` auf.
6. **Sprachausgabe:** `TextToSpeech.py` (pyttsx3, lokale Windows-Stimme)

## Projektstruktur

```
Maturaarbeit/
├─ setup.bat                  Installation (Python, Ollama, Modelle, danach setup.py)
├─ Sprachassistent.bat        Startet den Sprachassistenten
├─ befehle.txt                Liste der 27 Befehle mit Parametern mit ihren jeweiligen
├─ models/                    grosse Modelle (FastText, Qwen3-Embedding) und models/self_trained/ (trainierte Modelle)
├─ screenshots/               hier speichert der Screenshot-Befehl
└─ Sprachassistent-Code/
   ├─ sprachassistent.py      Hauptprogramm, GUI, Befehlsausführung (Einstiegspunkt)
   ├─ ASR.py                  Wake Word, Aufnahme, Transkription
   ├─ TextToSpeech.py         Sprachausgabe
   ├─ ki_params.py            Parameter-Extraktion mit kleinem Sprachmodell
   ├─ user_data.py            persönliche Einstellungen und Zugangsdaten
   ├─ setup.py                legt die virtuelle Umgebung an und installiert Pakete
   ├─ systems/                die fünf Erkennungssysteme + training_data.py
   ├─ Befehle/                eine Datei pro Befehl (bzw. Befehlsgruppe)
   └─ system_comparison/      Testdaten, Auswertung (test_system*.py), Statistik (bootstrap.py), Rohdaten (daten*.json), Plots
```

| Datei in `systems/` | Verfahren |
|---|---|
| `keyword_matching.py` | Schlüsselwörter (Funktion `if_else`) |
| `tf_idf.py` | TF-IDF + logistische Regression |
| `word_embeds.py` | FastText-Wortvektoren (Mittelwert) + logistische Regression |
| `sentence_embeds.py` | Qwen3-Embedding-0.6B + logistische Regression |
| `ki_gemma.py` | Sprachmodell gemma4:e4b über Ollama |

## Installation und Start

1. **`setup.bat` ausführen.** Es prüft/installiert Python (3.11.9, falls noch kein Python vorhanden ist) und Ollama, lädt die Ollama-Modelle `qwen2.5:1.5b-instruct` und `gemma4:e4b` und startet `setup.py`.
   `setup.py` legt die virtuelle Umgebung `sprachassistentenv` an und installiert die Pakete mit festen Versionen. Danach wird gefragt, ob eine NVIDIA-GPU (CUDA) vorhanden ist.
   **Achtung:** Das Setup ist eine Neuinstallation und löscht die bestehende Umgebung, den Spotify-Token und **überschreibt `user_data.py`** (eingetragene Zugangsdaten gehen verloren).
2. **`Sprachassistent-Code/user_data.py` ausfüllen** (siehe unten).
3. **`Sprachassistent.bat` starten.** In der Konsole wird ein System gewählt (Nummer oder Name). Ohne Eingabe startet der **Testmodus** mit allen Systemen und grosser Oberfläche, mit Auswahl der **Betriebsmodus** mit kleinem Statusfenster.
4. Beim ersten Start werden fehlende Modelle automatisch geladen bzw. trainiert:
   FastText `cc.de.300.bin` (mehrere GB) und Qwen3-Embedding-0.6B in `models/`, die logistischen Regressionen in `models/self_trained/` (Ordner wird automatisch angelegt).

Das Projekt wurde mit **Python 3.11.9** entwickelt und ausgewertet.

## Konfiguration (`user_data.py`)

| Einstellung | Bedeutung |
|---|---|
| `MICROPHONE_INDEX` | Mikrofon; bei `None` wird beim ersten Start nachgefragt |
| `MODELL_SMALL`, `MODELL_LARGE` | Ollama-Modelle für Parameter-Extraktion/Recherche bzw. KI-System |
| `STANDARD_STADT` | Standardstadt für den Wetterbefehl |
| `E_MAIL`, `E_MAIL_PASSWORT`, `IMAP_ADRESS` | E-Mail-Befehl |
| `ORS_KEY` | OpenRouteService (Routenbefehl) |
| `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET` | Spotify-Befehl «Lied abspielen» |

## Auswertung der Systeme (`system_comparison/`)

- `test_dataset.py`: fehlerfreier und fehlerhafter Testdatensatz. `systems/training_data.py`: Trainings- und Validierungsdaten.
- `python test_system.py`: erstellt aus `daten.json` alle Plots (SVG, Ordner `Plots`). Das Berechnen der Rohdaten (`create_data`) ist im Block `__main__` auskommentiert, da es lange dauert.
- `python bootstrap.py`: Paired-Bootstrap-Test und Konfidenzintervalle (aktuell mit 10^2 Stichproben; die Ergebnisse im Kommentar am Dateiende stammen laut Kommentar aus 10^6).
- Format der Rohdaten: pro Testsatz `[erkannter Intent, richtiger Intent, Dauer in Sekunden]`.

## Weiterentwicklung

- **Neuen Befehl hinzufügen:** Datei in `Befehle/` anlegen; in `sprachassistent.py` importieren, Eintrag in `BEFEHLSNAMEN` und einen Zweig in `befehl_ausführen()` ergänzen; Schlüsselwörter in `systems/keyword_matching.py`; Beispielsätze in `systems/training_data.py` und den Testdaten (die Modelle in `models/self_trained/` müssen danach neu trainiert, also gelöscht werden); Parameter-Prompt in `ki_params.py`; Beschreibung im Prompt in `systems/ki_gemma.py`. Alle Auswertungsdaten müssten neu berechnet werden.
- **Neues Erkennungssystem:** Ladefunktion `lade_...` und Eintrag in `LADER` in `sprachassistent.py`; für die Auswertung eine `system_...`-Funktion in `system_comparison/test_system.py`.
- **Wake Word / Aufnahme:** `ASR.py` (Schwellenwert 0.28, Sprechpause 1.5 s).

