import React from "react";
import "./About.css";

export default function About() {
  return (
    <div className="page">
      <div className="about-card">
        <h2>About This Project</h2>
        <p>
          This system uses Machine Learning models to assist in identifying
          psychological health conditions such as depression, anxiety, and sleep
          disorders.
        </p>
        <p>
          The application is designed for educational purposes and does not
          replace professional medical advice.
        </p>
      </div>
    </div>
  );
}
