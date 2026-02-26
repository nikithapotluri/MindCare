import React, { useState } from "react";

import "./Predictor.css";

export default function Predictor() {
  // ===== Model-related states =====
  const [gender, setGender] = useState("female");
  const [phq, setPhq] = useState("");
  const [gad, setGad] = useState("");
  const [bmi, setBmi] = useState("");
  const [epw, setEpw] = useState("");
  const [age, setAge] = useState("");

  // ===== UI-only (contextual) states =====
  const [screenTime, setScreenTime] = useState("Low");
  const [socialInteraction, setSocialInteraction] = useState("Moderate");
  const [physicalActivity, setPhysicalActivity] = useState("Moderate");
  const [routineType, setRoutineType] = useState("Regular");

  // ===== App states =====
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const API =
    process.env.REACT_APP_API_URL || "http://localhost:5000/predict_struct";

  const onSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setResult(null);

    if (!phq || !gad || !bmi || !epw || !age) {
      setError("Please fill all required fields.");
      return;
    }

    // 🔒 Payload ONLY includes model-required inputs
    const payload = {
      gender,
      phq_score: parseFloat(phq),
      gad_score: parseFloat(gad),
      bmi: parseFloat(bmi),
      epworth_score: parseFloat(epw),
      age: parseInt(age, 10),
    };

    try {
      setLoading(true);
      const res = await fetch(API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Prediction failed");

      setResult(data.results[0]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Utility to prevent scroll-wheel number change
  const disableWheel = (e) => e.target.blur();

  return (
    <div className="page">
      <div className="container">
        <div className="card">
          <h1 className="title">Psychological Health Prediction System</h1>
          <p className="subtitle">
            Depression • Anxiety • Sleep Disorder
          </p>

          <form className="form-grid" onSubmit={onSubmit}>
            {/* ===== MODEL INPUTS ===== */}
            <div className="form-group">
              <label>Gender</label>
              <select value={gender} onChange={(e) => setGender(e.target.value)}>
                <option value="female">Female</option>
                <option value="male">Male</option>
              </select>
            </div>

            <div className="form-group">
              <label>Age</label>
              <input
                type="number"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                onWheel={disableWheel}
              />
            </div>

            <div className="form-group">
              <label>PHQ Score</label>
              <input
                type="number"
                value={phq}
                onChange={(e) => setPhq(e.target.value)}
                onWheel={disableWheel}
              />
            </div>

            <div className="form-group">
              <label>GAD Score</label>
              <input
                type="number"
                value={gad}
                onChange={(e) => setGad(e.target.value)}
                onWheel={disableWheel}
              />
            </div>

            <div className="form-group">
              <label>BMI</label>
              <input
                type="number"
                value={bmi}
                onChange={(e) => setBmi(e.target.value)}
                onWheel={disableWheel}
              />
            </div>

            <div className="form-group">
              <label>Epworth Score</label>
              <input
                type="number"
                value={epw}
                onChange={(e) => setEpw(e.target.value)}
                onWheel={disableWheel}
              />
            </div>

            {/* ===== UI-ONLY CONTEXTUAL INPUTS ===== */}
        

            <div className="form-group">
              <label>Screen Time Before Bed</label>
              <select
                value={screenTime}
                onChange={(e) => setScreenTime(e.target.value)}
              >
                <option>Low</option>
                <option>Medium</option>
                <option>High</option>
              </select>
            </div>

            <div className="form-group">
              <label>Social Interaction Frequency</label>
              <select
                value={socialInteraction}
                onChange={(e) => setSocialInteraction(e.target.value)}
              >
                <option>Low</option>
                <option>Moderate</option>
                <option>High</option>
              </select>
            </div>

            <div className="form-group">
              <label>Physical Activity Level</label>
              <select
                value={physicalActivity}
                onChange={(e) => setPhysicalActivity(e.target.value)}
              >
                <option>Low</option>
                <option>Moderate</option>
                <option>High</option>
              </select>
            </div>

            <div className="form-group">
              <label>Daily Routine Type</label>
              <select
                value={routineType}
                onChange={(e) => setRoutineType(e.target.value)}
              >
                <option>Regular</option>
                <option>Irregular</option>
              </select>
            </div>


        



            <button className="predict-btn" disabled={loading}>
              {loading ? "Predicting..." : "Predict"}
            </button>
          </form>

          {error && <div className="error">{error}</div>}

          {result && (
            <div className="results">
              <h2>Prediction Results</h2>

              <div className="result-grid">
                <div className="result-card depression">
                  <h3>Depression</h3>
                  <p>{result.depression}</p>
                </div>

                <div className="result-card anxiety">
                  <h3>Anxiety</h3>
                  <p>{result.anxiety}</p>
                </div>

                <div className="result-card sleep">
                  <h3>Sleep Disorder</h3>
                  <p>{result.sleepiness ? "Detected" : "Not Detected"}</p>
                </div>
              </div>

            </div>
          )}
        </div>
      </div>
    </div>
  );
}
