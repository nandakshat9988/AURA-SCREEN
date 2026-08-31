import React, { useState, useEffect } from "react";
import Header from "./components/Header";
import SetupScreen from "./components/SetupScreen";
import InterviewScreen from "./components/InterviewScreen";
import SummaryScreen from "./components/SummaryScreen";

const API_BASE = import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL}/api` : "/api";

export default function App() {
  const [stage, setStage] = useState("setup");
  const [roles, setRoles] = useState([]);
  const [sessionData, setSessionData] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [lastFeedback, setLastFeedback] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE}/roles`)
      .then((res) => res.json())
      .then((data) => {
        if (data.roles) setRoles(data.roles);
      })
      .catch(() => {
        setRoles([
          {
            id: "ai_ml",
            name: "AI / Machine Learning Engineer",
            source: "Tom Mitchell / Burkov Machine Learning",
            description: "Evaluates inductive bias, neural networks, backpropagation, and foundational attention mechanisms."
          },
          {
            id: "data_science",
            name: "Data Scientist / Applied ML",
            source: "Applied ML, Jason Brownlee & Scikit-Learn",
            description: "Evaluates feature engineering, imputation, class imbalance metrics, bagging, and boosting."
          },
          {
            id: "backend",
            name: "Backend Engineer",
            source: "System Design, Distributed Architectures & Storage",
            description: "Evaluates ACID internals, asynchronous event loops, caching strategies, and API resilience."
          }
        ]);
      });
  }, []);

  const handleStartSession = async ({ role, resumeFile, resumeText }) => {
    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append("role", role);
      if (resumeFile) {
        formData.append("resume_file", resumeFile);
      }
      if (resumeText) {
        formData.append("resume_text", resumeText);
      }

      const res = await fetch(`${API_BASE}/sessions/start`, {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      setSessionData(data);
      setLastFeedback(null);
      setStage("interview");
    } catch (err) {
      alert("Failed to connect to backend server. Make sure the FastAPI server is running on port 8000.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmitAnswer = async (answer) => {
    if (!sessionData) return;
    setIsSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/sessions/${sessionData.session_id}/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer })
      });
      const data = await res.json();

      if (data.is_completed) {
        const sumRes = await fetch(`${API_BASE}/sessions/${sessionData.session_id}/summary`);
        const sumData = await sumRes.json();
        setSummaryData(sumData);
        setStage("summary");
      } else {
        setLastFeedback(data.feedback_on_previous);
        setSessionData((prev) => ({
          ...prev,
          turn_index: data.turn_index,
          question: data.question,
          topic: data.topic,
          difficulty: data.difficulty,
          rag_sources: data.rag_sources
        }));
      }
    } catch (err) {
      alert("Error submitting answer to server.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRestart = () => {
    setSessionData(null);
    setSummaryData(null);
    setLastFeedback(null);
    setStage("setup");
  };

  return (
    <>
      <div className="animated-mesh">
        <div className="glow-orb glow-orb-1"></div>
        <div className="glow-orb glow-orb-2"></div>
      </div>

      <div className="app-container">
        <Header status={stage} role={sessionData?.role} />

        <main>
          {stage === "setup" && (
            <SetupScreen
              roles={roles}
              onStartSession={handleStartSession}
              isLoading={isLoading}
            />
          )}

          {stage === "interview" && sessionData && (
            <InterviewScreen
              sessionData={sessionData}
              onSubmitAnswer={handleSubmitAnswer}
              isSubmitting={isSubmitting}
              lastFeedback={lastFeedback}
            />
          )}

          {stage === "summary" && summaryData && (
            <SummaryScreen
              summaryData={summaryData}
              onRestart={handleRestart}
            />
          )}
        </main>
      </div>
    </>
  );
}
