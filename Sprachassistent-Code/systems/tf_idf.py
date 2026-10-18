"""TF-IDF-System: Intent-Erkennung mit TF-IDF-Merkmalen und multinomialer logistischer Regression (scikit-learn).

Beim Import wird eine Pipeline (TfidfVectorizer + LogisticRegression) entweder aus models/self_trained geladen
oder mit den Trainingsdaten (training_data.py) neu trainiert und dort gespeichert. Mit do_grid_search = True
werden stattdessen die Hyperparameter per GridSearchCV (10-fold, Macro-F1) gesucht und danach der beste
Threshold auf dem Validierungsdatensatz bestimmt (Ausgabe in der Konsole).
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import f1_score
from pathlib import Path
import pickle
import sys
sys.path.append(str(Path(__file__).resolve().parent))
from training_data import dataset, validation_dataset

print("Bereite TF-IDF vor...")


# Standardparameter
# Standardwerte des Systems: Threshold, Regularisierungsparameter C und Einstellungen des TfidfVectorizers
STANDARD_THRESHOLD = 0.35
STANDARD_C = 14
STANDARD_NGRAM_RANGE = (1, 1)
STANDARD_MIN_DF = 1


# Grid Search aktivieren/deaktivieren
# True = Hyperparameter und Threshold suchen statt das gespeicherte Modell zu verwenden
do_grid_search=False

# Speicherort der trainierten Pipeline (Ordner models/self_trained im Projekt; wird beim Speichern bei Bedarf angelegt)
model_file = Path(__file__).resolve().parent.parent.parent / "models" / "self_trained" / "tf_idf_with_mlr"

# Wenn vorhanden und keine Suche gewünscht: gespeicherte Pipeline laden. Sonst die Pipeline neu aufbauen.
# TF-IDF und Logistic Regression als Pipeline
if Path(model_file).exists() and not do_grid_search:
    print("Lade vortrainierte TF-IDF Pipeline")
    model = pickle.load(open(model_file, 'rb'))

else:
    print("Trainiere neues Modell")
    model = Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                ngram_range=STANDARD_NGRAM_RANGE, #(1,1)
                min_df=STANDARD_MIN_DF, #1
                smooth_idf=False
            )
        ),
        (
            "clf",
            LogisticRegression(
                max_iter=1000,
                class_weight="balanced",
                C=STANDARD_C #14
            )
        )
    ])
    # Trainingsdaten sammeln und normalisieren
    texts = []
    # Die Labels im Datensatz sind Strings (z. B. "12"); bei der Vorhersage wird deshalb int() verwendet
    labels = []

    for item in dataset.values():
        intent = item["intent"]

        for satz in item["examples"]:
            texts.append(satz.lower())
            labels.append(intent)


def predict_intent(text, threshold=STANDARD_THRESHOLD):
    """Bestimmt die Befehlsnummer zu einem Satz.

    Parameter:
        text: Der Satz (wird in Kleinbuchstaben umgewandelt).
        threshold: Mindest-Wahrscheinlichkeit der besten Klasse (Standard: STANDARD_THRESHOLD).
    Rückgabe: Tupel (Befehlsnummer, Wahrscheinlichkeit). Liegt die beste Wahrscheinlichkeit unter dem Threshold,
    wird (0, None) zurückgegeben (unbekannter Befehl).
    """
    # Wahrscheinlichste Klasse und Confidence bestimmen
    predicts = model.predict_proba([text.lower()])[0]
    best_prediction_index = predicts.argmax()

    # Bei zu geringer Confidence kein Intent
    if predicts[best_prediction_index] < threshold:
        return 0, None

    return int(model.classes_[best_prediction_index]), predicts.max()




if do_grid_search:
    print("Grid Search machen")

    # Beste Modellparameter suchen
    grid_parameters = {
        "tfidf__ngram_range": [(1, 1)],#{"tfidf__ngram_range": [(1, 1), (1, 2), (1, 3)]
        "tfidf__min_df": [1], #"tfidf__min_df": [1,2,3,4,5]
        "clf__C": [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15] #"clf__C": [0.1, 1, 10, 100, 1000]} 10 ist die beste
    }

    grid = GridSearchCV(
        model,
        grid_parameters,
        cv=10,
        scoring="f1_macro",
        n_jobs=-1,
        verbose=3
    )

    grid.fit(texts, labels)

    print("Beste Parameter: ", grid.best_params_)
    print("Beste Evaluationsmetrik: ", grid.best_score_)

    # Bestes Modell übernehmen
    model = grid.best_estimator_
    validation_labels = []

    # Validierungslabels sammeln
    for item in validation_dataset.values():
        for satz in item["examples"]:
            validation_labels.append(int(item["intent"]))

    thresholds_with_score = []

    # Vorhersagen und Confidences für Validierungsdaten berechnen
    predictions_with_intents = []

    for item in validation_dataset.values():
        for satz in item["examples"]:
            prediction = predict_intent(satz, 0)
            predictions_with_intents.append(prediction)

    # Verschiedene Thresholds mit F1-Score vergleichen
    for threshold in range(0, 101):
        thresholds_predictions = []
        threshold = threshold / 100

        for intent, confidence in predictions_with_intents:
            if confidence < threshold:
                thresholds_predictions.append(0)
            else:
                thresholds_predictions.append(intent)

        score = f1_score(
            validation_labels,
            thresholds_predictions,
            average="macro"
        )

        print(threshold, ": ", score)
        thresholds_with_score.append([score, threshold])

    # Thresholds nach F1-Score sortieren
    thresholds_with_score.sort(
        key=lambda x: x[0],
        reverse=True
    )

    print(thresholds_with_score)

# Ohne Grid Search und ohne gespeichertes Modell: mit den Standardparametern trainieren und speichern
elif not Path(model_file).exists():
    # Modell mit Standardparametern trainieren
    model.fit(texts, labels)
    model_file.parent.mkdir(parents=True, exist_ok=True)
    pickle.dump(model, open(model_file, 'wb'))
    print("Modell gespeichert")


    # Anzahl der erzeugten TF-IDF-Features ausgeben
    features = model.named_steps["tfidf"].get_feature_names_out()

    print("Unigramme:", len([x for x in features if len(x.split()) == 1]))
    print("Bigramme:", len([x for x in features if len(x.split()) == 2]))
    print("Gesamt:", len(features))


if __name__ == "__main__":
    print(predict_intent("spiele das lied never. fit in a box"))
    print(predict_intent("spiel das lied never fit in a box von xandra"))
    print(predict_intent("was ist ein auto?"))
    print(predict_intent("xaxaxaxa"))
