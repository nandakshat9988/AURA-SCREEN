import React, { useState } from "react";
import { Upload, FileText, CheckCircle2, ArrowRight, BookOpen, UserCheck, Loader2 } from "lucide-react";

export default function SetupScreen({ roles, onStartSession, isLoading }) {
  const [selectedRole, setSelectedRole] = useState(roles[0]?.name || "AI / Machine Learning Engineer");
  const [resumeFile, setResumeFile] = useState(null);
  const [resumeText, setResumeText] = useState("");

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setResumeFile(e.target.files[0]);
    }
  };

  const handleStart = () => {
    onStartSession({
      role: selectedRole,
      resumeFile,
      resumeText
    });
  };

  return (
    <div className="setup-container">
      <div className="hero-banner">
        <h2 className="hero-title">Technical Candidate Screening</h2>
        <p className="hero-desc">
          Dynamically grounded interview simulation powered by Claude Opus and role-specific textbooks.
          Upload your resume and select a target track to begin your technical evaluation.
        </p>
      </div>

      <div className="glass-card setup-grid">
        <div className="setup-col">
          <div className="section-label">
            <BookOpen size={16} />
            <span>Select Target Role</span>
          </div>

          <div className="roles-container">
            {roles.map((r) => {
              const isSelected = selectedRole === r.name;
              return (
                <div
                  key={r.id}
                  className={`role-card ${isSelected ? "active" : ""}`}
                  onClick={() => setSelectedRole(r.name)}
                >
                  <div className="role-header">
                    <span className="role-title">{r.name}</span>
                    {isSelected && <CheckCircle2 size={18} color="#06b6d4" />}
                  </div>
                  <span className="role-source">Corpus: {r.source}</span>
                  <p className="role-desc">{r.description}</p>
                </div>
              );
            })}
          </div>
        </div>

        <div className="setup-col">
          <div className="section-label">
            <UserCheck size={16} />
            <span>Candidate Resume Data</span>
          </div>

          <label className={`upload-zone ${resumeFile ? "has-file" : ""}`}>
            <input
              type="file"
              accept=".pdf,.txt,.doc"
              onChange={handleFileChange}
              style={{ display: "none" }}
            />
            <div className="upload-icon-circle">
              {resumeFile ? <CheckCircle2 size={28} color="#10b981" /> : <Upload size={28} />}
            </div>
            <div>
              <p style={{ fontWeight: 600, color: "#fff", fontSize: 14 }}>
                {resumeFile ? resumeFile.name : "Upload Resume (PDF or TXT)"}
              </p>
              <p style={{ color: "#94a3b8", fontSize: 12 }}>
                {resumeFile ? `${(resumeFile.size / 1024).toFixed(1)} KB uploaded` : "Drag and drop or click to browse"}
              </p>
            </div>
          </label>

          <div className="or-divider">OR PASTE RESUME HIGHLIGHTS</div>

          <textarea
            className="custom-textarea"
            placeholder="Paste raw resume text, technical skills, or project experience here..."
            value={resumeText}
            onChange={(e) => setResumeText(e.target.value)}
          />

          <button
            className="action-btn-primary"
            onClick={handleStart}
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 size={20} className="spin-animation" />
                <span>Ingesting Knowledge & Parsing Resume...</span>
              </>
            ) : (
              <>
                <span>Initialize Technical Interview</span>
                <ArrowRight size={20} />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
