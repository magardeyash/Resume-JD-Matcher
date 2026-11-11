import React, { useEffect, useState } from 'react';
import { CheckCircle2, AlertTriangle, HelpCircle, Check, ArrowLeft, History } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Results({ analysisId, onNavigate }) {
  const { token } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [progressOffset, setProgressOffset] = useState(440); // 2 * PI * 70

  useEffect(() => {
    async function fetchResult() {
      try {
        setLoading(true);
        const headers = {};
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
        const res = await fetch(`/api/analyses/${analysisId}`, { headers });
        if (!res.ok) {
          let detail = 'Failed to fetch analysis.';
          if (res.status === 404) detail = 'Analysis not found.';
          if (res.status === 403) detail = 'You do not have permission to view this private analysis.';
          throw new Error(detail);
        }
        const json = await res.json();
        setData(json);

        // Animate circular score gauge
        const radius = 70;
        const circumference = 2 * Math.PI * radius; // ~440
        const targetOffset = circumference - (json.compatibility_score / 100) * circumference;
        setTimeout(() => {
          setProgressOffset(targetOffset);
        }, 150);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    if (analysisId) {
      fetchResult();
    }
  }, [analysisId]);

  if (loading) {
    return (
      <main className="container" style={{ textAlign: 'center', padding: '5rem 1rem' }}>
        <div
          className="spinner"
          style={{ width: 40, height: 40, borderColor: 'rgba(79, 70, 229, 0.2)', borderTopColor: 'var(--primary)' }}
        ></div>
        <p style={{ marginTop: '1.2rem', color: 'var(--text-muted)', fontWeight: 500 }}>
          Loading analysis results...
        </p>
      </main>
    );
  }

  if (error || !data) {
    return (
      <main className="container">
        <div className="alert alert-danger" style={{ display: 'block' }}>
          {error || 'Unable to display results.'}
        </div>
        <button onClick={() => onNavigate('/')} className="btn btn-secondary">
          <ArrowLeft style={{ width: 18, height: 18 }} /> Back to Dashboard
        </button>
      </main>
    );
  }

  const dateStr = new Date(data.created_at).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  const breakdownRows = [
    {
      name: 'Semantic Similarity',
      weight: '30%',
      score: data.semantic_score,
      contribution: (data.semantic_score * 0.3).toFixed(1),
    },
    {
      name: 'Required Skill Coverage',
      weight: '40%',
      score: data.required_skills_score,
      contribution: (data.required_skills_score * 0.4).toFixed(1),
    },
    {
      name: 'Experience Relevance',
      weight: '20%',
      score: data.experience_score,
      contribution: (data.experience_score * 0.2).toFixed(1),
    },
    {
      name: 'Preferred Skill Coverage',
      weight: '10%',
      score: data.preferred_skills_score,
      contribution: (data.preferred_skills_score * 0.1).toFixed(1),
    },
  ];

  return (
    <main className="container">
      <div className="page-header" style={{ textAlign: 'left', marginBottom: '1.5rem' }}>
        <h1 className="page-title">{data.job_title || 'Position Match Analysis'}</h1>
        <p className="page-subtitle">
          Resume: <strong>{data.resume_filename}</strong> • Analyzed on {dateStr}
        </p>
      </div>

      {/* Hero Score Card */}
      <section className="card">
        <div className="score-hero">
          <div className="score-chart-container">
            <svg viewBox="0 0 160 160">
              <circle className="score-bg-circle" cx="80" cy="80" r="70"></circle>
              <circle
                className="score-progress-circle"
                cx="80"
                cy="80"
                r="70"
                style={{ strokeDashoffset: progressOffset }}
              ></circle>
            </svg>
            <div className="score-text-overlay">
              <div className="score-number">{Math.round(data.compatibility_score)}</div>
              <div className="score-percent">/ 100</div>
            </div>
          </div>
          <div>
            <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: '0.5rem' }}>
              Overall Compatibility Score
            </h2>
            <p className="score-assessment">{data.overall_assessment}</p>
            <p className="score-disclaimer">
              * Note: The compatibility score is an approximate text-relevance estimate based on explicit resume content
              and job requirements. It is not a prediction of interview selection or hiring success.
            </p>
          </div>
        </div>
      </section>

      {/* Breakdown Table */}
      <section className="card">
        <h2 className="card-title">Score Breakdown</h2>
        <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
          The final compatibility score is calculated from four deterministic weighted factors:
        </p>
        <div className="table-responsive">
          <table className="breakdown-table">
            <thead>
              <tr>
                <th>Factor</th>
                <th>Weight</th>
                <th>Raw Score</th>
                <th>Contribution</th>
              </tr>
            </thead>
            <tbody>
              {breakdownRows.map((r, i) => (
                <tr key={i}>
                  <td>
                    <strong>{r.name}</strong>
                  </td>
                  <td>{r.weight}</td>
                  <td>{r.score.toFixed(1)} / 100</td>
                  <td>
                    <strong>+{r.contribution}%</strong>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Skills Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '1.5rem',
          marginBottom: '1.75rem',
        }}
      >
        {/* Matched */}
        <section className="card" style={{ marginBottom: 0 }}>
          <h2 className="card-title" style={{ color: 'var(--success)' }}>
            <CheckCircle2 style={{ width: 20, height: 20 }} /> Matched Skills
          </h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
            Skills explicitly identified in both resume and job requirements (hover for details):
          </p>
          <div className="skills-container">
            {data.matched_skills && data.matched_skills.length > 0 ? (
              data.matched_skills.map((s, idx) => (
                <div key={idx} className="skill-badge skill-matched">
                  <span>{s.name}</span>
                  <span className="tooltip">{s.explanation || s.importance}</span>
                </div>
              ))
            ) : (
              <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No direct matching skills.</span>
            )}
          </div>
        </section>

        {/* Missing */}
        <section className="card" style={{ marginBottom: 0 }}>
          <h2 className="card-title" style={{ color: 'var(--danger)' }}>
            <AlertTriangle style={{ width: 20, height: 20 }} /> Missing Skills
          </h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
            Important requirements not explicitly found in your resume (an unmentioned skill is not necessarily one you lack):
          </p>
          <div className="skills-container">
            {data.missing_skills && data.missing_skills.length > 0 ? (
              data.missing_skills.map((s, idx) => (
                <div key={idx} className="skill-badge skill-missing">
                  <span>{s.name}</span>
                  <span className="tooltip">{s.explanation || s.importance}</span>
                </div>
              ))
            ) : (
              <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No major required skills missing.</span>
            )}
          </div>
        </section>

        {/* Partial */}
        <section className="card" style={{ marginBottom: 0 }}>
          <h2 className="card-title" style={{ color: 'var(--warning)' }}>
            <HelpCircle style={{ width: 20, height: 20 }} /> Partial Matches
          </h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
            Related skills or experience needing stronger demonstration in the resume:
          </p>
          <div className="skills-container">
            {data.partial_skills && data.partial_skills.length > 0 ? (
              data.partial_skills.map((s, idx) => (
                <div key={idx} className="skill-badge skill-partial">
                  <span>{s.name}</span>
                  <span className="tooltip">{s.explanation || s.importance}</span>
                </div>
              ))
            ) : (
              <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No partial matches identified.</span>
            )}
          </div>
        </section>
      </div>

      {/* Strengths & Weaknesses */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '1.5rem',
          marginBottom: '1.75rem',
        }}
      >
        <section className="card" style={{ marginBottom: 0 }}>
          <h2 className="card-title">Candidate Strengths</h2>
          <ul className="bullet-list strengths">
            {data.strengths && data.strengths.length > 0 ? (
              data.strengths.map((str, i) => <li key={i}>{str}</li>)
            ) : (
              <li style={{ listStyle: 'none' }}>No specific strengths highlighted.</li>
            )}
          </ul>
        </section>

        <section className="card" style={{ marginBottom: 0 }}>
          <h2 className="card-title">Areas for Alignment</h2>
          <ul className="bullet-list weaknesses">
            {data.weaknesses && data.weaknesses.length > 0 ? (
              data.weaknesses.map((w, i) => <li key={i}>{w}</li>)
            ) : (
              <li style={{ listStyle: 'none' }}>No specific weaknesses highlighted.</li>
            )}
          </ul>
        </section>
      </div>

      {/* Improvement Suggestions */}
      <section className="card">
        <h2 className="card-title">Actionable Improvement Suggestions</h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
          Grounding guarantee: Suggestions focus strictly on how to better frame and describe your existing experience,
          without recommending fabricating qualifications.
        </p>
        <ol className="bullet-list suggestions">
          {data.suggestions && data.suggestions.length > 0 ? (
            data.suggestions.map((sug, i) => <li key={i}>{sug}</li>)
          ) : (
            <li style={{ listStyle: 'none' }}>No specific improvement suggestions.</li>
          )}
        </ol>
      </section>

      {/* Action Footer */}
      <div className="actions-footer">
        <button onClick={() => onNavigate('/')} className="btn btn-primary" style={{ width: 'auto' }}>
          Analyze Another Resume
        </button>
        <button onClick={() => onNavigate('/history')} className="btn btn-secondary">
          <History style={{ width: 18, height: 18 }} /> View History
        </button>
      </div>
    </main>
  );
}
