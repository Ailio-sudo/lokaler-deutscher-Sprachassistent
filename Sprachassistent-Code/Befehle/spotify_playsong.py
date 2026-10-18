"""Befehl 19: Ein Lied über die Spotify-Web-API abspielen.

Benötigt SPOTIFY_CLIENT_ID und SPOTIFY_CLIENT_SECRET (user_data.py). Bei der ersten Nutzung ist eine Anmeldung nötig;
der Token wird in Befehle/spotify_token_cache gespeichert. Ohne Zugangsdaten gibt der Befehl nur einen Hinweistext zurück.
"""
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from Befehle.getparam import get_parameter
from Befehle.start_program import start_program
import time
from user_data import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from pathlib import Path
if SPOTIFY_CLIENT_ID == None or SPOTIFY_CLIENT_SECRET == None:
    print(r"Folge den Anweisungen in Sprachassistent-Code\user_data.py für Spotify PlaySong um diesen Befehl zu nutzen.")

    def play_song(song = None, artist = None):
        """Ersatzfunktion ohne Zugangsdaten: gibt nur den Hinweistext zurück."""
        return r"Folge den Anweisungen in Sprachassistent-Code\user_data.py für Spotify PlaySong um diesen Befehl zu nutzen."

else:
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri="http://127.0.0.1:8888/",
        scope=("user-modify-playback-state ""user-read-playback-state ""user-read-currently-playing"),
        cache_path=str(Path(Path(__file__).resolve().parent)/"spotify_token_cache")
    ))
    def get_device_id():
        """Gibt die ID des aktiven Spotify-Geräts zurück (sonst die des ersten Geräts); None, wenn kein Gerät gefunden wird."""
        devices = sp.devices()["devices"]
        active = [d for d in devices if d["is_active"]]
        if not devices:
            print("Keine Spotify-Geräte gefunden.")
            return None
        return (active[0] if active else devices[0])["id"]

    def play_song(song = None, artist = ""):
        """Befehl 19: Sucht das Lied und spielt es ab.

        Parameter:
            song: Titel (Fehlt er, wird per get_parameter nachgefragt).
            artist: Künstler (optional, Standard leer).
        Ablauf: Suche mit «Titel Künstler» (10 Treffer, der erste wird verwendet); ist kein Gerät aktiv, wird Spotify gestartet
        und gewartet, bis ein Gerät gefunden wird; dann wird das Album mit dem gewählten Titel abgespielt.
        Rückgabe: Nichts (None); Meldungen erscheinen nur in der Konsole.
        """
        if song == None:
            return play_song(get_parameter("Welches Lied möchtest du Abspielen?"), artist)
        if artist == None:
            artist = ""
        query = song + " " + artist
        items = sp.search(q=query, type="track", limit=10)["tracks"]["items"]
        if not items:
            print(f"No track found for: {query}")
            return
        track = items[0]
        device_id = get_device_id()
        if device_id == None:
            start_program("Spotify")
        n=0
        while device_id == None:
            print("Versuch ", n, " ein Device zu finden (Device id: ", device_id, ")")
            device_id = get_device_id()
            n += 1
            time.sleep(0.2)

        # Lied abspielen
        sp.start_playback(
            device_id=device_id,
            context_uri=track["album"]["uri"],
            offset={"uri": track["uri"]}
        )

        if artist != "":
            print(song + " von " + artist + " wird Abgespielt.")
        else:
            print(song + " wird Abgespielt.")



if __name__ == "__main__":
    play_song('spiel around the world', 'daft punk')
