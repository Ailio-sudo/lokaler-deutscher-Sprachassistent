"""Auswertung der fünf Intent-Erkennungssysteme auf den Testdatensätzen und Erstellung aller Plots.

Ablauf:
  1. create_data(system[, True]) wendet ein System auf den fehlerfreien bzw. fehlerhaften Testdatensatz an und speichert
     pro Satz [erkannter Intent, richtiger Intent, Dauer in Sekunden] in daten.json
     (Schlüssel: ifelse, tfidf, word_embeds, sentence_embeds, ki; Version mit Fehlern: Schlüssel + «_fehler»).
  2. get_all_plots() berechnet aus daten.json die Evaluationsmetriken (Accuracy, Precision, Recall, F1 als Macro-Durchschnitt, MCC)
     und speichert die Diagramme als SVG im Ordner Plots.
Beim direkten Start werden nur die Plots erstellt; das Berechnen der Daten ist im Block «__main__» auskommentiert,
weil es lange dauert (KI-System).
"""
import time
from test_dataset import test_dataset, test_dataset_fehler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix, ConfusionMatrixDisplay, matthews_corrcoef
from matplotlib import pyplot
from matplotlib.ticker import PercentFormatter
import json
import numpy
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent/"systems"))
from training_data import dataset, validation_dataset
#Testet die Systeme auf den beiden Testdatensätzen und erstellt Plots

daten_path = Path(__file__).resolve().parent/"daten.json"
plots_path = str(Path(__file__).resolve().parent/"Plots") + "/"

#Befehle mit ihrem korrekten Index in der Liste
commands = [
    "unknown",
    "change_brightness",
    "get_brightness",
    "set_brightness",
    "check_emails",
    "einkaufsliste_add",
    "einkaufsliste_lesen",
    "einkaufsliste_leeren",
    "change_volume",
    "get_volume",
    "set_volume",
    "news",
    "recherchieren",
    "route",
    "screenshot",
    "searchfile",
    "next_track",
    "pause",
    "play",
    "play_song",
    "previous_track",
    "start_program",
    "tag",
    "start_timer",
    "translate",
    "uhrzeit",
    "wetter",
    "wuerfeln"
]

command_lengths = [1,2,1,2,1,2,1,1,2,1,2,2,2,4,1,2,1,1,1,3,1,2,1,2,3,1,2,1] #Höchste Anzahl parameter für einen befehl

#Jedes System einheitlich mit system_ benennen und Zeitmessung einbauen
def system_ifelse(input):
    """Keyword Matching auf einen Satz anwenden. Rückgabe: ([Befehlsnummer], Dauer in Sekunden)."""
    from keyword_matching import if_else

    start = time.perf_counter()
    output = if_else(input)
    end = time.perf_counter()

    dauer = end - start

    return [output], dauer

def system_sentence_embeds(input):
    """Sentence Embeddings auf einen Satz anwenden. Rückgabe: ([Befehlsnummer], Dauer in Sekunden)."""
    from sentence_embeds import sentence_embeddings

    start = time.perf_counter()
    output = sentence_embeddings(input)[0]
    end = time.perf_counter()

    dauer = end - start

    return [output], dauer

def system_ki(input):
    """KI-System auf einen Satz anwenden. Rückgabe: (Liste [Befehlsnummer, Parameter...], Dauer in Sekunden)."""
    from ki_gemma import ki_local

    start = time.perf_counter()
    output = ki_local(input)
    end = time.perf_counter()

    dauer = end - start

    return output, dauer

def system_tfidf(input):
    """TF-IDF auf einen Satz anwenden. Rückgabe: ([Befehlsnummer], Dauer in Sekunden)."""
    from tf_idf import predict_intent

    start = time.perf_counter()
    output = predict_intent(input)[0]
    end = time.perf_counter()

    dauer = end - start

    return [output], dauer

def system_word_embeds(input):
    """Word Embeddings auf einen Satz anwenden. Rückgabe: ([Befehlsnummer], Dauer in Sekunden)."""
    from word_embeds import word_embeddings

    start = time.perf_counter()
    output = word_embeddings(input)[0]
    end = time.perf_counter()

    dauer = end - start

    return [output], dauer



