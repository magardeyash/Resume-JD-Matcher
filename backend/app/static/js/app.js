// ResumeMatch Client-Side Application Logic

document.addEventListener("DOMContentLoaded", () => {
  initDashboard();
  initResults();
  initHistory();
});

// Helper: Escape HTML to prevent XSS
function escapeHtml(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/* =========================================================================
   DASHBOARD
   ========================================================================= */
function initDashboard() {
  const form = document.getElementById("analyze-form");
  if (!form) return;

  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("resume-input");
  const filePreview = document.getElementById("file-preview");
  const fileNameDisplay = document.getElementById("file-name");
  const btnRemoveFile = document.getElementById("btn-remove-file");
  const jdTextarea = document.getElementById("jd-text");
  const charCounter = document.getElementById("char-count");
  const submitBtn = document.getElementById("btn-analyze");
  const errorAlert = document.getElementById("error-alert");

  let selectedFile = null;
  const MAX_SIZE_BYTES = 5 * 1024 * 1024; // 5 MB
  const ALLOWED_EXTS = [".pdf", ".docx", ".txt"];

  function showError(msg) {
    if (errorAlert) {
      errorAlert.textContent = msg;
      errorAlert.style.display = "block";
      errorAlert.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }

  function hideError() {
    if (errorAlert) {
      errorAlert.style.display = "none";
      errorAlert.textContent = "";
    }
  }

  function handleFile(file) {
    hideError();
    if (!file) return;

    const ext = "." + file.name.split(".").pop().toLowerCase();
    if (!ALLOWED_EXTS.includes(ext)) {
      showError(`Unsupported file type '${ext}'. Please upload a PDF, DOCX, or TXT file.`);
      return;
    }

    if (file.size > MAX_SIZE_BYTES) {
      showError(`File is too large (${(file.size / (1024 * 1024)).toFixed(1)} MB). Maximum allowed size is 5 MB.`);
      return;
    }

    selectedFile = file;
    fileNameDisplay.textContent = file.name;
    filePreview.style.display = "flex";
    dropzone.style.display = "none";
  }

  // Click dropzone to open picker
  dropzone.addEventListener("click", () => fileInput.click());

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  });

  // Drag and drop events
  ["dragenter", "dragover"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove("dragover");
    });
  });

  dropzone.addEventListener("drop", (e) => {
    const dt = e.dataTransfer;
    if (dt.files && dt.files[0]) {
      handleFile(dt.files[0]);
    }
  });

  // Remove file
  btnRemoveFile.addEventListener("click", (e) => {
    e.stopPropagation();
    selectedFile = null;
    fileInput.value = "";
    filePreview.style.display = "none";
    dropzone.style.display = "block";
    hideError();
  });

  // Character counter for JD
  if (jdTextarea && charCounter) {
    jdTextarea.addEventListener("input", () => {
      const len = jdTextarea.value.length;
      charCounter.textContent = `${len.toLocaleString()} / 10,000`;
      if (len > 10000) {
        charCounter.style.color = "var(--danger)";
      } else {
        charCounter.style.color = "var(--text-muted)";
      }
    });
  }

  // Form submission
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideError();

    if (!selectedFile) {
      showError("Please upload a resume file (PDF, DOCX, or TXT).");
      return;
    }

    const jdVal = jdTextarea.value.trim();
    if (!jdVal) {
      showError("Please enter a job description.");
      return;
    }

    if (jdVal.length > 10000) {
      showError(`Job description exceeds the 10,000 character limit (${jdVal.length.toLocaleString()} characters).`);
      return;
    }

    const jobTitleInput = document.getElementById("job-title");
    const jobTitleVal = jobTitleInput ? jobTitleInput.value.trim() : "";
    if (jobTitleVal.length > 200) {
      showError("Job title exceeds the 200 character limit.");
      return;
    }

    // Set loading state
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner"></span> Analyzing My Resume...';

    const formData = new FormData();
    formData.append("resume", selectedFile);
    formData.append("jd_text", jdVal);
    if (jobTitleVal) {
      formData.append("job_title", jobTitleVal);
    }

    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        body: formData,
      });

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        let msg = "An unexpected error occurred during analysis.";
        if (data && data.detail) {
          msg = data.detail;
        } else if (response.status === 503) {
          msg = "AI analysis service is currently unavailable or unconfigured. Please check GEMINI_API_KEY.";
        }
        showError(msg);
        submitBtn.disabled = false;
        submitBtn.innerHTML = "Analyze My Resume";
        return;
      }

      // Save ID to local storage for history
      try {
        const stored = JSON.parse(localStorage.getItem("resumematch_ids") || "[]");
        if (!stored.includes(data.id)) {
          stored.unshift(data.id);
          localStorage.setItem("resumematch_ids", JSON.stringify(stored));
        }
      } catch (err) {
        console.warn("Could not save to localStorage:", err);
      }

      // Redirect to results
      window.location.href = `/results/${data.id}`;
    } catch (err) {
      showError("Network error: Could not connect to the server.");
      submitBtn.disabled = false;
      submitBtn.innerHTML = "Analyze My Resume";
    }
  });
}

