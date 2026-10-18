
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


MICROPHONE_INDEX = 2 #Index des Standard Mikrofons, das Verwendet werden soll

MODELL_SMALL = "qwen2.5:1.5b-instruct" #Für Parameterextraktion und Recherchieren-Befehl
MODELL_LARGE = "gemma4:e4b" #Für KI-Klassifikationssystem