def system_check(system, fehler = False): # fehler = True -> System wird auf Testdatensätze auf fehlerhaften Sätzen getestet
    """Wendet ein System auf einen kompletten Testdatensatz an.

    Parameter:
        system: Name des Systems (ifelse, tfidf, word_embeds, sentence_embeds oder ki).
        fehler: True = Testdatensatz mit eingebauten Fehlern, False = fehlerfreier Testdatensatz.
    Vor der Messung wird das System mit 28 Sätzen aufgewärmt, da die ersten Aufrufe oft deutlich länger dauern.
    Rückgabe: Liste von Einträgen [erkannter Intent, richtiger Intent, Dauer in Sekunden], ein Eintrag pro Testsatz.
    """
    #Systeme werden auf den Testdatensatz angewandt und die Daten ausgegeben.
    output = []
    #Aufwärmen, da erste Rechenzeit sonst oft viel länger ist
    for i in range(28):
        globals()["system_"+ system](test_dataset[i]["examples"][i])

    if fehler:
        for intent in range(28): #28 Intents
            for sentence in test_dataset_fehler[intent]["examples"]:
                systemoutput = globals()["system_"+ system](sentence)
                output.append([systemoutput[0][0], intent, systemoutput[1]]) #[erkannter intent, richtiger intent, dauer]
        return output
    else:
        for intent in range(28): #28 Intents
            for sentence in test_dataset[intent]["examples"]:
                systemoutput = globals()["system_"+ system](sentence)
                #if systemoutput[0][0] != intent:
                    #print(sentence, intent, systemoutput[0][0])
                output.append([systemoutput[0][0], intent, systemoutput[1]]) #[erkannter intent, richtiger intent, dauer]
            #print(intent)

        return output

def mean_system(system):
    """Berechnet die Evaluationsmetriken eines Systems aus den Rohdaten (Liste wie von system_check).
    Rückgabe: [[Accuracy, Precision, Recall, F1], [Summe der Zeiten, Anzahl Aufrufe], MCC]. Precision, Recall und F1 sind Macro-Durchschnitte.
    """
    # Berechnet aus den Daten die durchschnittliche Evaluetionsmetriken eines Systems
    true_labels = []
    predicted_labels = []
    counter=0
    time=0
    for output in system:
        counter+= 1
        time+=output[2]
        true_labels.append(output[1])
        predicted_labels.append(output[0])
    accuracy = accuracy_score(true_labels, predicted_labels)
    precision = precision_score(true_labels,predicted_labels,average="macro",zero_division=0)
    recall = recall_score(true_labels,predicted_labels,average="macro",zero_division=0)
    f1 = f1_score(true_labels,predicted_labels,average="macro",zero_division=0)
    mcc = matthews_corrcoef(true_labels,predicted_labels)
    return [[accuracy,precision,recall,f1],[time,counter], mcc] #Accuracy, Precision, Recall, F1, Zeit aller Aufrufe, Anzahl Aufrufe, MCC (test)

def mean_system_per_command(system):
    """Berechnet Precision, Recall, F1 und Anzahl Testsätze für jeden der 28 Befehle (0 bis 27) einzeln.
    Rückgabe: (Precision-Liste, Recall-Liste, F1-Liste, Support-Liste, Liste aller Zeiten).
    """
    # Berechnet aus den Daten die durchschnittlichen Evaluationsmetriken eines Systems
    true_labels = []
    predicted_labels = []
    times = [] #Rechenzeiten
    for output in system:
        true_labels.append(output[1])
        predicted_labels.append(output[0])
        times.append(output[2])
    report = classification_report(true_labels, predicted_labels, output_dict=True) #Classification Report gibt für jeden Intent einzeln die Werte heraus
    precision_per_command = []
    recall_per_command = []
    f1_per_command = []
    support_per_command = [] # Anzahl Sätze pro Befehl
    for befehl in range(0,28):
        precision_per_command.append(report[str(befehl)]["precision"])
        recall_per_command.append(report[str(befehl)]["recall"])
        f1_per_command.append(report[str(befehl)]["f1-score"])
        support_per_command.append(report[str(befehl)]["support"])
    return precision_per_command,recall_per_command, f1_per_command, support_per_command, times



import textwrap


# ============================================================
# Einheitliches Design für alle Plots
# ============================================================

COLORS = {
    "navy": "#263B50",
    "blue": "#4477AA",
    "light_blue": "#77AADD",
    "teal": "#228877",
    "orange": "#EE9944",
    "red": "#CC6677",
    "purple": "#AA4499",
    "gray": "#667788",
    "grid": "#E5E9EF",
    "text": "#334155",
    "background": "#FFFFFF",
}

SYSTEM_COLORS = [
    COLORS["navy"],
    COLORS["blue"],
    COLORS["teal"],
    COLORS["orange"],
    COLORS["purple"],
]

SYSTEM_NAMES = [
    "Keyword Matching",
    "TF-IDF",
    "Wort Embeddings",
    "Satz Embeddings",
    "KI",
]


