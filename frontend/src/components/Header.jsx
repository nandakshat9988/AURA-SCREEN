import React from "react";
import { Sparkles, Database, BrainCircuit, Activity } from "lucide-react";

export default function Header({ status = "ready", role = null }) {
  return (
    <header className="navbar">
      <div className="brand-wrapper">
        <div className="brand-icon">
          <BrainCircuit size={24} />
        </div>
        <div>
          <h1 className="brand-title">AURA SCREEN</h1>
          <p className="brand-subtitle">AI-Powered Role-Based Screening</p>
        </div>
      </div>

      <div className="nav-badges">
        <div className="badge-tag badge-opus">
          <Sparkles size={14} />
          <span>Claude Opus LLM</span>
        </div>
        <div className="badge-tag badge-mongo">
          <Database size={14} />
          <span>MongoDB Grounded</span>
        </div>
        <div className="badge-tag">
          <span className="status-dot"></span>
          <span>{status.toUpperCase()}</span>
        </div>
      </div>
    </header>
  );
}
