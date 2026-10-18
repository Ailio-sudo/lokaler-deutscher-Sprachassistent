"""Befehl 18: Wiedergabe fortsetzen.
Der auskommentierte Teil oben ist eine frühere Variante, die zuerst prüft, ob gerade keine Medien abgespielt werden.
"""
# import asyncio
# import keyboard
# from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager, GlobalSystemMediaTransportControlsSessionPlaybackStatus

# async def is_media_playing():
#     status = (await GlobalSystemMediaTransportControlsSessionManager.request_async()).get_current_session()

#     return status is not None and status.get_playback_info().playback_status == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING
# async def play_asyncio():
#     if not  await is_media_playing():
#         keyboard.press("play/pause")
# def play():
#     asyncio.run(play_asyncio())
# if __name__ == "__main__":
#     play()
import keyboard
def play():
    """Befehl 18: Simuliert die Medientaste «play/pause».
    Die Taste schaltet zwischen Wiedergabe und Pause um (identisch zu pause()). Liefert keinen Text zurück.
    """
    keyboard.press("play/pause")