def apply_plot_style():
    """Setzt das einheitliche Design (Schrift, Farben, Achsen) für alle Plots."""
    # Einheitliche Schrift, Farben und Abstände
    pyplot.rcParams.update({
        "figure.facecolor": COLORS["background"],
        "axes.facecolor": COLORS["background"],
        "savefig.facecolor": COLORS["background"],
        "font.family": "sans-serif",
        "font.size": 11,
        "axes.titlesize": 15,
        "axes.titleweight": "bold",
        "axes.labelsize": 12,
        "axes.labelcolor": COLORS["text"],
        "text.color": COLORS["text"],
        "xtick.color": COLORS["text"],
        "ytick.color": COLORS["text"],
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": COLORS["grid"],
        "axes.linewidth": 0.8,
        "grid.color": COLORS["grid"],
        "grid.linewidth": 0.8,
        "grid.alpha": 1.0,
        "legend.frameon": False,
        "legend.fontsize": 10,
        "svg.fonttype": "none",
    })


def style_axes(ax):
    """Formatiert die Achsen eines Diagramms (dezentes Gitternetz, keine oberen und rechten Achsenlinien)."""
    # Ruhige Achsen und dezentes Gitternetz
    ax.set_axisbelow(True)
    ax.grid(axis="y", linestyle="-", alpha=1.0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(COLORS["grid"])
    ax.spines["bottom"].set_color(COLORS["grid"])
    ax.tick_params(axis="both", length=0, pad=6)


def set_plot_title(ax, title, width=42, fontsize=15):
    """Setzt den Titel eines Diagramms und verteilt lange Titel automatisch auf mehrere Zeilen."""
    # Lange Titel automatisch auf mehrere Zeilen verteilen
    wrapped_title = textwrap.fill(
        str(title),
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
    )

    ax.set_title(
        wrapped_title,
        loc="center",
        fontsize=fontsize,
        fontweight="bold",
        pad=20,
        linespacing=1.25,
    )


# Design aktivieren
apply_plot_style()


# ============================================================
# Einzelplots für ein System
# ============================================================

def create_all_plots_per_system(system, system_name):
    """Erstellt alle Einzel-Diagramme eines Systems: Durchschnittliche Evaluationsmetriken, Evaluationsmetriken pro Befehl und Confusion Matrix.

    Parameter:
        system: Rohdaten des Systems (Liste wie von system_check).
        system_name: Name, der im Dateinamen und Titel verwendet wird.
    Rückgabe: (Ergebnis von mean_system, Ergebnis von mean_system_per_command).
    """
    # Erstellt alle Plots für ein einzelnes System
    meansystem = mean_system(system)
    meansystempercommand = mean_system_per_command(system)

    # --------------------------------------------------------
    # Durchschnittliche Evaluationsmetriken
    # --------------------------------------------------------

    fig, ax = pyplot.subplots(figsize=(8, 5))

    metrics = ["Accuracy", "Precision", "Recall", "F1"]
    values = [x * 100 for x in meansystem[0]]

    bars = ax.bar(
        metrics,
        values,
        color=SYSTEM_COLORS[1],
        width=0.62,
        edgecolor="none",
        zorder=3,
    )

    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(PercentFormatter(100))
    ax.set_ylabel("Evaluationsmetriken")

    set_plot_title(
        ax,
        system_name + " – durchschnittliche Evaluationsmetriken",
        width=38,
    )

    style_axes(ax)

    ax.bar_label(
        bars,
        fmt="%.1f%%",
        padding=4,
        fontsize=10,
        color=COLORS["text"],
    )

    fig.tight_layout()
    fig.savefig(
        plots_path + system_name + "_mean_system_metrics.svg",
        bbox_inches="tight",
    )
    pyplot.close(fig)

    # --------------------------------------------------------
    # Durchschnittliche Evaluationsmetriken pro Befehl
    # --------------------------------------------------------

    for index, metric in enumerate(["Precision", "Recall", "F1-Score"]):
        fig, ax = pyplot.subplots(figsize=(16, 7))

        values = [x * 100 for x in meansystempercommand[index]]
        x = numpy.arange(len(values))

        ax.bar(
            x,
            values,
            color=SYSTEM_COLORS[1],
            width=0.72,
            edgecolor="none",
            zorder=3,
        )

        ax.set_ylim(0, 100)
        ax.yaxis.set_major_formatter(PercentFormatter(100))
        ax.set_ylabel(metric + " in Prozent")
        ax.set_xlabel("Befehl")
        ax.set_xticks(x)
        ax.set_xticklabels(range(len(values)))

        set_plot_title(
            ax,
            system_name + " – " + metric + " pro Befehl",
            width=42,
        )

        style_axes(ax)

        fig.tight_layout()
        fig.savefig(
            plots_path + system_name + "_" + metric + "_per_command.svg",
            bbox_inches="tight",
        )
        pyplot.close(fig)

    # --------------------------------------------------------
    # Confusion Matrix
    # --------------------------------------------------------

    fig, ax = pyplot.subplots(figsize=(14, 12))

    cm = confusion_matrix(
        [x[1] for x in system], 
        [x[0] for x in system], 
        labels=range(28),
    )

    disp = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=range(28),
    )

    disp.plot(
        ax=ax,
        xticks_rotation=0,
        values_format="d",
        cmap="Blues",
        colorbar=True,
    )


    ax.set_xlabel(
        "Vorhergesagter Befehl",
        fontsize=16,
        labelpad=10,
    )
    ax.set_ylabel(
        "Tatsächlicher Befehl",
        fontsize=16,
        labelpad=10,
    )

    set_plot_title(
        ax,
        system_name + " – Confusion Matrix",
        width=42,
        fontsize=20,
    )


    for text in disp.text_.ravel():
        text.set_fontsize(10)

    ax.grid(False)
    ax.tick_params(axis="both", length=0, labelsize=12)

    fig.tight_layout()
    fig.savefig(
        plots_path + system_name + "_confusion_matrix.svg",
        bbox_inches="tight",
    )
    pyplot.close(fig)

    return meansystem, meansystempercommand


