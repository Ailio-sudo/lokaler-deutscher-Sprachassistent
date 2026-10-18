"""Befehl 21: Ein installiertes Programm (Startmenü-Eintrag bzw. Microsoft-Store-App) per Name starten."""
import subprocess
from difflib import get_close_matches
from Befehle.getparam import get_parameter
def get_all_apps():
    """Liest über PowerShell («Get-StartApps») alle Startmenü-Apps ein.
    Rückgabe: Dictionary {Name in Kleinbuchstaben: App-ID}.
    """
    result = subprocess.run(
        ["powershell","-NoProfile","-Command","Get-StartApps | ForEach-Object { $_.Name + '|' + $_.AppID }"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore")
    apps = {}
    for line in result.stdout.strip().split("\n"):
        if "|" in line:
            app_name, app_pfad = line.split("|", 1)
            apps[app_name.strip().lower()] = app_pfad.strip()
            #print(app_name)
    return apps

def find_best_match(program, apps):
    """Sucht den passenden App-Namen zum gesprochenen Namen.
    Zuerst wird der erste App-Name gesucht, der den Namen enthält; sonst der ähnlichste Name (difflib, Mindestähnlichkeit 0.5).
    Rückgabe: App-Name (Schlüssel aus apps) oder None.
    """
    for app in apps:
        if program.lower().strip() in app.lower():
            return app
    matches = get_close_matches(program.lower(), apps.keys(), n=1, cutoff=0.5)
    return matches[0] if matches else None

def start_program(program=False):
    """Befehl 21: Startet das Programm.

    Parameter:
        program: Name des Programms. Ist er leer, wird per get_parameter nachgefragt.
    Rückgabe: Meldung, ob das Programm gestartet wurde oder nicht gefunden wurde. Gestartet wird über den Windows-Explorer (shell:AppsFolder).
    """
    if not program:
        program = get_parameter("Welches Programm möchtest du ausführen?")
    apps = get_all_apps()
    token = program.lower().strip()
    #print(apps)
    if token not in apps:
        best_match = find_best_match(token, apps)
        if best_match:
            token = best_match
        else:
            return f"Das Programm '{program}' wurde nicht gefunden."
    app_id = apps[token]
    #print(token)
    try:
        subprocess.Popen(f'explorer shell:AppsFolder\\{app_id}', shell=True)
        return f"{program} wurde gestartet."
    except Exception as e:
        return f"Fehler beim Starten von '{program}': {e}"
if __name__ == "__main__":
    print(start_program("firefox"))
