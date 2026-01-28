# backend/app.py
import os

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import joblib
import numpy as np
import pandas as pd

from sentence_transformers import SentenceTransformer, util


# React build folder (for production; in dev you use npm start on port 3000)
app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), "..", "frontend", "build"),
    static_url_path="/",
)
nlp_model = SentenceTransformer('all-MiniLM-L6-v2')
CORS(app)

# ---- ARTIFACT LOADING ----

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "..", "backend_artifacts")
print("ARTIFACTS_DIR:", ARTIFACTS_DIR)


def safe_load(path, name=""):
    """
    Try to load a joblib artifact.
    If loading fails (e.g. version mismatch), print a warning and return None.
    """
    if os.path.exists(path):
        try:
            obj = joblib.load(path)
            print(f"Loaded {name or os.path.basename(path)} from {path}")
            return obj
        except Exception as e:
            print(
                f"Warning: could not load {name or os.path.basename(path)} "
                f"from {path}: {e}"
            )
            return None
    else:
        print(f"{name or os.path.basename(path)} not found at {path}")
    return None


# Load artifacts
ct = safe_load(os.path.join(ARTIFACTS_DIR, "ct.joblib"), "ct")
scaler = safe_load(os.path.join(ARTIFACTS_DIR, "scaler.joblib"), "scaler")

svm_depression = safe_load(
    os.path.join(ARTIFACTS_DIR, "svm_depression.joblib"), "svm_depression"
)
svm_anxiety = safe_load(
    os.path.join(ARTIFACTS_DIR, "svm_anxiety.joblib"), "svm_anxiety"
)
svm_sleep = safe_load(os.path.join(ARTIFACTS_DIR, "svm_sleep.joblib"), "svm_sleep")

le_depression = safe_load(
    os.path.join(ARTIFACTS_DIR, "le_depression.joblib"), "le_depression"
)
le_anxiety = safe_load(
    os.path.join(ARTIFACTS_DIR, "le_anxiety.joblib"), "le_anxiety"
)
le_sleep = safe_load(os.path.join(ARTIFACTS_DIR, "le_sleep.joblib"), "le_sleep")

print("ct:", bool(ct))
print("scaler:", bool(scaler))
print("svm_depression:", bool(svm_depression))
print("svm_anxiety:", bool(svm_anxiety))
print("svm_sleep:", bool(svm_sleep))
print("le_depression:", bool(le_depression))
print("le_anxiety:", bool(le_anxiety))
print("le_sleep:", bool(le_sleep))

# Infer expected number of features from any of the models
EXPECTED_FEATURES = None
for m in (svm_depression, svm_anxiety, svm_sleep):
    if m is not None and hasattr(m, "n_features_in_"):
        EXPECTED_FEATURES = m.n_features_in_
        break
print("EXPECTED_FEATURES:", EXPECTED_FEATURES)


# ---- HELPER FUNCTIONS ----

def build_vector_from_json(d: dict) -> np.ndarray:
    """
    Build the SAME feature vector used during training.

    Training code:
      numerical_columns = ['phq_score', 'gad_score', 'bmi', 'epworth_score', 'age']
      categorical_columns = ['gender']
      ct = ColumnTransformer(
          transformers=[('encoder', OneHotEncoder(), categorical_columns)],
          remainder='passthrough'
      )
      x_encoded = ct.fit_transform(x)

    Here we support two cases:
      1) If ct loaded: use ct.transform on a DataFrame row.
      2) If ct failed to load: manual encoding [female, male, phq, gad, bmi, epw, age].
    """
    required = ["gender", "phq_score", "gad_score", "bmi", "epworth_score", "age"]
    for k in required:
        if k not in d:
            raise ValueError(f"Missing field: {k}")

    gender_raw = str(d["gender"]).strip()

    if ct is not None:
        # Use the original ColumnTransformer
        row = pd.DataFrame(
            [
                {
                    "phq_score": float(d["phq_score"]),
                    "gad_score": float(d["gad_score"]),
                    "bmi": float(d["bmi"]),
                    "epworth_score": float(d["epworth_score"]),
                    "age": int(d["age"]),
                    "gender": gender_raw,
                }
            ]
        )
        X_enc = ct.transform(row)  # shape (1, n_features)
        return np.array(X_enc).reshape(1, -1)

    # Fallback: manual encoding identical to your predict_severity() logic:
    # gender_encoded = [1, 0] if female else [0, 1]
    gender = gender_raw.lower()
    if gender == "female":
        gender_encoded = [1, 0]
    else:
        gender_encoded = [0, 1]

    phq = float(d["phq_score"])
    gad = float(d["gad_score"])
    bmi = float(d["bmi"])
    epw = float(d["epworth_score"])
    age = int(d["age"])

    vec = gender_encoded + [phq, gad, bmi, epw, age]
    return np.array(vec).reshape(1, -1)