# ============================================================
# Daten berechnen und in JSON speichern
# ============================================================

def create_data(system, fehler=False):
    """Wendet ein System auf den Testdatensatz an und speichert das Ergebnis in daten.json (überschreibt den Schlüssel dieses Systems).

    Parameter:
        system: Name des Systems (ifelse, tfidf, word_embeds, sentence_embeds, ki).
        fehler: True = Datensatz mit Fehlern (Schlüssel «<system>_fehler»).
    """
    # Berechnet die Daten und speichert sie in daten.json
    with open(daten_path, "r", encoding="utf-8") as datei:
        daten = json.load(datei)

    if fehler:
        daten[system + "_fehler"] = system_check(system, True)
    else:
        daten[system] = system_check(system)

    with open(daten_path, "w", encoding="utf-8") as datei:
        json.dump(daten, datei, indent=4, ensure_ascii=False)


# ============================================================
# Gemeinsame Vergleichsplots
# ============================================================

def gemeinsame_plots(
    systeme_daten,
    x_beschriftungen,
    Title,
    Fehler=False,
    ylim=[0, 1],
):
    """Erstellt ein Balkendiagramm, das mehrere Systeme oder Datensätze vergleicht, und speichert es als SVG.

    Parameter:
        systeme_daten: Werte pro System (oder bei Fehler=True: zwei Reihen «ohne Fehler» und «mit Fehler»).
        x_beschriftungen: Beschriftungen der Balkengruppen.
        Title: Titel; wird auch als Dateiname verwendet.
        Fehler: True = Vergleich mit und ohne Fehler statt Vergleich der fünf Systeme.
        ylim: Bereich der y-Achse.
    """
    # Vergleicht mehrere Systeme oder Testsätze
    breite = 0.15
    x = numpy.arange(len(x_beschriftungen))

    fig, ax = pyplot.subplots(figsize=(10, 5))

    if Fehler:
        # Vergleich mit und ohne Fehler
        ax.bar(
            x - breite / 2,
            systeme_daten[0],
            width=breite,
            label="Ohne Fehler",
            color=COLORS["blue"],
            edgecolor="none",
            zorder=3,
        )

        ax.bar(
            x + breite / 2,
            systeme_daten[1],
            width=breite,
            label="Mit Fehler",
            color=COLORS["orange"],
            edgecolor="none",
            zorder=3,
        )

    else:
        # Vergleich aller fünf Systeme
        for index, (werte, name, color) in enumerate(
            zip(systeme_daten, SYSTEM_NAMES, SYSTEM_COLORS)
        ):
            ax.bar(
                x + (index - 2) * breite,
                werte,
                width=breite,
                label=name,
                color=color,
                edgecolor="none",
                zorder=3,
            )

        # Durchschnitt aller Systeme darstellen
        if ylim[0] == 0:
            durchschnitt = numpy.mean(systeme_daten, axis=0)

            ax.plot(
                x,
                durchschnitt,
                linestyle="none",
                marker="_",
                color="#111827",
                markersize=20,
                markeredgewidth=2.5,
                label="Durchschnitt",
                zorder=5,
            )

    # Achsen und Beschriftungen
    style_axes(ax)

    ax.set_xticks(x)
    ax.set_xticklabels(x_beschriftungen)
    ax.set_ylabel("Wert")
    ax.set_xlabel("Befehle", labelpad=10)
    ax.set_ylim(ylim[0], ylim[1])

    set_plot_title(
        ax,
        Title,
        width=42,
    )

    if ylim[0] == 0:
        ax.yaxis.set_major_formatter(PercentFormatter(1))

    # Bei vielen Kategorien Beschriftungen etwas kleiner halten
    if len(x_beschriftungen) > 12:
        ax.tick_params(axis="x", labelsize=9)
    
    # Legende unterhalb der Grafik
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.25),
        ncol=3 if not Fehler else 2,
        frameon=False,
    )

    fig.tight_layout()
    fig.savefig(
        plots_path + Title + ".svg",
        bbox_inches="tight",
    )
    pyplot.close(fig)