/* =========================================================================
   RESULTS PAGE
   ========================================================================= */
async function initResults() {
  const container = document.getElementById("results-root");
  if (!container) return;

  const analysisId = container.dataset.analysisId;
  if (!analysisId) return;

  const loadingEl = document.getElementById("results-loading");
  const contentEl = document.getElementById("results-content");
  const errorEl = document.getElementById("results-error");

  try {
    const res = await fetch(`/api/analyses/${analysisId}`);
    if (!res.ok) {
      let detail = "Analysis not found.";
      if (res.status === 400) detail = "Invalid analysis ID.";
      throw new Error(detail);
    }

    const data = await res.json();
    renderResults(data);
    if (loadingEl) loadingEl.style.display = "none";
    if (contentEl) contentEl.style.display = "block";
  } catch (err) {
    if (loadingEl) loadingEl.style.display = "none";
    if (errorEl) {
      errorEl.textContent = err.message || "Failed to load analysis results.";
      errorEl.style.display = "block";
    }
  }
}

function renderResults(data) {
  // Filename & Title
  const titleEl = document.getElementById("res-title");
  if (titleEl) {
    const titleText = data.job_title ? escapeHtml(data.job_title) : "Position Match Analysis";
    titleEl.textContent = titleText;
  }

  const subtitleEl = document.getElementById("res-subtitle");
  if (subtitleEl) {
    const dateStr = new Date(data.created_at).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
    subtitleEl.textContent = `Resume: ${data.resume_filename} • Analyzed on ${dateStr}`;
  }

  // Overall Score & Gauge
  const scoreNumEl = document.getElementById("res-score-number");
  if (scoreNumEl) {
    scoreNumEl.textContent = Math.round(data.compatibility_score);
  }

  const progressCircle = document.getElementById("score-progress");
  if (progressCircle) {
    const radius = 70;
    const circumference = 2 * Math.PI * radius; // ~440
    const offset = circumference - (data.compatibility_score / 100) * circumference;
    setTimeout(() => {
      progressCircle.style.strokeDashoffset = offset;
    }, 150);
  }

  // Assessment text
  const assessEl = document.getElementById("res-assessment");
  if (assessEl) {
    assessEl.textContent = data.overall_assessment || `Your resume has a ${Math.round(data.compatibility_score)}% compatibility match with this position.`;
  }

  // Score Breakdown Table
  const breakdownRows = [
    {
      name: "Semantic Similarity",
      weight: "30%",
      score: data.semantic_score,
      contribution: (data.semantic_score * 0.3).toFixed(1),
    },
    {
      name: "Required Skill Coverage",
      weight: "40%",
      score: data.required_skills_score,
      contribution: (data.required_skills_score * 0.4).toFixed(1),
    },
    {
      name: "Experience Relevance",
      weight: "20%",
      score: data.experience_score,
      contribution: (data.experience_score * 0.2).toFixed(1),
    },
    {
      name: "Preferred Skill Coverage",
      weight: "10%",
      score: data.preferred_skills_score,
      contribution: (data.preferred_skills_score * 0.1).toFixed(1),
    },
  ];

  const tbody = document.getElementById("breakdown-tbody");
  if (tbody) {
    tbody.innerHTML = breakdownRows
      .map(
        (r) => `
      <tr>
        <td><strong>${escapeHtml(r.name)}</strong></td>
        <td>${r.weight}</td>
        <td>${r.score.toFixed(1)} / 100</td>
        <td><strong>+${r.contribution}%</strong></td>
      </tr>
    `
      )
      .join("");
  }

  // Skills Render Helper
  function renderSkillList(containerId, skills, typeClass, emptyMsg) {
    const el = document.getElementById(containerId);
    if (!el) return;
    if (!skills || skills.length === 0) {
      el.innerHTML = `<span style="color: var(--text-muted); font-size: 0.9rem;">${escapeHtml(emptyMsg)}</span>`;
      return;
    }
    el.innerHTML = skills
      .map(
        (s) => `
      <div class="skill-badge ${typeClass}">
        <span>${escapeHtml(s.name)}</span>
        <span class="tooltip">${escapeHtml(s.explanation || s.importance || "")}</span>
      </div>
    `
      )
      .join("");
  }

  renderSkillList("matched-skills-list", data.matched_skills, "skill-matched", "No direct matching skills identified.");
  renderSkillList("missing-skills-list", data.missing_skills, "skill-missing", "No major required skills missing.");
  renderSkillList("partial-skills-list", data.partial_skills, "skill-partial", "No partially matching skills identified.");

  // Strengths
  const strengthsEl = document.getElementById("strengths-list");
  if (strengthsEl) {
    if (data.strengths && data.strengths.length > 0) {
      strengthsEl.innerHTML = data.strengths.map((s) => `<li>${escapeHtml(s)}</li>`).join("");
    } else {
      strengthsEl.innerHTML = `<li style="list-style:none;">No specific strengths highlighted.</li>`;
    }
  }

  // Weaknesses
  const weaknessesEl = document.getElementById("weaknesses-list");
  if (weaknessesEl) {
    if (data.weaknesses && data.weaknesses.length > 0) {
      weaknessesEl.innerHTML = data.weaknesses.map((w) => `<li>${escapeHtml(w)}</li>`).join("");
    } else {
      weaknessesEl.innerHTML = `<li style="list-style:none;">No specific weaknesses highlighted.</li>`;
    }
  }

  // Suggestions
  const suggestionsEl = document.getElementById("suggestions-list");
  if (suggestionsEl) {
    if (data.suggestions && data.suggestions.length > 0) {
      suggestionsEl.innerHTML = data.suggestions.map((sg) => `<li>${escapeHtml(sg)}</li>`).join("");
    } else {
      suggestionsEl.innerHTML = `<li style="list-style:none;">No specific improvement suggestions.</li>`;
    }
  }
}

