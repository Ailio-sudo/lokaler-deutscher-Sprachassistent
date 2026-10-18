"""Statistische Auswertung mit dem Paired-Bootstrap-Test (nach Berg-Kirkpatrick et al., 2012).

Verwendet die Rohdaten aus daten.json (siehe test_system.py). Verglichen wird der Macro-F1-Score:
  - alle fünf Systeme paarweise (10 Paare) auf dem fehlerfreien Testdatensatz,
  - jedes System mit und ohne Fehler in den Sätzen,
  - 95-%-Konfidenzintervalle des Macro-F1 je System.
Beim Ausführen der Datei läuft alles am Ende der Datei direkt ab; die Ergebnisse werden in der Konsole ausgegeben.
Die Anzahl der Bootstrap-Stichproben steht in den Aufrufen am Ende (create_bootstrap_data und create_bootstrap_data_fehler).
"""
import random
import json
from test_dataset import test_dataset, test_dataset_fehler
from sklearn.metrics import f1_score
from itertools import combinations
from test_system import mean_system
random.seed(0)
from pathlib import Path
daten_path = Path(__file__).resolve().parent/"daten.json"
print(daten_path)
# Prüfen, ob beide Testdatensätze gleich viele Sätze enthalten
if sum(len(intent["examples"]) for intent in test_dataset.values()) != sum(len(intent["examples"]) for intent in test_dataset_fehler.values()):
    print(sum(len(intent["examples"]) for intent in test_dataset.values()))
    print(sum(len(intent["examples"]) for intent in test_dataset_fehler.values()))
    print("Datensätze nicht gleich lange")
    raise SystemError
else:
    print(sum(len(intent["examples"]) for intent in test_dataset.values()))

# Funktionen für Daten ohne Fehler
def create_bootstrap_data(amount):
    """Zieht Bootstrap-Stichproben (mit Zurücklegen) aus dem Testdatensatz und berechnet die F1-Differenzen aller Systempaare.

    Parameter:
        amount: Anzahl der Bootstrap-Stichproben.
    Rückgabe: (Liste mit 10 Listen von Differenzen, je eine pro Systempaar in der Reihenfolge von itertools.combinations;
               die F1-Werte der letzten Stichprobe).
    """
    # Bootstrap-Stichproben für F1-Score-Vergleich erstellen
    print("Lade Daten")
    with open(daten_path, "r", encoding="utf-8") as datei:
        daten = json.load(datei)

    # Testsätze mit zugehörigem Intent speichern
    texts_with_intent = []
    for intent_data in test_dataset.values():
        for example in intent_data["examples"]:
            texts_with_intent.append((example, int(intent_data["intent"])))

    print("Fertig")

    differences = [[] for i in range(10)]
    for i in range(amount):
        # Bootstrap-Stichprobe mit Zurücklegen
        indexes = [random.randint(0, len(texts_with_intent) - 1) for i in range(len(texts_with_intent))]
        gold = [texts_with_intent[i][1] for i in indexes]

        # Vorhersagen aller Systeme
        predictions = [[daten["ifelse"][i][0] for i in indexes], [daten["tfidf"][i][0] for i in indexes], [daten["word_embeds"][i][0] for i in indexes], [daten["sentence_embeds"][i][0] for i in indexes], [daten["ki"][i][0] for i in indexes]]

        # F1-Scores berechnen
        f1_scores = [f1_score(gold, pred, average="macro") for pred in predictions]

        # F1-Differenzen zwischen den Systempaaren speichern
        for index, (system_a, system_b) in enumerate(combinations(range(5), 2)):
            differences[index].append(f1_scores[system_a] - f1_scores[system_b])

    return differences, f1_scores

