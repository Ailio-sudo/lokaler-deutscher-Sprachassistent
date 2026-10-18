"""Befehl 17: Wiedergabe pausieren.
Der auskommentierte Teil oben ist eine frühere Variante, die zuerst prüft, ob gerade Medien abgespielt werden.
"""
# import asyncio
# import keyboard
# from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager, GlobalSystemMediaTransportControlsSessionPlaybackStatus

# async def is_media_playing():
#     status = (await GlobalSystemMediaTransportControlsSessionManager.request_async()).get_current_session()

#     return status is not None and status.get_playback_info().playback_status == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING
# async def pause_asyncio():
#     if await is_media_playing():
#         keyboard.press("play/pause")
# def pause():
#     asyncio.run(pause_asyncio())
# if __name__ == "__main__":
#     pause()
import keyboard
def pause():
    """Befehl 17: Simuliert die Medientaste «play/pause».
    Die Taste schaltet zwischen Wiedergabe und Pause um (identisch zu play()). Liefert keinen Text zurück.
    """
    keyboard.press("play/pause")
