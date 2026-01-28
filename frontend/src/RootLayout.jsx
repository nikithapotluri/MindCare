import Header from "./components/header/Header";
//import Footer from "./components/footer/Footer";
import { Outlet, useLocation } from "react-router-dom";
import { useState, useEffect } from "react";
import "./RootLayout.css";

function RootLayout() {
  const location = useLocation();
  const isHome = location.pathname === "/";

  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    document.body.className = darkMode ? "dark-mode" : "";
  }, [darkMode]);

  return (
    <div className={`root-layout ${isHome ? "home-layout" : ""}`}>
      {!isHome && (
        <Header darkMode={darkMode} setDarkMode={setDarkMode} />
      )}

      <div className="right-panel">
        <main className={`content ${!isHome ? "with-sidebar" : ""}`}>
          {/* 👇 pass via context */}
          <Outlet context={{ darkMode, setDarkMode }} />
        </main>

        {/*!isHome && <Footer />*/}
      </div>
    </div>
  );
}

export default RootLayout;
