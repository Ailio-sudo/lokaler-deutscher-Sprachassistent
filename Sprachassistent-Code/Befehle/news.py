"""Befehl 11: Nachrichten-Schlagzeilen von SRF (RSS-Feed). Dafür wird auf das Internet zugegriffen."""
# Source - https://stackoverflow.com/a/5098674
# Posted by Kurt McKee, modified by community. See post 'Timeline' for change history
# Retrieved 2026-07-08, License - CC BY-SA 4.0

import feedparser
def news(anzahl=5):
    """Befehl 11: Gibt die obersten Schlagzeilen des SRF-News-Feeds zurück.

    Parameter:
        anzahl: Anzahl der Schlagzeilen (Standard 5).
    Rückgabe: Text mit einer Schlagzeile pro Zeile (nur die Titel).
    """
    f = feedparser.parse("https://www.srf.ch/news/bnf/rss/1890")
    # f contains a dictionary key 'entries'
    # entries is a list of dictionaries with 'title' and 'content' keys
    text = ""
    for e in f['entries'][:anzahl]:
        text += e.get('title', '') + ".\n"
    return text

if __name__ == "__main__":
    print(news())
