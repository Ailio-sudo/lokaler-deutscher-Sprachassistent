import csv
import math

# ============================================================
# Tabellen für Bootstrap-Test und Konfidenzintervalle
# ============================================================

SYSTEM_ANZEIGE = {
    "ifelse": "Keyword Matching",
    "tfidf": "TF-IDF",
    "word_embeds": "Wort-Embeddings",
    "sentence_embeds": "Satz-Embeddings",
    "ki": "KI",
}

HOCH = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def _zahl_de(wert, stellen=1):
    """Formatiert eine Zahl mit Dezimalkomma."""
    return f"{wert:.{stellen}f}".replace(".", ",")


def _format_p(p, ziehungen=10**6):
    """Formatiert einen p-Wert: 0 wird zu «< 10⁻⁶», kleine Werte in Zehnerpotenz, sonst drei Nachkommastellen."""
    if p == 0:
        exponent = int(round(math.log10(ziehungen)))
        return "< 10" + str(-exponent).translate(HOCH)
    if p < 0.001:
        mantisse, exponent = f"{p:.1e}".split("e")
        return mantisse.replace(".", ",") + " · 10" + str(int(exponent)).translate(HOCH)
    return _zahl_de(p, 3)


def _anzeigename(name):
    """Wandelt 'ifelse - tfidf' in 'Keyword Matching – TF-IDF' um."""
    teile = [SYSTEM_ANZEIGE.get(teil.strip(), teil.strip()) for teil in name.split(" - ")]
    return " – ".join(teile)


def _zeichne_tabelle(spalten, zellen, dateiname, titel=None, figsize=(8, 4.2),
                     spaltenbreiten=None, zellfarben=None):
    """Zeichnet eine Tabelle im einheitlichen Design und speichert sie als SVG und CSV.

    Parameter:
        spalten: Spaltenüberschriften.
        zellen: Liste von Zeilen (Texte).
        dateiname: Dateiname ohne Endung (wird in plots_path gespeichert).
        titel: Optionaler Titel (in der Arbeit meist weglassen, da die Beschriftung ihn ersetzt).
        zellfarben: Dict {(zeile, spalte): Farbe} für einzelne Textfarben (Zeile 0 = erste Datenzeile).
    """
    zellfarben = zellfarben or {}

    fig, ax = pyplot.subplots(figsize=figsize)
    ax.axis("off")

    tab = ax.table(
        cellText=zellen,
        colLabels=spalten,
        cellLoc="center",
        loc="center",
        colWidths=spaltenbreiten,
    )
    tab.auto_set_font_size(False)
    tab.set_fontsize(11)
    tab.scale(1, 2.0)

    for (zeile, spalte), zelle in tab.get_celld().items():
        zelle.set_edgecolor(COLORS["grid"])
        zelle.set_linewidth(0.8)

        if zeile == 0:
            zelle.set_facecolor(COLORS["navy"])
            zelle.set_text_props(color="white", fontweight="bold")
        else:
            zelle.set_facecolor("#F5F7FA" if zeile % 2 == 0 else COLORS["background"])
            zelle.set_text_props(color=zellfarben.get((zeile - 1, spalte), COLORS["text"]))
            if spalte == 0:
                zelle.set_text_props(fontweight="bold", color=COLORS["navy"])

    if titel:
        set_plot_title(ax, titel, width=50)

    fig.tight_layout()
    fig.savefig(plots_path + dateiname + ".svg", bbox_inches="tight")
    pyplot.close(fig)

    with open(plots_path + dateiname + ".csv", "w", encoding="utf-8-sig", newline="") as datei:
        writer = csv.writer(datei, delimiter=";")
        writer.writerow(spalten)
        writer.writerows(zellen)


