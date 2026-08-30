import { useState, useEffect } from "react";
import { api } from "../api";

export default function ResumeUpload({ onStart }) {
  const [roles, setRoles] = useState([]);
  const [role, setRole] = useState("");
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.roles().then((r) => {
      setRoles(r);
      if (r.length) setRole(r[0].key);
    }).catch((e) => setError(e.message));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file || !role) return;
    setLoading(true);
    setError(null);
    try {
      await onStart(role, file);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2>Start your screening interview</h2>
      <p className="muted">
        Upload your resume and pick a target role. Questions are generated
        live from your resume and a role-specific knowledge base.
      </p>
      <form onSubmit={handleSubmit}>
        <label className="field">
          <span>Target role</span>
          <select value={role} onChange={(e) => setRole(e.target.value)}>
            {roles.map((r) => (
              <option key={r.key} value={r.key}>{r.label}</option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Resume (PDF)</span>
          <input
            type="file"
            accept=".pdf,.txt"
            onChange={(e) => setFile(e.target.files[0])}
          />
        </label>

        {error && <div className="error">{error}</div>}

        <button type="submit" disabled={loading || !file}>
          {loading ? "Analyzing resume..." : "Begin Interview"}
        </button>
      </form>
    </div>
  );
}