def decode_with_encoder(pred_list, encoder):
    """Use LabelEncoder to get string labels; if encoder missing, return raw ints."""
    if encoder is None:
        return pred_list
    try:
        return [encoder.inverse_transform([p])[0] for p in pred_list]
    except Exception:
        return pred_list


# ---- ROUTES ----

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/predict", methods=["POST"])
def predict_vector():
    """
    Legacy route:
      Request JSON: { "features": [f1, f2, ..., fN] }
    Sends the raw feature vector directly (must match EXPECTED_FEATURES length).
    """
    if not (svm_depression and svm_anxiety and svm_sleep):
        return jsonify({"error": "Models not loaded"}), 500

    data = request.get_json(force=True)
    if not data or "features" not in data:
        return jsonify({"error": "Missing 'features' field"}), 400

    X = np.array(data["features"])
    if X.ndim == 1:
        X = X.reshape(1, -1)

    if EXPECTED_FEATURES is not None and X.shape[1] != EXPECTED_FEATURES:
        return (
            jsonify(
                {
                    "error": f"Expected {EXPECTED_FEATURES} features, got {X.shape[1]}"
                }
            ),
            400,
        )

    try:
        X_proc = scaler.transform(X) if scaler is not None else X
    except Exception as e:
        return jsonify({"error": f"Scaler transform failed: {e}"}), 400

    try:
        p_dep = svm_depression.predict(X_proc).tolist()
        p_anx = svm_anxiety.predict(X_proc).tolist()
        p_slp = svm_sleep.predict(X_proc).tolist()
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {e}"}), 500

    dep_labels = decode_with_encoder(p_dep, le_depression)
    anx_labels = decode_with_encoder(p_anx, le_anxiety)
    slp_labels = decode_with_encoder(p_slp, le_sleep)

    results = []
    for i in range(len(dep_labels)):
        results.append(
            {
                "depression": dep_labels[i],
                "anxiety": anx_labels[i],
                "sleepiness": slp_labels[i],
            }
        )
    return jsonify({"results": results}), 200


@app.route("/predict_struct", methods=["POST"])
def predict_struct():
    """
    Recommended route:

    Single instance:
    {
      "gender": "female",
      "phq_score": 10,
      "gad_score": 8,
      "bmi": 22.5,
      "epworth_score": 6,
      "age": 30
    }

    Batch:
    {
      "instances": [
        { ... },
        { ... }
      ]
    }
    """
    if not (svm_depression and svm_anxiety and svm_sleep):
        return jsonify({"error": "Models not loaded"}), 500

    data = request.get_json(force=True)

    try:
        if "instances" in data:
            rows = [build_vector_from_json(inst) for inst in data["instances"]]
            X = np.vstack(rows)
        else:
            X = build_vector_from_json(data)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"Invalid input: {e}"}), 400

    try:
        X_proc = scaler.transform(X) if scaler is not None else X
    except Exception as e:
        return jsonify({"error": f"Scaler transform failed: {e}"}), 400

    try:
        p_dep = svm_depression.predict(X_proc).tolist()
        p_anx = svm_anxiety.predict(X_proc).tolist()
        p_slp = svm_sleep.predict(X_proc).tolist()
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {e}"}), 500

    dep_labels = decode_with_encoder(p_dep, le_depression)
    anx_labels = decode_with_encoder(p_anx, le_anxiety)
    slp_labels = decode_with_encoder(p_slp, le_sleep)

    results = []
    for i in range(len(dep_labels)):
        results.append(
            {
                "depression": dep_labels[i],
                "anxiety": anx_labels[i],
                "sleepiness": slp_labels[i],
            }
        )
    return jsonify({"results": results}), 200