def tabelle_p_werte(p_werte, dateiname, titel=None, spaltentitel="Vergleich",
                    alpha=0.05, bonferroni=False, ziehungen=10**6):
    """Speichert die p-Werte des Paired-Bootstrap-Tests als Tabelle.

    Parameter:
        p_werte: Liste [[p-Wert, 'ifelse - tfidf'], ...] wie in der Konsole ausgegeben
                 (auch für den Vergleich mit/ohne Fehler: [[p, 'ifelse'], ...]).
        dateiname: Dateiname ohne Endung.
        spaltentitel: «Vergleich» (zwei Systeme) oder «System» (mit/ohne Fehler).
        alpha: Signifikanzniveau.
        bonferroni: True = alpha wird durch die Anzahl Vergleiche geteilt.
        ziehungen: Anzahl Bootstrap-Stichproben (bestimmt, was «p < 10⁻ⁿ» bedeutet).
    """
    if bonferroni:
        alpha = alpha / len(p_werte)

    zellen = []
    zellfarben = {}
    for zeile, (p, name) in enumerate(p_werte):
        signifikant = p < alpha
        zellen.append([
            _anzeigename(name),
            _format_p(p, ziehungen),
            "Ja" if signifikant else "Nein",
        ])
        zellfarben[(zeile, 2)] = COLORS["teal"] if signifikant else COLORS["red"]

    spalten = [spaltentitel, "p-Wert", f"Signifikant (α = {_zahl_de(alpha, 3).rstrip('0').rstrip(',')})"]

    _zeichne_tabelle(
        spalten, zellen, dateiname, titel,
        figsize=(8, 0.5 + 0.42 * (len(zellen) + 1)),
        spaltenbreiten=[0.5, 0.2, 0.3],
        zellfarben=zellfarben,
    )


def tabelle_konfidenzintervalle(konfidenzintervalle, dateiname, titel=None, stellen=1):
    """Speichert die 95-%-Konfidenzintervalle als Tabelle.

    Parameter:
        konfidenzintervalle: Liste [['ifelse', untere Grenze, obere Grenze], ...] wie in der Konsole ausgegeben
                             (Werte als Anteil 0 bis 1).
        dateiname: Dateiname ohne Endung.
        stellen: Nachkommastellen in Prozent.
    """
    zellen = []
    for name, unten, oben in konfidenzintervalle:
        zellen.append([
            SYSTEM_ANZEIGE.get(name, name),
            _zahl_de(unten * 100, stellen) + " %",
            _zahl_de(oben * 100, stellen) + " %",
        ])

    spalten = ["System", "Untere Grenze", "Obere Grenze"]

    _zeichne_tabelle(
        spalten, zellen, dateiname, titel,
        figsize=(8, 0.5 + 0.42 * (len(zellen) + 1)),
        spaltenbreiten=[0.4, 0.3, 0.3],
    )


# ------------------------------------------------------------
# Eingabe: Werte aus dem Bootstrap-Skript (10**6 Ziehungen, Seed = 0)
# ------------------------------------------------------------

P_WERTE_SYSTEME = [[0.0, 'ifelse - tfidf'], [0.0, 'ifelse - word_embeds'], [0.0, 'ifelse - sentence_embeds'], [0.0, 'ifelse - ki'], [0.000936, 'tfidf - word_embeds'], [0.000137, 'tfidf - sentence_embeds'], [0.0, 'tfidf - ki'], [0.0, 'word_embeds - sentence_embeds'], [0.0, 'word_embeds - ki'], [0.0, 'sentence_embeds - ki']]

P_WERTE_FEHLER = [[0.0, 'ifelse'], [0.0, 'tfidf'], [0.0, 'word_embeds'], [0.0, 'sentence_embeds'], [0.0, 'ki']]

KI_OHNE_FEHLER = [['ifelse', 0.6974290754427489, 0.7378678996706817], ['tfidf', 0.8832976794217113, 0.9090208870321177], ['word_embeds', 0.860226379262558, 0.8866393698595937], ['sentence_embeds', 0.9146057095747754, 0.9346405612985614], ['ki', 0.9567908477972057, 0.9736156941645836]]

KI_MIT_FEHLER = [['ifelse', 0.5615950812379267, 0.6065642241333672], ['tfidf', 0.673657566381199, 0.7140807464981254], ['word_embeds', 0.6343733063290181, 0.6764687214833006], ['sentence_embeds', 0.788205213376399, 0.8198208194806627], ['ki', 0.9221724153613474, 0.9437886637028254]]


def bootstrap_tabellen():
    """Erstellt alle vier Bootstrap-Tabellen aus den oben eingegebenen Werten."""
    tabelle_p_werte(P_WERTE_SYSTEME, "tabelle_p_werte_systeme", bonferroni=False)
    tabelle_p_werte(P_WERTE_FEHLER, "tabelle_p_werte_mit_ohne_fehler", spaltentitel="System")
    tabelle_konfidenzintervalle(KI_OHNE_FEHLER, "tabelle_ki_ohne_fehler")
    tabelle_konfidenzintervalle(KI_MIT_FEHLER, "tabelle_ki_mit_fehler")


if __name__ == "__main__":
    bootstrap_tabellen()