/* =========================================================================
   HISTORY PAGE
   ========================================================================= */
async function initHistory() {
  const tableBody = document.getElementById("history-tbody");
  if (!tableBody) return;

  const emptyState = document.getElementById("history-empty");
  const tableContainer = document.getElementById("history-table-container");
  const clearBtn = document.getElementById("btn-clear-history");

  let ids = [];
  try {
    ids = JSON.parse(localStorage.getItem("resumematch_ids") || "[]");
  } catch (e) {
    ids = [];
  }

  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      if (confirm("Clear your local analysis history?")) {
        localStorage.removeItem("resumematch_ids");
        window.location.reload();
      }
    });
  }

  if (ids.length === 0) {
    if (emptyState) emptyState.style.display = "block";
    if (tableContainer) tableContainer.style.display = "none";
    if (clearBtn) clearBtn.style.display = "none";
    return;
  }

  // Fetch each ID in parallel
  const results = await Promise.allSettled(
    ids.map((id) =>
      fetch(`/api/analyses/${id}`).then((r) => {
        if (!r.ok) return null;
        return r.json();
      })
    )
  );

  const validItems = [];
  const validIds = [];

  results.forEach((res, idx) => {
    if (res.status === "fulfilled" && res.value) {
      validItems.push(res.value);
      validIds.push(ids[idx]);
    }
  });

  // Clean up nonexistent IDs from localStorage
  if (validIds.length !== ids.length) {
    localStorage.setItem("resumematch_ids", JSON.stringify(validIds));
  }

  if (validItems.length === 0) {
    if (emptyState) emptyState.style.display = "block";
    if (tableContainer) tableContainer.style.display = "none";
    if (clearBtn) clearBtn.style.display = "none";
    return;
  }

  // Sort by created_at desc
  validItems.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

  tableBody.innerHTML = validItems
    .map((item) => {
      const dateStr = new Date(item.created_at).toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
      const scoreBadgeClass =
        item.compatibility_score >= 70
          ? "skill-matched"
          : item.compatibility_score >= 45
          ? "skill-partial"
          : "skill-missing";

      return `
      <tr>
        <td><strong>${escapeHtml(item.resume_filename)}</strong></td>
        <td>${escapeHtml(item.job_title || "Not specified")}</td>
        <td>
          <span class="skill-badge ${scoreBadgeClass}" style="cursor: default;">
            ${Math.round(item.compatibility_score)}%
          </span>
        </td>
        <td>${dateStr}</td>
        <td>
          <a href="/results/${item.id}" class="btn btn-secondary" style="padding: 0.4rem 0.8rem; font-size: 0.85rem;">
            View Result
          </a>
        </td>
      </tr>
    `;
    })
    .join("");

  if (emptyState) emptyState.style.display = "none";
  if (tableContainer) tableContainer.style.display = "block";
  if (clearBtn) clearBtn.style.display = "inline-flex";
}
