// script.js - JobNex Frontend Controller

const API_BASE_URL = 'http://127.0.0.1:8000';

document.addEventListener('DOMContentLoaded', () => {
    // Form and input elements
    const form = document.getElementById('analyze-Form');
    const resumeInput = document.getElementById('Resume');
    const jdInput = document.getElementById('Job-description') || document.getElementById('Job description');
    const analyzeBtn = document.getElementById('analyze-button');
    const statusBanner = document.getElementById('status');
    const resultsSection = document.getElementById('results');

    // Stats & badges
    const apiStatusDot = document.getElementById('api-status-dot');
    const apiStatusText = document.getElementById('api-status-text');
    const resumeCount = document.getElementById('resume-count');
    const jdCount = document.getElementById('jd-count');
    const sampleBtn = document.getElementById('sample-btn');
    const clearBtn = document.getElementById('clear-btn');

    // Result elements
    const dbRecordId = document.getElementById('db-record-id');
    const scoreCircle = document.getElementById('score-circle');
    const scoreValue = document.getElementById('score-value');
    const scoreRating = document.getElementById('score-rating');
    const matchedCount = document.getElementById('matched-count');
    const missingCount = document.getElementById('missing-count');
    const matchedSkillsTags = document.getElementById('matched-skills-tags');
    const missingSkillsTags = document.getElementById('missing-skills-tags');
    const suggestionsList = document.getElementById('suggestions-list');
    const rawJsonPre = document.getElementById('raw-json-pre');
    const toggleRawJsonBtn = document.getElementById('toggle-raw-json');

    // 1. Check Backend Connectivity
    async function checkBackendHealth() {
        try {
            const response = await fetch(`${API_BASE_URL}/`, { method: 'GET' });
            if (response.ok) {
                if (apiStatusDot) {
                    apiStatusDot.classList.remove('offline');
                    apiStatusDot.classList.add('online');
                }
                if (apiStatusText) {
                    apiStatusText.textContent = 'Backend Live (FastAPI)';
                }
            } else {
                throw new Error('Status ' + response.status);
            }
        } catch (err) {
            if (apiStatusDot) {
                apiStatusDot.classList.remove('online');
                apiStatusDot.classList.add('offline');
            }
            if (apiStatusText) {
                apiStatusText.textContent = 'Backend Offline';
            }
        }
    }

    checkBackendHealth();
    setInterval(checkBackendHealth, 15000);

    // 2. Character Counters
    function updateCounts() {
        if (resumeInput && resumeCount) {
            const len = resumeInput.value.length;
            resumeCount.textContent = `${len.toLocaleString()} characters`;
        }
        if (jdInput && jdCount) {
            const len = jdInput.value.length;
            jdCount.textContent = `${len.toLocaleString()} characters`;
        }
    }

    if (resumeInput) resumeInput.addEventListener('input', updateCounts);
    if (jdInput) jdInput.addEventListener('input', updateCounts);

    // 3. Sample Data Loader
    if (sampleBtn) {
        sampleBtn.addEventListener('click', () => {
            if (resumeInput) {
                resumeInput.value = `Alex Morgan
Senior Backend Engineer
Email: alex.morgan@example.com | GitHub: alexmorgan

PROFESSIONAL SUMMARY
Experienced backend engineer with 4+ years of building robust REST APIs and scalable data microservices.
Proficient in Python, SQL databases (MySQL/PostgreSQL), and modern web frameworks like FastAPI. 
Familiar with basic React frontend integration and cloud deployments using Docker containers.

CORE SKILLS
- Languages & Frameworks: Python, FastAPI, React, SQL
- DevOps & Tools: Docker, Git, CI/CD, Linux`;
            }

            if (jdInput) {
                jdInput.value = `Job Title: Senior Python Backend Developer
Location: Remote / Hybrid

REQUIREMENTS & RESPONSIBILITIES:
We are seeking an experienced Backend Engineer to lead API development and database architecture.
- 3+ years writing clean, efficient code in Python.
- Strong proficiency in relational databases with complex SQL queries and indexing.
- Deep hands-on experience designing REST APIs with FastAPI or Flask.
- Experience containerizing services with Docker and deploying to AWS/GCP.
- Basic familiarity with React frontends is an added advantage.`;
            }

            updateCounts();
            showStatus('Sample resume and job description loaded!', 'success');
        });
    }

    // 4. Clear Button
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            if (resumeInput) resumeInput.value = '';
            if (jdInput) jdInput.value = '';
            updateCounts();
            if (resultsSection) resultsSection.hidden = true;
            if (statusBanner) statusBanner.hidden = true;
        });
    }

    // 5. Toggle Raw JSON view
    if (toggleRawJsonBtn && rawJsonPre) {
        toggleRawJsonBtn.addEventListener('click', () => {
            rawJsonPre.hidden = !rawJsonPre.hidden;
        });
    }

    // Helper: Show status banner
    function showStatus(message, type = 'info') {
        if (!statusBanner) return;
        statusBanner.textContent = message;
        statusBanner.className = `status-banner ${type}`;
        statusBanner.hidden = false;
    }

    // 6. Handle Form Submission
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const resumeText = resumeInput ? resumeInput.value.trim() : '';
            const jdText = jdInput ? jdInput.value.trim() : '';

            if (!resumeText || !jdText) {
                showStatus('Please provide both Resume and Job Description text.', 'error');
                return;
            }

            // Set loading state
            if (analyzeBtn) {
                analyzeBtn.disabled = true;
                analyzeBtn.classList.add('loading');
            }
            showStatus('Analyzing candidate fit against job requirements...', 'info');

            try {
                const response = await fetch(`${API_BASE_URL}/api/analyze`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        resume_text: resumeText,
                        jd_text: jdText
                    })
                });

                if (!response.ok) {
                    const errData = await response.json().catch(() => ({}));
                    throw new Error(errData.detail || `Server responded with HTTP ${response.status}`);
                }

                const data = await response.json();
                renderResults(data);
                showStatus('Analysis completed and saved to database successfully!', 'success');

            } catch (error) {
                console.error('Analysis error:', error);
                showStatus(`Failed to analyze: ${error.message}. Is the backend running?`, 'error');
            } finally {
                if (analyzeBtn) {
                    analyzeBtn.disabled = false;
                    analyzeBtn.classList.remove('loading');
                }
            }
        });
    }

    // 7. Render Analysis Results
    function renderResults(data) {
        if (!resultsSection) return;

        // Analysis record ID
        const recordId = data.Analysis_Id || data.analysis_id || 'N/A';
        if (dbRecordId) {
            dbRecordId.textContent = `#${recordId}`;
        }

        const result = data.result || {};
        const score = Number(result.matched_score || 0);
        const matched = result.matched_skills || [];
        const missing = result.missing_skills || [];
        const suggestions = result.suggestions || result.suggestion || [];

        // Update Score and Animated Circle
        if (scoreValue) {
            scoreValue.textContent = `${Math.round(score)}%`;
        }

        let ratingText = 'Low Match';
        let circleColor = '#ef4444';
        if (score >= 80) {
            ratingText = 'High Match';
            circleColor = '#10b981';
        } else if (score >= 50) {
            ratingText = 'Moderate Match';
            circleColor = '#f59e0b';
        }

        if (scoreRating) {
            scoreRating.textContent = ratingText;
            scoreRating.style.color = circleColor;
        }

        if (scoreCircle) {
            scoreCircle.style.background = `conic-gradient(${circleColor} 0% ${score}%, rgba(255, 255, 255, 0.05) ${score}% 100%)`;
            scoreCircle.style.boxShadow = `0 0 35px ${circleColor}40`;
        }

        // Matched Skills
        if (matchedCount) matchedCount.textContent = matched.length;
        if (matchedSkillsTags) {
            matchedSkillsTags.innerHTML = '';
            if (matched.length === 0) {
                matchedSkillsTags.innerHTML = '<span class="empty-state">No matching skills detected.</span>';
            } else {
                matched.forEach(skill => {
                    const tag = document.createElement('span');
                    tag.className = 'skill-pill matched';
                    tag.innerHTML = `✓ ${escapeHtml(skill)}`;
                    matchedSkillsTags.appendChild(tag);
                });
            }
        }

        // Missing Skills
        if (missingCount) missingCount.textContent = missing.length;
        if (missingSkillsTags) {
            missingSkillsTags.innerHTML = '';
            if (missing.length === 0) {
                missingSkillsTags.innerHTML = '<span class="empty-state">All target skills present!</span>';
            } else {
                missing.forEach(skill => {
                    const tag = document.createElement('span');
                    tag.className = 'skill-pill missing';
                    tag.innerHTML = `+ ${escapeHtml(skill)}`;
                    missingSkillsTags.appendChild(tag);
                });
            }
        }

        // Recommendations List
        if (suggestionsList) {
            suggestionsList.innerHTML = '';
            if (suggestions.length === 0) {
                suggestionsList.innerHTML = '<li class="suggestion-item">No specific suggestions at this time. Resume matches all tracked criteria!</li>';
            } else {
                suggestions.forEach((item, index) => {
                    const li = document.createElement('li');
                    li.className = 'suggestion-item';
                    li.innerHTML = `
                        <span class="suggestion-number">${index + 1}</span>
                        <span>${escapeHtml(item)}</span>
                    `;
                    suggestionsList.appendChild(li);
                });
            }
        }

        // Raw JSON output (for developer inspection or automated tests)
        if (rawJsonPre) {
            rawJsonPre.textContent = JSON.stringify(data, null, 2);
        }

        // Reveal the section and scroll into view smoothly
        resultsSection.hidden = false;
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }
});
