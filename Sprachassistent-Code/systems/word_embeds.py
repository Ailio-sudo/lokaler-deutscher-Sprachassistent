"""Word-Embeddings-System: Wortvektoren (FastText «cc.de.300.bin») + multinomiale logistische Regression.

Jedes Wort eines Satzes wird in einen 300-dimensionalen Vektor umgewandelt, der Satzvektor ist der Durchschnitt
der Wortvektoren (make_sentence_vector). Eine logistische Regression ordnet den Satzvektor einem Befehl zu.
Das FastText-Modell wird aus dem Ordner models geladen und bei Bedarf automatisch heruntergeladen (mehrere GB).
Die trainierte Regression wird in models/self_trained gespeichert.
"""
import numpy as np
from sklearn.linear_model import LogisticRegression
import string
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import f1_score
from pathlib import Path
import pickle
import sys
sys.path.append(str(Path(__file__).resolve().parent))
from training_data import dataset, validation_dataset
import urllib.request
import gzip
import shutil
from gensim.models.fasttext import load_facebook_vectors

print("Lade FastText...")

# Speicherort des FastText-Modells (Ordner models im Projekt)
model_path = (Path(__file__).resolve().parent.parent.parent / "models" / "cc.de.300.bin")

if not model_path.exists():
    print("Fasttext-Modell nicht gefunden")
    print("Lade Fasttext herunter...")
    gz_path = model_path.with_suffix(".bin.gz")
    urllib.request.urlretrieve(
        "https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.de.300.bin.gz",
        gz_path,
    )

    with gzip.open(gz_path, "rb") as src:
        with model_path.open("wb") as dst:
            shutil.copyfileobj(src, dst)

    gz_path.unlink()
    print("Download abgeschlossen.")

# Nur die Wortvektoren laden (reicht für make_sentence_vector)
wv = load_facebook_vectors(str(model_path))
print("FastText geladen.")


# Standardparameter
# Standardwerte des Systems: Threshold und Regularisierungsparameter C der logistischen Regression
STANDARD_THRESHOLD = 0.55
STANDARD_C = 200


# Grid Search aktivieren/deaktivieren
# True = C und Threshold per Grid Search bzw. Threshold-Suche bestimmen statt das gespeicherte Modell zu verwenden
do_grid_search = False


def make_sentence_vector(sentence):
    """Wandelt einen Satz in einen Vektor um.

    Der Satz wird in Kleinbuchstaben umgewandelt, an Leerzeichen in Wörter zerlegt und Satzzeichen am Wortanfang
    und -ende werden entfernt. Der Satzvektor ist der Mittelwert der Wortvektoren.
    Rückgabe: numpy-Vektor oder None, wenn der Satz keine Wörter enthält.
    """
    vectors = []

    # Vektor für jedes Wort erzeugen
    for token in sentence.lower().split():
        word = token.strip(string.punctuation)
        vectors.append(wv.get_vector(word)) # FastText erzeugt auch Vektoren für unbekannte Wörter

    # Durchschnitt der Wortvektoren als Satzvektor
    return np.mean(vectors, axis=0) if vectors else None


def word_embeddings(input_text, threshold=STANDARD_THRESHOLD):
    """Bestimmt die Befehlsnummer zu einem Satz.

    Parameter:
        input_text: Der Satz.
        threshold: Mindest-Wahrscheinlichkeit der besten Klasse (Standard: STANDARD_THRESHOLD).
    Rückgabe: Tupel (Befehlsnummer, Wahrscheinlichkeit). (0, None) bei leerem Satz, (0, Wahrscheinlichkeit)
    wenn die Wahrscheinlichkeit unter dem Threshold liegt (unbekannter Befehl).
    """
    # Satzvektor und Klassenwahrscheinlichkeiten berechnen
    input_vector = make_sentence_vector(input_text)

    if input_vector is None:
        return 0, None

    probabilities = classifier.predict_proba([input_vector])[0]
    highest_index = probabilities.argmax()
    confidence = probabilities[highest_index]
    intent = classifier.classes_[highest_index]

    # Bei zu geringer Confidence kein Intent
    if confidence < threshold:
        return 0, confidence

    return int(intent), confidence


model_file = Path(__file__).resolve().parent.parent.parent / "models" / "self_trained" / "mlr_word_embeddings"

# Trainingsdaten werden nur gebraucht, wenn trainiert oder gesucht wird: Sätze in Vektoren umwandeln
if not Path(model_file).exists() or do_grid_search:
    train_sentences = []
    train_labels = []

    # Trainingsdaten in Vektoren und Labels umwandeln
    for intent_id, data in dataset.items():
        for sentence in data["examples"]:
            vector = make_sentence_vector(sentence)

            if vector is None:
                continue

            train_sentences.append(vector)
            train_labels.append(data["intent"])

    print(f"{len(train_sentences)} Trainingssätze")


if do_grid_search:
    print("Trainiere MLR Modell")
    # Besten C-Wert per Grid Search bestimmen
    classifier = LogisticRegression(
        max_iter=1000,
        class_weight="balanced"
    )

    print("Grid Search machen")

    grid_parameters = {
        "C": [50, 60, 70, 80, 90, 100, 200, 300, 400, 500]
    }

    grid = GridSearchCV(
        classifier,
        grid_parameters,
        cv=10,
        scoring="f1_macro",
        n_jobs=-1,
        verbose=3
    )

    grid.fit(
        np.array(train_sentences),
        np.array(train_labels)
    )

    print("Beste Parameter: ", grid.best_params_)
    print("Beste Evaluationsmetrik: ", grid.best_score_)

    # Bestes Modell übernehmen
    classifier = grid.best_estimator_
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
            prediction = word_embeddings(satz, 0)
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

else:
    model_file = Path(__file__).resolve().parent.parent.parent / "models" / "self_trained" / "mlr_word_embeddings"
    if Path(model_file).exists():
        print("Lade vortrainiertes MLR-Modell..")
        classifier = pickle.load(open(model_file, 'rb'))
    else: # Modell mit Standardparametern trainieren
        print("Trainiere neues MLR-Modell")
        classifier = LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            C=STANDARD_C
        )

        classifier.fit(
            np.array(train_sentences),
            np.array(train_labels)
        )
        model_file.parent.mkdir(parents=True, exist_ok=True)
        pickle.dump(classifier, open(model_file, 'wb'))
        print("Neues MLR-Modell trainiert und Gespeichert")
print("Logistic Regression bereit")


if __name__ == "__main__":
    print("xyzabcqwe" in wv.key_to_index)
    print(word_embeddings(input("Welchen Befehl möchtest du ausführen? ")))