# ============================================================
# Tabellen
# ============================================================

def tabelle(fehler=False):
    """Erstellt eine Tabelle mit den durchschnittlichen Evaluationsmetriken aller Systeme und speichert sie als SVG.

    Parameter:
        fehler: False = Testdatensatz ohne Fehler, True = Testdatensatz auf fehlerhaften Sätzen.
    Spalten: Accuracy, Precision, Recall und F1.
    """
    # Daten laden
    with open(daten_path, "r", encoding="utf-8") as datei:
        daten = json.load(datei)

    schluessel = ["ifelse", "tfidf", "word_embeds", "sentence_embeds", "ki"]
    suffix = "_fehler" if fehler else ""

    # Zeilen berechnen (ein System pro Zeile)
    zeilen = []    # Anzeige-Werte (Text)
    rohwerte = []  # Zahlenwerte, um die besten Werte hervorzuheben

    for key in schluessel:
        system = daten[key + suffix]
        accuracy, precision, recall, f1 = mean_system(system)[0][0:4]

        rohwerte.append([accuracy, precision, recall, f1])
        zeilen.append([
            f"{accuracy * 100:.1f}%",
            f"{precision * 100:.1f}%",
            f"{recall * 100:.1f}%",
            f"{f1 * 100:.1f}%",
        ])

    spalten = ["System", "Accuracy", "Precision", "Recall", "F1"]
    zellen = [[name] + zeile for name, zeile in zip(SYSTEM_NAMES, zeilen)]

    # Bestes System pro Spalte
    beste = []
    for spalte in range(4):
        werte = [zeile[spalte] for zeile in rohwerte]
        beste.append(werte.index(max(werte)))

    # Tabelle zeichnen
    titel = "Durchschnittliche Evaluationsmetriken der Systeme"
    if fehler:
        titel += " auf fehlerhaften Sätzen"

    fig, ax = pyplot.subplots(figsize=(8, 3))
    ax.axis("off")

    tab = ax.table(
        cellText=zellen,
        colLabels=spalten,
        cellLoc="center",
        loc="center",
        colWidths=[0.3, 0.15, 0.15, 0.15, 0.15],
    )
    tab.auto_set_font_size(False)
    tab.set_fontsize(11)
    tab.scale(1, 2.0)

    for (zeile, spalte), zelle in tab.get_celld().items():
        zelle.set_edgecolor(COLORS["grid"])
        zelle.set_linewidth(0.8)

        if zeile == 0:
            # Kopfzeile
            zelle.set_facecolor(COLORS["navy"])
            zelle.set_text_props(color="white", fontweight="bold")
        else:
            zelle.set_facecolor("#F5F7FA" if zeile % 2 == 0 else COLORS["background"])
            zelle.set_text_props(color=COLORS["text"])

            if spalte == 0:
                # Systemname in der Farbe des Systems
                zelle.set_text_props(
                    color=SYSTEM_COLORS[zeile - 1],
                    fontweight="bold",
                )

    set_plot_title(ax, titel, width=52)

    dateiname = "tabelle_mit_fehler" if fehler else "tabelle_ohne_fehler"
    fig.tight_layout()
    fig.savefig(plots_path + dateiname + ".svg", bbox_inches="tight")
    pyplot.close(fig)

# ============================================================
# Vergleich aller Systeme mit und ohne Fehler
# ============================================================