def calculate_p_value(differences):
    """Berechnet die p-Werte der Systempaare.

    Für jedes Paar wird der Anteil der Bootstrap-Stichproben bestimmt, deren Differenz mindestens doppelt so gross ist wie die
    tatsächlich gemessene F1-Differenz (bei negativer Differenz entsprechend umgekehrt).
    Rückgabe: Liste [p-Wert, Name des Paares].
    """
    # p-Werte aus den Bootstrap-Daten berechnen
    real_difference = []
    with open(daten_path, "r", encoding="utf-8") as datei:
        daten = json.load(datei)

    # Tatsächliche F1-Scores der Systeme
    systems = [
    mean_system(daten["ifelse"])[0][3],
    mean_system(daten["tfidf"])[0][3],
    mean_system(daten["word_embeds"])[0][3],
    mean_system(daten["sentence_embeds"])[0][3],
    mean_system(daten["ki"])[0][3]
    ]

    # Tatsächliche F1-Differenzen der Systempaare
    for f1_a, f1_b in combinations(systems, 2):
        real_difference.append(f1_a - f1_b)

    reihenfolge = [
        "ifelse - tfidf",
        "ifelse - word_embeds",
        "ifelse - sentence_embeds",
        "ifelse - ki",
        "tfidf - word_embeds",
        "tfidf - sentence_embeds",
        "tfidf - ki",
        "word_embeds - sentence_embeds",
        "word_embeds - ki",
        "sentence_embeds - ki"
    ]

    p_values = []

    # p-Werte für jedes Systempaar berechnen
    for index,difference in enumerate(differences):
        counter=0
        for differenz in difference:
            # Bootstrap-Differenz mit tatsächlicher Differenz vergleichen
            if real_difference[index] >= 0:
                if differenz >= 2 * real_difference[index]:
                    counter += 1
            else:
                if differenz <= 2 * real_difference[index]:
                    counter += 1

        p_values.append([counter/len(difference), reihenfolge[index]])

    return p_values

# Funktionen für Daten mit Fehler
def create_bootstrap_data_fehler(amount):
    """Wie create_bootstrap_data, aber für den Vergleich «ohne Fehler» gegen «mit Fehler» je System.

    Rückgabe: (F1-Differenzen je System, F1-Werte ohne Fehler je System, F1-Werte mit Fehler je System).
    """
    # Bootstrap-Stichproben für Vergleich mit/ohne Fehler erstellen
    print("Lade Daten")
    with open(daten_path, "r", encoding="utf-8") as datei:
        daten = json.load(datei)

    # Testsätze mit zugehörigem Intent speichern
    texts_with_intent = []
    for intent_data in test_dataset.values():
        for example in intent_data["examples"]:
            texts_with_intent.append((example, int(intent_data["intent"])))

    print("Fertig")

    systems = ["ifelse", "tfidf", "word_embeds", "sentence_embeds", "ki"]
    differences = []
    f1_scores_list = []
    f1_scores_list_fehler = []

    for i in range(5):
        differences.append([]) # F1-Differenzen
        f1_scores_list.append([]) # F1-Scores ohne Fehler
        f1_scores_list_fehler.append([]) # F1-Scores mit Fehler

    for i in range(amount):
        # Bootstrap-Stichprobe erstellen
        indexes = [random.randint(0, len(texts_with_intent) - 1) for i in range(len(texts_with_intent))]

        gold = [texts_with_intent[i][1] for i in indexes]

        # Vorhersagen ohne und mit Fehler
        predictions = [[daten[system][i][0] for i in indexes] for system in systems]
        predictions_fehler = [[daten[system + "_fehler"][i][0] for i in indexes] for system in systems]

        # F1-Scores berechnen
        f1_scores = [f1_score(gold, pred, average="macro") for pred in predictions]
        f1_scores_fehler = [f1_score(gold, pred, average="macro") for pred in predictions_fehler]

        # Ergebnisse speichern
        for index in range(5):
            differences[index].append(f1_scores[index] - f1_scores_fehler[index])
            f1_scores_list[index].append(f1_scores[index])
            f1_scores_list_fehler[index].append(f1_scores_fehler[index])

    return differences, f1_scores_list, f1_scores_list_fehler

def calculate_p_value_fehler(differences):
    """Berechnet den p-Wert je System für den Unterschied zwischen fehlerfreien und fehlerhaften Sätzen (gleiches Verfahren wie calculate_p_value). Rückgabe: Liste [p-Wert, Systemname]."""
    real_difference = []

    with open(daten_path, "r", encoding="utf-8") as datei:
        daten = json.load(datei)

    systems = ["ifelse", "tfidf", "word_embeds", "sentence_embeds", "ki"]

    # Tatsächliche F1-Differenzen mit/ohne Fehler
    for system in systems:
        real_difference.append(mean_system(daten[system])[0][3] - mean_system(daten[system + "_fehler"])[0][3])

    # p-Werte berechnen
    p_values = []
    for index, difference in enumerate(differences):
        counter = 0
        for differenz in difference:

            # Bootstrap-Differenz mit tatsächlicher Differenz vergleichen
            if real_difference[index] >= 0:

                if differenz >= 2 * real_difference[index]:
                    counter += 1
            else:
                if differenz <= 2 * real_difference[index]:
                    counter += 1

        p_values.append([counter / len(difference), systems[index]])

    return p_values

