"""Einrichtung des Sprachassistenten (wird von setup.bat gestartet).

Das Skript legt eine neue virtuelle Umgebung «sprachassistentenv» im Projektordner an und installiert
darin alle benötigten Python-Pakete (Liste «packages», mit festen Versionen).

ACHTUNG: Das Setup ist eine Neuinstallation. Nach der Bestätigung im Dialog werden
  - die vorhandene Umgebung «sprachassistentenv» gelöscht,
  - der Spotify-Token (Befehle/spotify_token_cache) gelöscht und
  - die Datei user_data.py mit der leeren Vorlage überschrieben (eingetragene Zugangsdaten gehen verloren).
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
import shutil
import subprocess

# Hinweis: Diese Variable wird nicht verwendet. setup() legt weiter unten eine eigene (lokale) Variable
# venv_path an, die auf den Ordner «sprachassistentenv» zeigt.
venv_path = r"venv\Scripts\python.exe"

# Alle benötigten Python-Pakete mit festgelegten Versionen; sie werden im neuen venv installiert
packages = [
    "numpy==2.4.6",
    "pyaudio==0.2.14",
    "pygame==2.6.1",
    "SpeechRecognition==3.17.0",
    "typing-extensions==4.16.0",
    "certifi==2026.7.22",
    "charset_normalizer==3.5.2",
    "cloudpickle==3.1.2",
    "colorama==0.4.6",
    "flatbuffers==25.12.19",
    "idna==3.20",
    "joblib==1.6.0",
    "narwhals==2.27.1",
    "onnxruntime==1.31.0",
    "openwakeword==0.6.0",
    "packaging==26.3",
    "protobuf==7.36.2",
    "requests==2.34.2",
    "scikit-learn==1.9.1",
    "scipy==1.17.1",
    "threadpoolctl==3.7.0",
    "tqdm==4.70.1",
    "urllib3==2.8.0",
    "pypiwin32==223",
    "pywin32==312",
    "screen-brightness-control==0.27.2",
    "wmi==1.5.1",
    "comtypes==1.4.17",
    "pyttsx3==2.99",
    "psutil==7.2.2",
    "pycaw==20260927",
    "click==8.5.0",
    "ddgs==9.16.0",
    "lxml==6.1.3",
    "primp==2.0.1",
    "annotated-types==0.8.0",
    "anyio==4.15.1",
    "h11==0.16.0",
    "httpcore==1.0.9",
    "httpx==0.28.1",
    "ollama==0.6.3",
    "pydantic==2.14.0",
    "pydantic-core==2.50.0",
    "typing-inspection==0.4.4",
    "openrouteservice==2.3.3",
    "mss==10.2.0",
    "Pillow==12.3.0",
    "mouseinfo==0.1.3",
    "pyautogui==0.9.54",
    "pygetwindow==0.0.9",
    "pymsgbox==2.0.1",
    "pyperclip==1.11.0",
    "pyrect==0.2.0",
    "pyscreeze==1.0.1",
    "pytweening==1.2.0",
    "keyboard==0.13.5",
    "redis==8.1.0",
    "spotipy==2.26.0",
    "winotify==1.1.0",
    "beautifulsoup4==4.15.0",
    "deep-translator==1.11.4",
    "soupsieve==2.10",
    "langdetect==1.0.9",
    "six==1.17.0",
    "pycountry==26.2.16",
    "markdown==3.11",
    "zahlwort2num==1.0.1",
    "gensim==4.4.0",
    "smart_open==8.0.2",
    "wrapt==2.5.0",
    "MarkupSafe==3.0.4",
    "annotated-doc==0.0.5",
    "filelock==4.1.0",
    "fsspec==2026.9.0",
    "hf-xet==1.7.0",
    "huggingface-hub==1.33.0",
    "jinja2==3.1.6",
    "markdown-it-py==4.2.0",
    "mdurl==0.1.2",
    "mpmath==1.3.0",
    "networkx==3.6.1",
    "pygments==2.21.0",
    "pyyaml==6.0.3",
    "regex==2026.9.29",
    "rich==15.0.0",
    "safetensors==0.8.0",
    "sentence_transformers==6.1.0",
    "setuptools==84.0.0",
    "shellingham==1.5.4",
    "sympy==1.14.0",
    "tokenizers==0.23.3",
    "torch==2.14.1",
    "transformers==5.19.0",
    "typer==0.27.3",
    "contourpy==1.3.3",
    "cycler==0.12.1",
    "fonttools==4.66.1",
    "kiwisolver==1.5.1",
    "matplotlib==3.11.2",
    "pyparsing==3.3.3",
    "python-dateutil==2.9.0.post0",
    "pandas==3.0.6",
    "tzdata==2026.5",
    "upsetplot==0.9.0",
    "feedparser==6.0.14",
    "feedparser-sgmllib==2.1.0",
    "av==18.1.0",
    "ctranslate2==4.8.3",
    "faster-whisper==1.2.1"
]


# Projektordner (Maturaarbeit): ein Ordner oberhalb von Sprachassistent-Code
home_path = Path(Path(__file__).resolve().parent.parent)
def setup():
    """Führt die Neuinstallation durch (siehe Beschreibung am Anfang der Datei).

    Ablauf: Bestätigungsdialog -> alte Daten löschen -> neue virtuelle Umgebung erstellen
    (bevorzugt mit Python 3.11 über «py -3.11», sonst mit dem Standard-«python») -> Pakete installieren ->
    Abfrage, ob eine NVIDIA-GPU mit CUDA vorhanden ist (dann wird torch durch die CUDA-Version ersetzt).
    Anschliessend müssen die Zugangsdaten in user_data.py eingetragen werden.
    """
    root = tk.Tk()
    root.geometry("300x120")
    root.resizable(False, False)
    antwort = tk.BooleanVar(value=False)
    label = ttk.Label(root, text="Bist du sicher, dass du das Setup machen möchtest\n(Neu Installation)")
    label.pack(pady=15)
    def ja():
        antwort.set(True)
        root.destroy()
    def nein():
        antwort.set(False)
        root.destroy()
    buttons = ttk.Frame(root).pack()

    ttk.Button(buttons, text="Ja", command=ja).pack(side="left", padx=10)
    ttk.Button(buttons, text="Nein", command=nein).pack(side="left", padx=10)

    root.mainloop()
    if not antwort.get():
        print("Setup abgebrochen")
        return

    # Zielorte: neue virtuelle Umgebung und Spotify-Token-Datei
    venv_path = home_path / "sprachassistentenv"
    spotify_cache = home_path/"Sprachassistent-Code/Befehle/spotify_token_cache"
    print("Spotify Cache Löschen")
    spotify_cache.unlink(missing_ok=True)

    if venv_path.exists():
        print("Lösche sprachassistentenv")
        shutil.rmtree(venv_path)

    # ACHTUNG: überschreibt user_data.py mit der leeren Vorlage (eingetragene Zugangsdaten gehen verloren)
    print("Lösche Nutzerdaten")
    user_data_path = home_path / "Sprachassistent-Code" / "user_data.py"
    with open(user_data_path, "w", encoding="utf-8") as user_data:
            user_data.write("""
