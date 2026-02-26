import React from "react";
import { Link, useOutletContext } from "react-router-dom";
import "./Home.css";

export default function Home() {
  const { darkMode, setDarkMode } = useOutletContext();

  return (
    <div className="page">
      {/* 🌙 Dark mode toggle for Home */}
      <div className="home-toggle">
        <button onClick={() => setDarkMode(!darkMode)}>
          {darkMode ? "☀️ Light Mode" : "🌙 Dark Mode"}
        </button>
      </div>

      <div className="home-card">
        <h1>MindCare</h1>
        <p>
          AI-based assessment of <strong>Depression</strong>,{" "}
          <strong>Anxiety</strong> and <strong>Sleep Disorders</strong>.
        </p>

        <div className="home-actions">
          <Link to="/predict">
            <button>Start Assessment</button>
          </Link>


          {/*
          <Link to="/chatbot">
            <button className="secondary">Talk to Chatbot</button>
          </Link>
          */}

          
        </div>
      </div>
    </div>
  );
}
