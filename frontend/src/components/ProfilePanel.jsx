export default function ProfilePanel({ session }) {
  if (!session) return null;
  return (
    <div className="card profile-panel">
      <h3>Candidate profile detected from resume</h3>
      <div className="chips-row">
        <strong>Experience level:</strong>
        <span className="chip chip-level">{session.experience_level}</span>
      </div>
      <div className="chips-row">
        <strong>Domains:</strong>
        {session.extracted_domains.map((d) => (
          <span className="chip" key={d}>{d}</span>
        ))}
      </div>
      <div className="chips-row">
        <strong>Skills:</strong>
        {session.extracted_skills.slice(0, 10).map((s) => (
          <span className="chip chip-skill" key={s}>{s}</span>
        ))}
      </div>
    </div>
  );
}