# ---- REACT STATIC BUILD (for production) ----

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    """
    Serve React build if present.
    In development (npm start on port 3000), this is not used.
    """
    if app.static_folder and os.path.exists(
        os.path.join(app.static_folder, path)
    ) and path != "":
        return send_from_directory(app.static_folder, path)

    index_path = os.path.join(app.static_folder, "index.html")
    if app.static_folder and os.path.exists(index_path):
        return send_from_directory(app.static_folder, "index.html")

    return jsonify({"message": "Flask server is running. React build not found."})







#CHATBOT LOGIC

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    message = data.get("message", "").lower().strip()

    # ==========================
    # 🚨 EXPLICIT CRISIS (HIGHEST PRIORITY)
    # ==========================
    explicit_crisis = [
        "suicide",
        "kill myself",
        "end my life",
        "self harm"
    ]

    if any(word in message for word in explicit_crisis):
        return jsonify({
            "reply": (
                "I’m really sorry that you’re feeling this way 💙\n\n"
                "You are not alone, and help is available right now.\n\n"
                "📞 India Helpline: 9152987821 (Kiran – 24/7)\n"
                "🌍 https://findahelpline.com\n\n"
                "Please consider reaching out to a trusted person or a mental health professional immediately."
            )
        }), 200

    # ==========================
    # 🚨 SOFT / IMPLICIT CRISIS
    # ==========================
    soft_crisis = [
        "ending it",
        "don’t want to exist",
        "dont want to exist",
        "wish i could disappear",
        "tired of living",
        "can’t go on",
        "cant go on"
    ]

    if any(phrase in message for phrase in soft_crisis):
        return jsonify({
            "reply": (
                "I’m really glad you told me this 💙\n\n"
                "What you’re feeling matters, and support is available.\n\n"
                "📞 India Helpline: 9152987821 (Kiran – 24/7)\n"
                "🌍 https://findahelpline.com\n\n"
                "If possible, please reach out to someone you trust or a mental health professional."
            )
        }), 200

    # ==========================
    # 🧠 HOPELESSNESS (PRE-CRISIS)
    # ==========================
    hopeless_phrases = [
        "no point",
        "don’t see the point",
        "dont see the point",
        "nothing will change",
        "giving up",
        "tired of everything",
        "feel pointless"
    ]

    if any(phrase in message for phrase in hopeless_phrases):
        return jsonify({
            "reply": (
                "I’m really sorry you’re feeling this way 💙\n\n"
                "Feeling hopeless can be incredibly heavy, but it doesn’t mean things can’t improve.\n\n"
                "You don’t have to go through this alone. Would you like to talk about what’s been weighing on you, "
                "or would you prefer coping strategies?"
            )
        }), 200

    # ==========================
    # 🧠 CONTEXTUAL YES HANDLING
    # ==========================
    if message in ["yes", "yeah", "ok", "okay", "sure"]:
        return jsonify({
            "reply": (
                "Thank you for letting me know 🌱\n\n"
                "Here are a few gentle coping strategies you can try:\n\n"
                "• Slow breathing (inhale 4 seconds, exhale 6 seconds)\n"
                "• Maintain a simple daily routine\n"
                "• Reduce screen time before sleep\n"
                "• Talk to someone you trust\n\n"
                "If things feel overwhelming, professional support can really help."
            )
        }), 200

    # ==========================
    # 📊 ASSESSMENT RESULT PARSING
    # ==========================
    if "depression" in message and (
        "mild" in message or "moderate" in message or "severe" in message
    ):

        response = "Thank you for sharing your assessment results 🌱\n\n"

        if "depression severe" in message:
            response += (
                "🔴 **Severe Depression Detected**\n"
                "This can feel overwhelming, and you deserve support.\n"
                "Please consider reaching out to a mental health professional or someone you trust.\n\n"
            )
        elif "depression moderate" in message:
            response += (
                "🟠 **Moderate Depression Detected**\n"
                "This may affect daily functioning, and support can be helpful.\n\n"
            )
        elif "depression mild" in message:
            response += (
                "🟢 **Mild Depression Detected**\n"
                "Awareness and small self-care steps can make a difference.\n\n"
            )

        if "anxiety severe" in message:
            response += "🔴 **Severe Anxiety Detected**.\n\n"
        elif "anxiety moderate" in message:
            response += "🟠 **Moderate Anxiety Detected**.\n\n"
        elif "anxiety mild" in message:
            response += "🟢 **Mild Anxiety Detected**.\n\n"
        elif "no anxiety" in message:
            response += "✅ Anxiety does not appear to be a major concern currently.\n\n"

        if "sleep disorder not detected" in message:
            response += "🌙 Sleep disorder not detected.\n\n"

        response += (
            "⚠️ This assessment is for awareness, not diagnosis.\n"
            "Would you like coping strategies or guidance on next steps?"
        )

        return jsonify({ "reply": response }), 200

    # ==========================
    # 🧠 NLP INTENT DETECTION
    # ==========================
    intent_examples = {
        "anxiety": [
            "i feel anxious",
            "i am worried",
            "i feel overwhelmed",
            "i feel restless"
        ],
        "depression": [
            "i feel sad",
            "i feel hopeless",
            "i feel empty",
            "nothing feels meaningful"
        ],
        "sleep": [
            "i can’t sleep",
            "i have insomnia",
            "i wake up frequently",
            "my mind won’t calm down at night"
        ],
        "assessment": [
            "i want to take the assessment",
            "check my mental health",
            "i want to do the test"
        ]
    }

    user_embedding = nlp_model.encode(message, convert_to_tensor=True)

    scores = {}
    for intent, examples in intent_examples.items():
        example_embeddings = nlp_model.encode(examples, convert_to_tensor=True)
        similarity = util.cos_sim(user_embedding, example_embeddings)
        scores[intent] = float(similarity.max())

    best_intent = max(scores, key=scores.get)
    best_score = scores[best_intent]

    if best_score >= 0.5:
        if best_intent == "anxiety":
            return jsonify({
                "reply": (
                    "It sounds like anxiety may be affecting you 💙\n\n"
                    "Would you like to talk about what’s causing this, or take a short assessment?"
                )
            }), 200

        if best_intent == "depression":
            return jsonify({
                "reply": (
                    "I’m really sorry you’re feeling this way 💙\n\n"
                    "Would you like to talk more about it or take an assessment?"
                )
            }), 200

        if best_intent == "sleep":
            return jsonify({
                "reply": (
                    "Sleep difficulties can strongly affect well-being 🌙\n\n"
                    "Would you like tips or an assessment?"
                )
            }), 200

        if best_intent == "assessment":
            return jsonify({
                "reply": (
                    "You can take the psychological assessment from the **Prediction** section.\n\n"
                    "It helps understand depression, anxiety, and sleep patterns."
                )
            }), 200

    # ==========================
    # 🔄 FINAL FALLBACK
    # ==========================
    return jsonify({
        "reply": "I’m here to listen 🌱 You can share anything you feel comfortable with."
    }), 200







if __name__ == "__main__":
    # Debug server for local development
    app.run(host="0.0.0.0", port=5000, debug=True)