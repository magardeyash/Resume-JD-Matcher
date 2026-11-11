import React, { useEffect, useState } from 'react';
import { History as HistoryIcon, Trash2, ArrowRight, ShieldCheck, Trash } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function History({ onNavigate }) {
  const { token, isAuthenticated, user } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadHistory = async () => {
    setLoading(true);
    if (isAuthenticated && token) {
      // 1. Authenticated user: fetch directly from server database
      try {
        const res = await fetch('/api/analyses', {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const list = await res.json();
          setItems(list);
        } else {
          setItems([]);
        }
      } catch (err) {
        console.error('Failed to load user analyses:', err);
        setItems([]);
      } finally {
        setLoading(false);
      }
      return;
    }

    // 2. Guest user: fallback to localStorage IDs
    let ids = [];
    try {
      ids = JSON.parse(localStorage.getItem('resumematch_ids') || '[]');
    } catch {
      ids = [];
    }

    if (ids.length === 0) {
      setItems([]);
      setLoading(false);
      return;
    }

    const fetched = await Promise.allSettled(
      ids.map((id) =>
        fetch(`/api/analyses/${id}`).then((r) => (r.ok ? r.json() : null))
      )
    );

    const validItems = [];
    const validIds = [];

    fetched.forEach((res, idx) => {
      if (res.status === 'fulfilled' && res.value) {
        validItems.push(res.value);
        validIds.push(ids[idx]);
      }
    });

    if (validIds.length !== ids.length) {
      localStorage.setItem('resumematch_ids', JSON.stringify(validIds));
    }

    validItems.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    setItems(validItems);
    setLoading(false);
  };

  useEffect(() => {
    loadHistory();
  }, [isAuthenticated, token]);

  const handleDeleteItem = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm('Delete this analysis from your history?')) {
      return;
    }

    if (isAuthenticated && token) {
      try {
        const res = await fetch(`/api/analyses/${id}`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          setItems((prev) => prev.filter((item) => item.id !== id));
        } else {
          alert('Could not delete this analysis.');
        }
      } catch {
        alert('Failed to connect to server.');
      }
    } else {
      // Guest local removal
      try {
        const ids = JSON.parse(localStorage.getItem('resumematch_ids') || '[]');
        const updated = ids.filter((storedId) => storedId !== id);
        localStorage.setItem('resumematch_ids', JSON.stringify(updated));
        setItems((prev) => prev.filter((item) => item.id !== id));
      } catch {
        // ignore
      }
    }
  };

  const handleClearAll = () => {
    if (!window.confirm('Clear all your local analysis history?')) {
      return;
    }
    localStorage.removeItem('resumematch_ids');
    setItems([]);
  };

  return (
    <main className="container">
      <div
        className="page-header"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-end',
          textAlign: 'left',
          marginBottom: '1.5rem',
        }}
      >
        <div>
          <h1 className="page-title">Analysis History</h1>
          <p className="page-subtitle">
            {isAuthenticated ? (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', color: 'var(--success)' }}>
                <ShieldCheck style={{ width: 16, height: 16 }} />
                Saved in your private account ({user?.email})
              </span>
            ) : (
              'Analyses stored locally in this browser.'
            )}
          </p>
        </div>
        {!isAuthenticated && items.length > 0 && (
          <div>
            <button type="button" onClick={handleClearAll} className="btn btn-danger-outline">
              <Trash2 style={{ width: 16, height: 16 }} /> Clear History
            </button>
          </div>
        )}
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '4rem 1rem' }}>
          <div
            className="spinner"
            style={{ width: 36, height: 36, borderColor: 'rgba(79, 70, 229, 0.2)', borderTopColor: 'var(--primary)' }}
          ></div>
          <p style={{ marginTop: '1rem', color: 'var(--text-muted)' }}>Loading history...</p>
        </div>
      ) : items.length === 0 ? (
        <div className="card history-empty">
          <HistoryIcon style={{ width: 48, height: 48, color: 'var(--text-muted)', margin: '0 auto 1rem' }} />
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text)', marginBottom: '0.5rem' }}>
            No analyses found
          </h3>
          <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
            {isAuthenticated
              ? "You haven't run any resume analyses in this account yet."
              : "You haven't run any resume analyses in this browser yet."}
          </p>
          <button onClick={() => onNavigate('/')} className="btn btn-primary" style={{ width: 'auto' }}>
            Analyze a Resume <ArrowRight style={{ width: 18, height: 18 }} />
          </button>
        </div>
      ) : (
        <div className="card" style={{ padding: 0 }}>
          <div className="table-responsive">
            <table className="history-table">
              <thead>
                <tr>
                  <th>Resume File</th>
                  <th>Target Job Title</th>
                  <th>Match Score</th>
                  <th>Date</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => {
                  const dateStr = new Date(item.created_at).toLocaleDateString(undefined, {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                  });
                  const scoreBadgeClass =
                    item.compatibility_score >= 70
                      ? 'skill-matched'
                      : item.compatibility_score >= 45
                      ? 'skill-partial'
                      : 'skill-missing';

                  return (
                    <tr key={item.id}>
                      <td>
                        <strong>{item.resume_filename}</strong>
                      </td>
                      <td>{item.job_title || 'Not specified'}</td>
                      <td>
                        <span className={`skill-badge ${scoreBadgeClass}`} style={{ cursor: 'default' }}>
                          {Math.round(item.compatibility_score)}%
                        </span>
                      </td>
                      <td>{dateStr}</td>
                      <td style={{ textAlign: 'right' }}>
                        <div style={{ display: 'inline-flex', gap: '0.5rem' }}>
                          <button
                            type="button"
                            onClick={() => onNavigate(`/results/${item.id}`)}
                            className="btn btn-secondary"
                            style={{ padding: '0.35rem 0.75rem', fontSize: '0.85rem' }}
                          >
                            View Result
                          </button>
                          <button
                            type="button"
                            onClick={(e) => handleDeleteItem(item.id, e)}
                            className="btn btn-danger-outline"
                            style={{ padding: '0.35rem 0.5rem' }}
                            title="Delete this analysis"
                          >
                            <Trash style={{ width: 14, height: 14 }} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </main>
  );
}
