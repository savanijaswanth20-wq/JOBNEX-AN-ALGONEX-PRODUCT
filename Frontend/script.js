// script.js

const form = document.getElementById("analyze-Form");
const resumeInput = document.getElementById("resume_text");
const jobDescriptionInput = document.getElementById("jd_text");
const button = document.getElementById("analyze-button");
const status = document.getElementById("status");
const results = document.getElementById("results");
const resultData = document.getElementById("result-data");

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const resume_text = resumeInput.value.trim();
    const jd_text = jobDescriptionInput.value.trim();

    if (!resume_text || !jd_text) {
        status.textContent = "Please fill in both the resume and job description fields.";
        return;
    }

    button.disabled = true;
    status.textContent = "Analyzing resume...";
    results.hidden = true;

    try {
        const response = await fetch(
            "http://127.0.0.1:8000/api/analyze",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    resume_text: resume_text,
                    jd_text: jd_text
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            let message = "Request failed";
            if (data?.detail) {
                if (typeof data.detail === "string") {
                    message = data.detail;
                } else if (Array.isArray(data.detail)) {
                    message = data.detail.map((err) => err.msg || JSON.stringify(err)).join(", ");
                }
            }
            throw new Error(message);
        }

        resultData.textContent = JSON.stringify(data, null, 2);
        results.hidden = false;
        status.textContent = "Analysis completed successfully!";

    } catch (error) {
        status.textContent =
            "Could not analyze resume: " + error.message;

    } finally {
        button.disabled = false;
    }
});