def vergleich_fehler_plot(metrik="F1"):
    """Erstellt einen Balkenplot, der für alle fünf Systeme die Kennzahl ohne und mit fehlerhaften Testsätzen vergleicht.

    Parameter:
        metrik: "Accuracy", "Precision", "Recall" oder "F1".
    Unter jedem Systemnamen steht die Veränderung in Prozentpunkten.
    """
    metriken = ["Accuracy", "Precision", "Recall", "F1"]
    metrik_index = metriken.index(metrik)

    with open(daten_path, "r", encoding="utf-8") as datei:
        daten = json.load(datei)

    schluessel = ["ifelse", "tfidf", "word_embeds", "sentence_embeds", "ki"]

    ohne = [mean_system(daten[k])[0][metrik_index] * 100 for k in schluessel]
    mit = [mean_system(daten[k + "_fehler"])[0][metrik_index] * 100 for k in schluessel]

    # Veränderung in Prozentpunkten unter den Systemnamen
    beschriftungen = [
        f"{name}\n{m - o:+.1f} PP".replace("-", "−")
        for name, o, m in zip(SYSTEM_NAMES, ohne, mit)
    ]

    x = numpy.arange(len(SYSTEM_NAMES))
    breite = 0.36

    fig, ax = pyplot.subplots(figsize=(11, 6.5))

    balken_ohne = ax.bar(
        x - breite / 2,
        ohne,
        width=breite,
        label="Ohne Fehler",
        color=COLORS["blue"],
        edgecolor="none",
        zorder=3,
    )
    balken_mit = ax.bar(
        x + breite / 2,
        mit,
        width=breite,
        label="Mit Fehler",
        color=COLORS["orange"],
        edgecolor="none",
        zorder=3,
    )

    for balken in (balken_ohne, balken_mit):
        ax.bar_label(
            balken,
            fmt="%.1f%%",
            padding=4,
            fontsize=10,
            color=COLORS["text"],
        )

    style_axes(ax)

    ax.set_xticks(x)
    ax.set_xticklabels(beschriftungen)
    ax.set_ylim(0, 105)
    ax.yaxis.set_major_formatter(PercentFormatter(100))
    ax.set_ylabel(metrik)
    ax.set_xlabel("System (Veränderung durch Fehler in PP)")

    set_plot_title(
        ax,
        "Robustheit der Systeme: " + metrik + " mit und ohne fehlerhafte Sätze",
        width=60,
    )

    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.18),
        ncol=2,
        frameon=False,
    )

    fig.tight_layout()
    fig.savefig(
        plots_path + "vergleich_alle_systeme_mit_ohne_fehler_" + metrik + ".svg",
        bbox_inches="tight",
    )
    pyplot.close(fig)

# ============================================================
# Alle Plots erstellen
# ============================================================

