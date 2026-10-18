"""Sentence-Embeddings-System: Satzvektoren mit Qwen3-Embedding-0.6B + multinomiale logistische Regression.

Der ganze Satz wird mit einer Anweisung (format_query) vom Modell in einen Vektor umgewandelt. Eine logistische
Regression ordnet ihn einem Befehl zu. Das Modell wird aus dem Ordner models geladen und bei Bedarf von
Hugging Face heruntergeladen. Es läuft auf der GPU (CUDA), wenn verfügbar, sonst auf der CPU.
Die trainierte Regression wird in models/self_trained gespeichert.
"""
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import f1_score
from pathlib import Path
import pickle
import torch
import sys
sys.path.append(str(Path(__file__).resolve().parent))
from training_data import dataset, validation_dataset
print("Lade Sentence Transformer Modell...")



# Speicherort des Embedding-Modells (Ordner models im Projekt)
model_path = (Path(__file__).resolve().parent.parent.parent / "models" / "Qwen3-Embedding-0.6B")

# GPU verwenden, wenn verfügbar (mit float16), sonst CPU (float32)
device = "cuda" if torch.cuda.is_available() else "cpu"

if (model_path / "modules.json").exists():
    model = SentenceTransformer(
        str(model_path),
        device=device,
        model_kwargs={
        "low_cpu_mem_usage": True,
        "torch_dtype": torch.float16 if device == "cuda" else torch.float32,
    })
else:
    print("Qwen3-Embedding-0.6B nicht gefunden")
    print("Lade Qwen3-Embedding-0.6B herunter...")
    model = SentenceTransformer(
        "Qwen/Qwen3-Embedding-0.6B",
        device=device,
        model_kwargs={
        "low_cpu_mem_usage": True,
        "torch_dtype": torch.float16 if device == "cuda" else torch.float32,
    }
    )
    model.save(str(model_path))
    print("Qwen3-Embedding-0.6B gespeichert")

print("Verwendetes Gerät:", model.device)
print("Sentence Transformer Modell Geladen")




# Standardwerte des Systems: Threshold und Regularisierungsparameter C der logistischen Regression
STANDARD_THRESHOLD = 0.65
STANDARD_C = 70
model_file = Path(__file__).resolve().parent.parent.parent / "models" / "self_trained" / "mlr_sentence_embeddings"

# Grid Search aktivieren/deaktivieren
# True = C und Threshold per Grid Search bzw. Threshold-Suche bestimmen statt das gespeicherte Modell zu verwenden
do_grid_search = False


def format_query(text):
    """Ergänzt den Satz um die Anweisung («Classify the intent of the following user message»), auf die das Qwen-Modell ausgerichtet wird."""
    # Query für das Embedding-Modell formatieren
    return f"Instruct: Classify the intent of the following user message\nQuery: {text}"

if not Path(model_file).exists() or do_grid_search:
    train_sentences = []
    train_labels = []

    # Trainingsdaten aus Dataset sammeln
    for intent_id, data in dataset.items():
        for sentence in data["examples"]:
            train_sentences.append(format_query(sentence))
            train_labels.append(data["intent"])

    print(f"{len(train_sentences)} Trainingssätze gefunden.")


def sentence_embeddings(input_text, threshold=STANDARD_THRESHOLD):
    """Bestimmt die Befehlsnummer zu einem Satz.

    Parameter:
        input_text: Der Satz.
        threshold: Mindest-Wahrscheinlichkeit der besten Klasse (Standard: STANDARD_THRESHOLD).
    Rückgabe: Tupel (Befehlsnummer, Wahrscheinlichkeit). Liegt die Wahrscheinlichkeit unter dem Threshold,
    wird als Befehlsnummer 0 (unbekannter Befehl) zurückgegeben.
    """
    # Anfrage in Embedding umwandeln und Klassenwahrscheinlichkeiten berechnen
    probabilities = classifier.predict_proba(
        model.encode(
            [format_query(input_text)],
            normalize_embeddings=True
        )
    )[0]

    # Klasse mit der höchsten Wahrscheinlichkeit auswählen
    highest_index = probabilities.argmax()
    confidence = probabilities[highest_index]
    intent = classifier.classes_[highest_index]

    # Bei zu geringer Confidence kein Intent
    if confidence < threshold:
        return 0, confidence

    return int(intent), confidence


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
        model.encode(
            train_sentences,
            show_progress_bar=True,
            normalize_embeddings=True
        ),
        train_labels
    )

    print("Beste Parameter: ", grid.best_params_)
    print("Beste Evaluationsmetrik: ", grid.best_score_)

    classifier = grid.best_estimator_
    validation_labels = []

    # Validierungslabels sammeln
    for item in validation_dataset.values():
        for satz in item["examples"]:
            validation_labels.append(int(item["intent"]))

    thresholds_with_score = []

    # Vorhersagen und Confidences für alle Validierungssätze berechnen
    predictions_with_intents = []

    for item in validation_dataset.values():
        for satz in item["examples"]:
            prediction = sentence_embeddings(satz, 0)
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
    if Path(model_file).exists():
        print("Lade vortrainiertes MLR-Modell..")
        classifier = pickle.load(open(model_file, 'rb'))
        print("MLR-Modell geladen")
    else:
        print("Trainiere neues MLR-Modell")
        # Logistic Regression mit Standardwerten trainieren
        classifier = LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            C=STANDARD_C
        )

        classifier.fit(
            model.encode(
                train_sentences,
                show_progress_bar=True,
                normalize_embeddings=True
            ),
            train_labels
        )
        model_file.parent.mkdir(parents=True, exist_ok=True)
        pickle.dump(classifier, open(model_file, 'wb'))
        print("MLR-Modell trainiert und gespeichert!")




# Alternative: Cross-Validation
# from sklearn.model_selection import cross_val_score
#
# X = model.encode(
#     train_sentences,
#     show_progress_bar=True,
#     normalize_embeddings=True
# )
# y = train_labels
#
# scores = cross_val_score(classifier, X, y, cv=5)
# print(scores, scores.mean())


if __name__ == "__main__":
    print(sentence_embeddings("Spiel ein LIEDD SOFORT"))
