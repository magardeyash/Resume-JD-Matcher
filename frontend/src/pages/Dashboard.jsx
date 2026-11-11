import React, { useState, useRef } from 'react';
import { Upload, FileUp, Briefcase, FileCheck, X, Sparkles } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const MAX_SIZE_BYTES = 5 * 1024 * 1024; // 5 MB
const ALLOWED_EXTS = ['.pdf', '.docx', '.txt'];

export default function Dashboard({ onNavigate }) {
  const { token, user, isAuthenticated } = useAuth();
  const [selectedFile, setSelectedFile] = useState(null);
  const [jobTitle, setJobTitle] = useState('');
  const [jdText, setJdText] = useState('');
  const [isDragover, setIsDragover] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const handleFileChange = (file) => {
    setError('');
    if (!file) return;

    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTS.includes(ext)) {
      setError(`Unsupported file type '${ext}'. Please upload a PDF, DOCX, or TXT file.`);
      return;
    }

    if (file.size > MAX_SIZE_BYTES) {
      setError(`File is too large (${(file.size / (1024 * 1024)).toFixed(1)} MB). Maximum allowed size is 5 MB.`);
      return;
    }

    setSelectedFile(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragover(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!selectedFile) {
      setError('Please upload a resume file (PDF, DOCX, or TXT).');
      return;
    }

    const trimmedJd = jdText.trim();
    if (!trimmedJd) {
      setError('Please enter a job description.');
      return;
    }

    if (trimmedJd.length > 10000) {
      setError(`Job description exceeds the 10,000 character limit (${trimmedJd.length.toLocaleString()} characters).`);
      return;
    }

    if (jobTitle.trim().length > 200) {
      setError('Job title exceeds the 200 character limit.');
      return;
    }

    setLoading(true);

    const formData = new FormData();
    formData.append('resume', selectedFile);
    formData.append('jd_text', trimmedJd);
    if (jobTitle.trim()) {
      formData.append('job_title', jobTitle.trim());
    }

    try {
      const headers = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers,
        body: formData,
      });

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        let msg = 'An unexpected error occurred during analysis.';
        if (data && data.detail) {
          msg = data.detail;
        } else if (response.status === 503) {
          msg = 'AI analysis service is currently unavailable or unconfigured. Please check GEMINI_API_KEY.';
        }
        setError(msg);
        setLoading(false);
        return;
      }

      // Store in localStorage
      try {
        const stored = JSON.parse(localStorage.getItem('resumematch_ids') || '[]');
        if (!stored.includes(data.id)) {
          stored.unshift(data.id);
          localStorage.setItem('resumematch_ids', JSON.stringify(stored));
        }
      } catch (err) {
        console.warn('Could not save to localStorage:', err);
      }

      onNavigate(`/results/${data.id}`);
    } catch (err) {
      setError('Network error: Could not connect to the backend server.');
      setLoading(false);
    }
  };

  return (
    <main className="container">
      <div className="page-header">
        {isAuthenticated && (
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.4rem',
              color: 'var(--primary)',
              fontWeight: 600,
              fontSize: '0.9rem',
              marginBottom: '0.5rem',
            }}
          >
            <Sparkles style={{ width: 16, height: 16 }} />
            Welcome back, {user?.full_name || user?.email}!
          </div>
        )}
        <h1 className="page-title">Find out how well your resume matches a job</h1>
        <p className="page-subtitle">
          Upload your resume and paste a job description to receive AI-powered compatibility analysis and feedback.
        </p>
      </div>

      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate>
        {/* Step 1: Upload */}
        <section className="card">
          <h2 className="card-title">
            <FileUp style={{ width: 22, height: 22, color: 'var(--primary)' }} />
            1. Upload Your Resume
          </h2>

          <input
            type="file"
            ref={fileInputRef}
            accept=".pdf,.docx,.txt"
            style={{ display: 'none' }}
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                handleFileChange(e.target.files[0]);
              }
            }}
          />

          {!selectedFile ? (
            <div
              className={`dropzone ${isDragover ? 'dragover' : ''}`}
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragover(true);
              }}
              onDragLeave={(e) => {
                e.preventDefault();
                setIsDragover(false);
              }}
              onDrop={handleDrop}
            >
              <Upload className="dropzone-icon" />
              <div className="dropzone-text">
                Drag and drop your resume here, or <span style={{ color: 'var(--primary)', textDecoration: 'underline' }}>browse</span>
              </div>
              <div className="dropzone-hint">Supports PDF, DOCX, TXT (Max 5 MB)</div>
            </div>
          ) : (
            <div className="file-preview">
              <div className="file-preview-name">
                <FileCheck style={{ width: 20, height: 20 }} />
                <span>{selectedFile.name}</span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  ({(selectedFile.size / 1024).toFixed(0)} KB)
                </span>
              </div>
              <button
                type="button"
                className="btn-remove"
                onClick={() => {
                  setSelectedFile(null);
                  if (fileInputRef.current) fileInputRef.current.value = '';
                }}
              >
                <X style={{ width: 18, height: 18 }} />
              </button>
            </div>
          )}
        </section>

        {/* Step 2: Job Description */}
        <section className="card">
          <h2 className="card-title">
            <Briefcase style={{ width: 22, height: 22, color: 'var(--primary)' }} />
            2. Target Job Description
          </h2>

          <div className="form-group">
            <label htmlFor="job-title" className="form-label">
              Job Title (Optional)
            </label>
            <input
              type="text"
              id="job-title"
              className="form-input"
              placeholder="e.g. Senior Backend Engineer"
              maxLength={200}
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label htmlFor="jd-text" className="form-label">
              Job Description <span style={{ color: 'var(--danger)' }}>*</span>
            </label>
            <textarea
              id="jd-text"
              className="form-textarea"
              placeholder="Paste the complete job description, responsibilities, and requirements here..."
              required
              maxLength={10000}
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
            />
            <div className="char-counter">
              <span style={{ color: jdText.length > 10000 ? 'var(--danger)' : 'var(--text-muted)' }}>
                {jdText.length.toLocaleString()} / 10,000
              </span>
            </div>
          </div>
        </section>

        <div style={{ marginTop: '1rem' }}>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? (
              <>
                <span className="spinner"></span>
                Analyzing My Resume...
              </>
            ) : (
              'Analyze My Resume'
            )}
          </button>
        </div>
      </form>
    </main>
  );
}
