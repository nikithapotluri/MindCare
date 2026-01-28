import "./App.css";
import { createBrowserRouter, RouterProvider } from "react-router-dom";

import RootLayout from "./RootLayout";
import Home from "./components/home/Home";
import Predictor from "./components/predictor/Predictor";
import Chatbot from "./components/chatbot/Chatbot";
import About from "./components/about/About";
// (optional later)
// import Login from "./components/login/Login";

function App() {
  const browserRouter = createBrowserRouter([
    {
      path: "",
      element: <RootLayout />,
      children: [
        {
          path: "",
          element: <Home />,
        },
        {
          path: "predict",
          element: <Predictor />,
        },
        {
          path: "chatbot",
          element: <Chatbot />,
        },
        {
          path: "about",
          element: <About />,
        },
        // {
        //   path: "login",
        //   element: <Login />,
        // },
      ],
    },
  ]);

  return <RouterProvider router={browserRouter} />;
}

export default App;