def get_all_plots():
    """Liest daten.json und erstellt sämtliche Plots (Einzelplots je System, Vergleichsplots, MCC, Vergleich mit/ohne Fehler, Anzahl Testsätze, Rechenzeiten)."""
    # Erstellt sämtliche Plots anhand der gespeicherten Daten
    print("Starte all Plots erstellen.")

    with open(daten_path, "r", encoding="utf-8") as datei:
        print("Lade Daten")
        daten = json.load(datei)

    times = [[] for _ in range(5)]

    # --------------------------------------------------------
    # Testdatensatz ohne Fehler
    # --------------------------------------------------------

    ohne_fehler = []
    mcc_ohne_fehler = []

    system_liste = [
        [daten["ifelse"], "Keyword Matching System"],
        [daten["tfidf"], "TF-IDF System"],
        [daten["word_embeds"], "Wort Embeddings System"],
        [daten["sentence_embeds"], "Satz Embeddings System"],
        [daten["ki"], "Künstliche Intelligenz"],
    ]

    for index, system in enumerate(system_liste):
        print("Beginne ", system[1])

        data = create_all_plots_per_system(
            system[0],
            system[1],
        )

        for time in data[1][4]:
            times[index].append(time)

        mcc_ohne_fehler.append(data[0][2])

        print("Fertig ", system[1])
        ohne_fehler.append(data)

    # --------------------------------------------------------
    # Testdatensatz auf fehlerhaften Sätzen
    # --------------------------------------------------------

    mit_fehler = []
    mcc_mit_fehler = []

    system_liste_fehler = [
        [
            daten["ifelse_fehler"],
            "Keyword Matching System mit fehlerhaften Testsätzen",
        ],
        [
            daten["tfidf_fehler"],
            "TF-IDF System mit fehlerhaften Testsätzen",
        ],
        [
            daten["word_embeds_fehler"],
            "Wort Embeddings System mit fehlerhaften Testsätzen",
        ],
        [
            daten["sentence_embeds_fehler"],
            "Satz Embeddings System mit fehlerhaften Testsätzen",
        ],
        [
            daten["ki_fehler"],
            "Künstliche Intelligenz mit fehlerhaften Testsätzen",
        ],
    ]

    for index, system in enumerate(system_liste_fehler):
        print("Beginne ", system[1])

        data = create_all_plots_per_system(
            system[0],
            system[1],
        )

        for time in data[1][4]:
            times[index].append(time)

        mcc_mit_fehler.append(data[0][2])

        print("Fertig ", system[1])
        mit_fehler.append(data)

    # --------------------------------------------------------
    # Durchschnittliche Evaluationsmetriken
    # --------------------------------------------------------

    gemeinsame_plots(
        [x[0][0] for x in ohne_fehler],
        ["Accuracy", "Precision", "Recall", "F1"],
        "Durchschnittliche Evaluationsmetriken aller Systeme",
    )

    gemeinsame_plots(
        [x[0][0] for x in mit_fehler],
        ["Accuracy", "Precision", "Recall", "F1"],
        "Durchschnittliche Evaluationsmetriken aller Systeme auf fehlerhaften Sätzen",
    )
    
    # --------------------------------------------------------
    # Tabellen (ohne und mit Fehler)
    # --------------------------------------------------------

    tabelle(False)
    tabelle(True)

    # --------------------------------------------------------
    # MCC-Vergleich
    # --------------------------------------------------------

    gemeinsame_plots(
        mcc_ohne_fehler,
        ["MCC"],
        "Alle Systeme durchschnittlicher MCC",
        False,
        [-1, 1],
    )

    gemeinsame_plots(
        mcc_mit_fehler,
        ["MCC"],
        "Alle Systeme durchschnittlicher MCC auf fehlerhaften Sätzen",
        False,
        [-1, 1],
    )

    # --------------------------------------------------------
    # Evaluationsmetriken pro Befehl
    # --------------------------------------------------------

    for index, metrik in enumerate(
        ["Precision", "Recall", "F1-Score"]
    ):
        gemeinsame_plots(
            [x[1][index] for x in ohne_fehler],
            range(28),
            metrik + " aller Systeme pro Befehl",
        )

        gemeinsame_plots(
            [x[1][index] for x in mit_fehler],
            range(28),
            "Alle Systeme " + metrik
            + " pro Befehl auf fehlerhaften Sätzen",
        )

    # --------------------------------------------------------
    # Vergleich jedes Systems mit und ohne Fehler
    # --------------------------------------------------------

    for index, system in enumerate(SYSTEM_NAMES):
        print(system, " Vergleich mit und ohne Fehler.")

        # Durchschnittliche Evaluationsmetriken
        gemeinsame_plots(
            [
                ohne_fehler[index][0][0][0:4],
                mit_fehler[index][0][0][0:4],
            ],
            ["Accuracy", "Precision", "Recall", "F1"],
            "Vergleich " + system + " mit und ohne Fehler",
            Fehler=True,
        )

        # Metriken pro Befehl
        for metrik_index, metrik in enumerate(
            ["Precision", "Recall", "F1-Score"]
        ):
            gemeinsame_plots(
                [
                    ohne_fehler[index][1][metrik_index],
                    mit_fehler[index][1][metrik_index],
                ],
                range(28),
                "Vergleich " + system + " " + metrik
                + " pro Befehl mit und ohne Fehler",
                Fehler=True,
            )

    # ========================================================
    # Support pro Befehl
    # ========================================================

    training_support = [
        len(dataset[i]["examples"]) for i in range(28)
    ]

    validation_support = [
        len(validation_dataset[i]["examples"]) for i in range(28)
    ]

    test_support = [
        len(test_dataset[i]["examples"]) for i in range(28)
    ]

    test_fehler_support = [
        len(test_dataset_fehler[i]["examples"]) for i in range(28)
    ]

    x = numpy.arange(28)
    breite = 0.2

    fig, ax = pyplot.subplots(figsize=(16, 7))

    support_daten = [
        (
            training_support,
            "Trainingsdatensatz",
            COLORS["navy"],
        ),
        (
            validation_support,
            "Validierungsdatensatz",
            COLORS["blue"],
        ),
        (
            test_support,
            "Testdatensatz",
            COLORS["teal"],
        ),
        (
            test_fehler_support,
            "Testdatensatz mit Fehlern",
            COLORS["orange"],
        ),
    ]

    for index, (werte, label, color) in enumerate(support_daten):
        ax.bar(
            x + (index - 1.5) * breite,
            werte,
            width=breite,
            label=label,
            color=color,
            edgecolor="none",
            zorder=3,
        )

    ax.set_ylabel("Anzahl Testsätze")
    ax.set_xlabel("Befehl")
    ax.set_xticks(x)
    ax.set_xticklabels(range(28))

    set_plot_title(
        ax,
        "Anzahl Beispielsätze pro Befehl und Datensatz",
        width=38,
    )

    style_axes(ax)

    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.12),
        ncol=2,
        frameon=False,
    )

    fig.tight_layout()
    fig.savefig(
        plots_path + "support_per_command.svg",
        bbox_inches="tight",
    )
    pyplot.close(fig)

    # ========================================================
    # Durchschnittliche Rechenzeiten pro System
    # ========================================================

    times_clear = []
    standardabweichungen = []

    # Durchschnitt und Standardabweichung berechnen
    for system_times in times:
        standardabweichungen.append(
            numpy.std(numpy.array(system_times))
        )
        times_clear.append(sum(system_times) / len(system_times))

    fig, ax = pyplot.subplots(figsize=(10, 5))

    bars = ax.bar(
        SYSTEM_NAMES,
        times_clear,
        yerr=standardabweichungen,
        capsize=5,
        color=SYSTEM_COLORS,
        edgecolor="none",
        error_kw={
            "ecolor": COLORS["gray"],
            "elinewidth": 1.3,
            "capthick": 1.3,
        },
        zorder=3,
    )

    ax.bar_label(
        bars,
        labels=[f"{value:.3e}" for value in times_clear],
        padding=5,
        fontsize=9,
        color=COLORS["text"],
    )

    ax.set_ylabel("Zeit (s)")
    ax.set_xlabel("System")
    ax.set_yscale("log")

    set_plot_title(
        ax,
        "Durchschnittliche Verarbeitungszeit der Systeme",
        width=50,
    )

    style_axes(ax)
    ax.tick_params(axis="x")

    fig.tight_layout()
    fig.savefig(
        plots_path + "calculating_times_of_systems.svg",
        bbox_inches="tight",
    )
    pyplot.close(fig)

    # --------------------------------------------------------
    # Zusätzliche Statistiken für Wort-Embeddings
    # --------------------------------------------------------

    x = numpy.array(times[2])

    print("Zeiten: ", times_clear)
    print("Standardabweichungen ", standardabweichungen)

    print("Min:", numpy.min(x))
    print("Max:", numpy.max(x))
    print("Mean:", numpy.mean(x))
    print("Median:", numpy.median(x))
    print("Std:", numpy.std(x, ddof=1))

    print(
        "DATEN WURDEN AUS DATEN.JSON GENOMMEN. "
        "BEI SELTSAMEN ERGEBNISSEN JSON DATEI ÜBERPRÜFEN!"
    )


