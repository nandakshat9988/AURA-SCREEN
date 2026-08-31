import React, { useState } from "react";
import { Send, Bot, BookMarked, CheckCircle, Clock, Loader2, Sparkles, Award } from "lucide-react";

export default function InterviewScreen({
  sessionData,
  onSubmitAnswer,
  isSubmitting,
  lastFeedback
}) {
  const [candidateAnswer, setCandidateAnswer] = useState("");

  const handleSend = (e) => {
    e.preventDefault();
    if (!candidateAnswer.trim() || isSubmitting) return;
    onSubmitAnswer(candidateAnswer);
    setCandidateAnswer("");
  };

  const currentTurn = sessionData.turn_index;
  const totalTurns = sessionData.total_turns;

  return (
    <div className="interview-layout">
      <div className="interviewer-panel">
        <div className="avatar-container">
          <div className="avatar-orb">
            <Bot size={44} color="#ffffff" />
          </div>
          <h3 className="avatar-name">Claude Opus</h3>
          <p className="avatar-role">Senior AI Technical Interviewer</p>
          <div style={{ marginTop: 14, display: "flex", gap: 6, flexWrap: "wrap", justifyContent: "center" }}>
            {sessionData.candidate?.skills?.slice(0, 4).map((skill, i) => (
              <span key={i} className="badge-tag" style={{ fontSize: 11, padding: "4px 8px" }}>
                {skill}
              </span>
            ))}
          </div>
        </div>

        <div className="rag-drawer">
          <div className="rag-header">
            <BookMarked size={14} />
            <span>Retrieved RAG Textbook Context</span>
          </div>
          {sessionData.rag_sources && sessionData.rag_sources.length > 0 ? (
            <div className="rag-quote">
              <strong style={{ color: "#38bdf8", display: "block", marginBottom: 4 }}>
                {sessionData.rag_sources[0]?.source}
              </strong>
              "{sessionData.rag_sources[0]?.text?.slice(0, 260)}..."
            </div>
          ) : (
            <p style={{ fontSize: 12, color: "#64748b" }}>Grounding against role textbook repository...</p>
          )}
        </div>
      </div>

      <div className="question-stage">
        <div className="turn-tracker">
          <div className="turn-pill">
            <Clock size={15} />
            <span>Question {currentTurn} of {totalTurns}</span>
          </div>
          <div className="badge-tag" style={{ color: "#c084fc", borderColor: "rgba(192, 132, 252, 0.4)" }}>
            <Award size={14} />
            <span>Difficulty: {sessionData.difficulty || "Advanced"}</span>
          </div>
        </div>

        {lastFeedback && (
          <div className="feedback-flash">
            <div className="feedback-title">
              <CheckCircle size={16} />
              <span>Feedback on Question {currentTurn - 1} (Score: {lastFeedback.score}/100)</span>
            </div>
            <p className="feedback-body">{lastFeedback.feedback}</p>
          </div>
        )}

        <div className="question-bubble">
          <span className="question-topic-badge">{sessionData.topic || "Core Architecture"}</span>
          <p className="question-text">{sessionData.question}</p>
        </div>

        <form onSubmit={handleSend} className="glass-card" style={{ padding: 20 }}>
          <textarea
            className="custom-textarea"
            style={{ minHeight: 140, marginBottom: 14 }}
            placeholder="Type your technical answer here. Reference specific concepts, mathematical formulations, or design patterns where applicable..."
            value={candidateAnswer}
            onChange={(e) => setCandidateAnswer(e.target.value)}
            disabled={isSubmitting}
          />

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: 12, color: "#64748b" }}>
              {candidateAnswer.trim().split(/\s+/).filter(Boolean).length} words
            </span>

            <button
              type="submit"
              className="action-btn-primary"
              style={{ width: "auto", margin: 0, padding: "12px 28px" }}
              disabled={!candidateAnswer.trim() || isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Loader2 size={18} className="spin-animation" />
                  <span>Evaluating Response & Grounding Next...</span>
                </>
              ) : (
                <>
                  <span>Submit Answer</span>
                  <Send size={18} />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
