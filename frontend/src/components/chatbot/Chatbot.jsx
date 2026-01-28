import React, { useState } from "react";
import "./Chatbot.css";

export default function Chatbot() {
  const [messages, setMessages] = useState([
    {
      sender: "bot",
      text: "Hello 👋 I’m MindCare Bot. How are you feeling today?",
    },
  ]);

  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);

  const CHAT_API = "http://127.0.0.1:5000/chat";

  /* =========================
     RESET CHAT
     ========================= */
  const resetChat = () => {
    setMessages([
      {
        sender: "bot",
        text: "Hello 👋 I’m MindCare Bot. How are you feeling today?",
      },
    ]);
    setTyping(false);
  };

  /* =========================
     SEND MESSAGE (BACKEND NLP)
     ========================= */
  const sendUserMessage = async (text) => {
    if (!text.trim()) return;

    // Show user message
    setMessages((prev) => [...prev, { sender: "user", text }]);
    setTyping(true);

    try {
      const res = await fetch(CHAT_API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });

      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: data.reply },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text:
            "Sorry, I’m having trouble responding right now. Please try again later.",
        },
      ]);
    } finally {
      setTyping(false);
    }
  };

  const sendMessage = () => {
    sendUserMessage(input);
    setInput("");
  };

  return (
    <div className="page">
      <div className="chat-card">
        <h2>MindCare Chatbot</h2>

        <button className="reset-btn" onClick={resetChat}>
          🔄 Reset Chat
        </button>

        <div className="chat-window">
          {messages.map((m, i) => (
            <div key={i} className={`msg ${m.sender}`}>
              {m.text}
            </div>
          ))}

          {typing && (
            <div className="msg bot typing">
              MindCare is typing<span className="dots">...</span>
            </div>
          )}
        </div>

        {/* Optional quick suggestions */}
        <div className="quick-replies">
          <button onClick={() => sendUserMessage("I feel anxious")}>
            I feel anxious
          </button>
          <button onClick={() => sendUserMessage("I feel sad")}>
            I feel sad
          </button>
          <button onClick={() => sendUserMessage("I can’t sleep")}>
            Sleep issues
          </button>
          <button onClick={() => sendUserMessage("I want to take the assessment")}>
            Take assessment
          </button>
        </div>

        <div className="chat-input">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          />
          <button onClick={sendMessage}>Send</button>
        </div>
      </div>
    </div>
  );
}
