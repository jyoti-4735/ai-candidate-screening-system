export default function Summary({ summary, onRestart }) {
  return (
    <div className="card">
      <h2>Interview Summary</h2>
      <p className="muted">Role: {summary.role} - Detected level: {summary.candidate_experience_level}</p>

      <div className="score-hero">
        <div className="score-number">{Math.round(summary.average_score * 100)}%</div>
        <div>
          <div>Average score across {summary.questions_answered}/{summary.questions_asked} questions</div>
          <div className="muted small">Generation mode: {summary.generation_mode}</div>
        </div>
      </div>

      <div className="two-col">
        <div>
          <h3>Strengths</h3>
          {summary.strengths.length ? (
            <ul>{summary.strengths.map((s) => <li key={s}>{s}</li>)}</ul>
          ) : <p className="muted">None reached the strength threshold this round.</p>}
        </div>
        <div>
          <h3>Growth areas</h3>
          {summary.growth_areas.length ? (
            <ul>{summary.growth_areas.map((s) => <li key={s}>{s}</li>)}</ul>
          ) : <p className="muted">No major gaps flagged.</p>}
        </div>
      </div>

      <h3>Question-by-question breakdown</h3>
      <table className="breakdown-table">
        <thead>
          <tr><th>Topic</th><th>Difficulty</th><th>Score</th><th>Feedback</th></tr>
        </thead>
        <tbody>
          {summary.topic_breakdown.map((t, i) => (
            <tr key={i}>
              <td>{t.topic}</td>
              <td>{t.difficulty}</td>
              <td>{t.score}</td>
              <td>{t.feedback}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <button onClick={onRestart}>Start another interview</button>
    </div>
  );
}
