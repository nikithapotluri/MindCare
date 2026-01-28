import React from "react";
import { NavLink } from "react-router-dom";
import "./Header.css";

export default function Header({ darkMode, setDarkMode }) {
  return (
    <aside className="sidebar">
      <NavLink to="/" className="sidebar-title">
        MindCare
      </NavLink>

      <nav className="sidebar-nav">
        <NavLink to="/predict">Prediction</NavLink>
        <NavLink to="/chatbot">Chatbot</NavLink>
        <NavLink to="/about">About</NavLink>
        {/* 🌙 Dark Mode Toggle */}
        
        <div className="theme-toggle">
          <button onClick={() => setDarkMode(!darkMode)}>
            {darkMode ? "☀️ Light Mode" : "🌙 Dark Mode"}
          </button>
        </div>
      </nav>

      
    </aside>
  );
}
