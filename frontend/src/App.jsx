import { useState } from "react";
import { api } from "./api";
import ResumeUpload from "./components/ResumeUpload";
import Interview from "./components/Interview";
import Summary from "./components/Summary";
import "./App.css";

const STAGE = { UPLOAD: "upload", INTERVIEW: "interview", SUMMARY: "summary" };

export default function App() {
  const [stage, setStage] = useState(STAGE.UPLOAD);
  const [session, setSession] = useState(null);
  const [summary, setSummary] = useState(null);

  const handleStart = async (role, file) => {
    const s = await api.startSession(role, file);
    setSession(s);
    setStage(STAGE.INTERVIEW);
  };

  const handleFinished = (finalSummary) => {
    setSummary(finalSummary);
    setStage(STAGE.SUMMARY);
  };

  const handleRestart = () => {
    setSession(null);
    setSummary(null);
    setStage(STAGE.UPLOAD);
  };

  return (
    <div className="app-shell">
      <header>
        <h1>AI Candidate Screening Interview</h1>
        <p className="muted">RAG-driven, resume-aware, adaptive technical screening</p>
      </header>

      {stage === STAGE.UPLOAD && <ResumeUpload onStart={handleStart} />}
      {stage === STAGE.INTERVIEW && session && (
        <Interview session={session} onFinished={handleFinished} />
      )}
      {stage === STAGE.SUMMARY && summary && (
        <Summary summary={summary} onRestart={handleRestart} />
      )}
    </div>
  );
}