def calculate_confidence_intervals_f1(f1_lists):
    """Berechnet 95-%-Konfidenzintervalle der F1-Scores aus den Bootstrap-Werten (2.5- und 97.5-Prozent-Quantil).
    Rückgabe: Liste [Systemname, untere Grenze, obere Grenze].
    """
    # 95%-Konfidenzintervalle für die F1-Scores berechnen
    systems = ["ifelse", "tfidf", "word_embeds", "sentence_embeds", "ki"]

    results = []
    for index, f1_list in enumerate(f1_lists):
        sorted_f1 = sorted(f1_list)
        n = len(sorted_f1)

        # Untere und obere Grenze des Intervalls
        lower = sorted_f1[int(0.025 * n)]
        upper = sorted_f1[int(0.975 * n) - 1]

        results.append([systems[index], lower, upper])

    return results


###########################################
# ALLE BOOTSTRAP-TESTS DURCHFÜHREN

# 1. Bootstrap für Vergleich der Systeme OHNE Fehler
# Anzahl Bootstrap-Stichproben: hier 10**6. Die Ergebnisse sind im Kommentar am Dateiende.
data_ohne_fehler = create_bootstrap_data(10**6)

# 2. Bootstrap für Vergleich MIT und OHNE Fehler
data_mit_fehler = create_bootstrap_data_fehler(10**6)


###########################################
# p-Werte: Vergleich der Systeme OHNE Fehler


print("P-WERTE: VERGLEICH DER SYSTEME OHNE FEHLER")


print(calculate_p_value(data_ohne_fehler[0]))


###########################################
# p-Werte: Vergleich MIT vs. OHNE Fehler


print("P-WERTE: MIT FEHLER vs. OHNE FEHLER")


print(calculate_p_value_fehler(data_mit_fehler[0]))


###########################################
# Konfidenzintervalle: OHNE Fehler


print("95%-KONFIDENZINTERVALLE OHNE FEHLER")


print(calculate_confidence_intervals_f1(data_mit_fehler[1]))


###########################################
# Konfidenzintervalle: MIT Fehler

print("95%-KONFIDENZINTERVALLE MIT FEHLER")

print(calculate_confidence_intervals_f1(data_mit_fehler[2]))



# Tabelle 1: Macro-F1, 10^6 Bootstrap-Stichproben

# System	F1 ohne Fehler [95-%]	F1 mit Fehler [95-%]	ΔF1 (ohne − mit)	p-Wert
# ifelse	0.719 [0.697, 0.738]	0.586 [0.562, 0.607]	+0.133	< 1e-6
# tfidf	0.897 [0.883, 0.909]	0.697 [0.675, 0.715]	+0.200	< 1e-6
# word_embeds	0.874 [0.860, 0.887]	0.658 [0.635, 0.677]	+0.216	< 1e-6
# sentence_embeds	0.930 [0.920, 0.939]	0.816 [0.800, 0.831]	+0.114	< 1e-6
# ki	0.977 [0.970, 0.984]	0.943 [0.932, 0.952]	+0.035	< 1e-6

# Tabelle 2: Paarweiser Systemvergleich ohne Fehler

# Paar	ΔF1 (beobachteter Wert)	p-Wert
# ifelse − tfidf	−0.178	< 1e-6
# ifelse − word_embeds	−0.155	< 1e-6
# ifelse − sentence_embeds	−0.211	< 1e-6
# ifelse − ki	−0.258	< 1e-6
# tfidf − word_embeds	+0.023	0.000825
# tfidf − sentence_embeds	−0.033	0.000009
# tfidf − ki	−0.080	< 1e-6
# word_embeds − sentence_embeds	−0.056	< 1e-6
# word_embeds − ki	−0.103	< 1e-6
# sentence_embeds − ki	−0.047	< 1e-6