#############################E-Mail#############################################
#Gib hier deine Daten zur E-Mail an (Konto und Passwort)
E_MAIL = None #Konto
E_MAIL_PASSWORT = None #Passwort
#Ausserdem musst du Imap in den Einstellungen deines Kontos aktivieren, falls dein Anbieter sie unterstützt. Sonst kann dieser Befehl nicht verwendet werden.
IMAP_ADRESS = None #IMAP Adresse des Anbieters des Kontos


#############################Spotify Playsong####################################
# öffne developer.spotify.com/dashboard
# Melde dich mit Spotify An
# Erstelle eine neue App: "Create App", nenne sie beispielsweise Sprachassistent
# Öffne die App und geh auf Settings, Dort siehst du Client ID und Client Secret. Kopiere diese zwei hierhin:
SPOTIFY_CLIENT_ID = None  #Client ID
SPOTIFY_CLIENT_SECRET = None #Client Secret
#Bei erstmaliger Nutzung des Befehls wirst du aufgefordert dich anzumelden. Anschliessend wird dein Token in .spotify_token_cache gespeichert.


#############################OpenRouteService#####################################
ORS_KEY = None #Registriere dich bei OpenRouteService.org und erstelle einen kostenlosen API Key

#############################Wetter###############################################
STANDARD_STADT = None #Stadt die Standardmässig bei einer Wetteranfrage verwendet werden soll)


MICROPHONE_INDEX = None #Index des Standard Mikrofons, das Verwendet werden soll

MODELL_SMALL = "qwen2.5:1.5b-instruct" #Für Parameterextraktion und Recherchieren-Befehl
MODELL_LARGE = "gemma4:e4b" #Für KI-Klassifikationssystem""")
    # Neues venv erstellen: zuerst mit Python 3.11 (Startprogramm «py»), sonst mit dem Standard-«python»
    print("Neues Venv erstellen")
    try:
        subprocess.run(["py", "-3.11", "-m", "venv", str(venv_path)], check=True)
    except:
        print("Python Installer nicht gefunden. Nutze Python.")
        print("(führe 'python --version' in einem neuen CMD Fenster aus und stelle sicher das es 3.11.9 ausgibt)")
        subprocess.run(["python", "-m", "venv", str(venv_path)],check=True)

    # Pakete mit dem pip des neuen venv installieren
    venv_python = venv_path/"Scripts/python.exe"
    print("Benötigte Packages installieren")
    subprocess.run([venv_python, "-m", "pip", "install", "--upgrade", "pip"],check=True)
    subprocess.run([venv_python, "-m", "pip", "install", *packages], check=True)


    # Zweite Abfrage: Hat das Gerät eine NVIDIA-GPU mit CUDA-Unterstützung?
    root = tk.Tk()
    root.geometry("300x120")
    root.resizable(False, False)
    antwort = tk.BooleanVar(value=False)
    label = ttk.Label(root, text="Hat dieses Gerät eine NVIDIA Gpu, die Cuda unterstützt?")
    label.pack(pady=15)
    def ja():
        antwort.set(True)
        root.destroy()
    def nein():
        antwort.set(False)
        root.destroy()
    buttons = ttk.Frame(root).pack()

    ttk.Button(buttons, text="Ja", command=ja).pack(side="left", padx=10)
    ttk.Button(buttons, text="Nein", command=nein).pack(side="left", padx=10)
    root.mainloop()
    # Mit CUDA-GPU: die bereits installierte torch-Version durch die CUDA-Version (cu130) ersetzen
    if antwort.get():
        print("Torch mit Cuda installieren: ")
        print("Altes Torch löschen")
        subprocess.run([
            venv_python, "-m", "pip", "uninstall",
            "-y", "torch", "torchvision", "torchaudio"
        ], check=True)
        print("Cuda Torch installieren")
        subprocess.run([
            venv_python, "-m", "pip", "install",
            "torch", "torchvision",
            "--index-url", "https://download.pytorch.org/whl/cu130"
        ], check=True)



    print("Fertig. Fülle nun die Datei user_data.py mit den benötigten Daten aus.")

# Das Setup startet, sobald diese Datei ausgeführt wird
setup()
