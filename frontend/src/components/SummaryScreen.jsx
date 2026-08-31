import React, { useEffect } from "react";
import confetti from "canvas-confetti";
import { CheckCircle2, AlertTriangle, RotateCcw, Award, Zap, BookOpen, Target, Sparkles } from "lucide-react";

export default function SummaryScreen({ summaryData, onRestart }) {
  const evalData = summaryData.evaluation || {};
  const overall = evalData.overall_score || 85;

  useEffect(() => {
    if (overall >= 75) {
      confetti({
        particleCount: 80,
        spread: 70,
        origin: { y: 0.6 }
      });
    }
  }, [overall]);

  const metrics = [
    { label: "Technical Depth", value: evalData.technical_depth || 88 },
    { label: "Conceptual Grounding", value: evalData.conceptual_grounding || 84 },
    { label: "Problem Solving", value: evalData.problem_solving || 82 },
    { label: "Communication & Clarity", value: evalData.communication || 90 }
  ];

  return (
    <div className="summary-container">
      <div className="glass-card">
        <div className="score-overview">
          <div className="circular-score" style={{ "--score-pct": overall }}>
            <div className="circular-score-inner">
              <span className="score-number">{overall}%</span>
              <span className="score-tag">Readiness</span>
            </div>
          </div>

          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
              <span className="badge-tag" style={{ background: "rgba(16, 185, 129, 0.15)", borderColor: "#10b981", color: "#6ee7b7", fontSize: 14 }}>
                <Award size={16} />
                <span>Recommendation: {evalData.recommendation || "Hire"}</span>
              </span>
            </div>
            <h2 style={{ fontSize: 26, color: "#fff", marginBottom: 10 }}>Technical Screening Report</h2>
            <p style={{ color: "#94a3b8", lineHeight: 1.6, fontSize: 14 }}>
              {evalData.executive_summary}
            </p>
          </div>
        </div>
      </div>

      <div className="glass-card">
        <div className="section-label">
          <Zap size={16} />
          <span>Core Competency Breakdown</span>
        </div>
        <div className="metrics-bars">
          {metrics.map((m, idx) => (
            <div key={idx} className="metric-row">
              <div className="metric-meta">
                <span style={{ color: "#e2e8f0" }}>{m.label}</span>
                <span style={{ color: "#38bdf8" }}>{m.value}%</span>
              </div>
              <div className="metric-progress">
                <div className="metric-fill" style={{ width: `${m.value}%` }}></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="insights-grid">
        <div className="insight-card">
          <div className="insight-heading" style={{ color: "#34d399" }}>
            <CheckCircle2 size={18} />
            <span>Demonstrated Strengths</span>
          </div>
          <ul className="insight-list">
            {(evalData.top_strengths || []).map((s, i) => (
              <li key={i} className="insight-item">
                <span style={{ color: "#10b981" }}>•</span>
                <span>{s}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="insight-card">
          <div className="insight-heading" style={{ color: "#fbbf24" }}>
            <AlertTriangle size={18} />
            <span>Growth & Target Areas</span>
          </div>
          <ul className="insight-list">
            {(evalData.growth_areas || []).map((g, i) => (
              <li key={i} className="insight-item">
                <span style={{ color: "#f59e0b" }}>•</span>
                <span>{g}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="glass-card">
        <div className="section-label">
          <BookOpen size={16} />
          <span>Interview Transcript & Grounded RAG Traceability</span>
        </div>
        <div className="audit-table">
          {(summaryData.turns || []).map((turn, i) => (
            <div key={i} className="audit-row">
              <div className="audit-header">
                <span className="badge-tag" style={{ fontSize: 11 }}>Question #{turn.turn_index}</span>
                <span style={{ fontSize: 12, color: "#38bdf8", fontWeight: 600 }}>
                  Score: {turn.feedback?.score || 80}/100
                </span>
              </div>
              <div className="audit-q">{turn.question}</div>
              <div className="audit-a">"{turn.candidate_answer || "No response recorded"}"</div>
              {turn.rag_chunks && turn.rag_chunks.length > 0 && (
                <div style={{ marginTop: 8, fontSize: 11, color: "#64748b" }}>
                  <strong style={{ color: "#94a3b8" }}>Grounded Source: </strong>
                  {turn.rag_chunks[0]?.source}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <button className="action-btn-primary" onClick={onRestart}>
        <RotateCcw size={18} />
        <span>Screen Another Candidate</span>
      </button>
    </div>
  );
}