if __name__ == "__main__":
    #system_check(system)
    # for i in ["ifelse", "tfidf", "word_embeds", "sentence_embeds", "ki"]:
    #     create_data(i)
    #     create_data(i, True)


    # # #create_all_plots_per_system(system_check("sentence_embeds"), "Satz Embeddings")
    # #get_all_plots()
    # create_data("word_embeds")
    # create_data("word_embeds", True)
    #get_all_plots()
    # tabelle(True)
    vergleich_fehler_plot("Recall")
    vergleich_fehler_plot("Precision")
    vergleich_fehler_plot()
    vergleich_fehler_plot("Accuracy")
    pass


#####################################################
# Befehl falsch erkannt wurde pro Befehl confusion matrix
# Durchschnittliche Accuracy, Precision, recall und F1 Score der systeme = mean_system(system_check(system))[0]/[1]/[2]/[3]
# Durchschnittliche Accuracy, Precision und F1 Score pro Befehl der systeme = mean_system_per_command(system_check(system))[0]/[1]/[2]/[3]
# Anzahl gleiche falsch erkannte sätze (zb alle sätze haben 5 sätze falsch, alle ausser ... haben 2 falsch usw.)
# Durchschnittliche Accuracy, Precision und F1 Score der systeme bei daten mit fehlern in den sätzen = wie bei den anderen einfach mit falschen daten
# Durchschnittliche Accuracy, Precision und F1 Score pro Befehl der systeme bei daten mit fehlern in den sätzen = wie bei den anderen einfach mit falschen daten
# unterschied zwischen mit und ohne fehler
# durchschnittliche geschwindigkeit der systeme = system_check(system)[3]
