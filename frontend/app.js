const API_BASE = "";

async function apiRequest(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, options);
  let data = null;
  try {
    data = await res.json();
  } catch (err) {
    data = null;
  }
  if (!res.ok) {
    throw new Error((data && data.detail) || "Request failed");
  }
  return data;
}

function setToken(token) {
  localStorage.setItem("token", token);
}

function getToken() {
  return localStorage.getItem("token");
}

const authHeaders = () => {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

let lastResumes = [];

function scoreBadge(score) {
  const badge = document.createElement("span");
  badge.className = "badge";
  if (score < 60) {
    badge.classList.add("low");
  }
  badge.textContent = `${score}%`;
  return badge;
}

function renderResumesTable(resumes) {
  const table = document.getElementById("resumes-table");
  if (!table) return;
  const body = table.querySelector("tbody");
  body.innerHTML = "";
  if (!resumes.length) {
    const row = document.createElement("tr");
    row.innerHTML = "<td colspan='3'>No data loaded.</td>";
    body.appendChild(row);
    return;
  }

  resumes.forEach((resume) => {
    const row = document.createElement("tr");
    const nameCell = document.createElement("td");
    nameCell.textContent = resume.file_name;
    const statusCell = document.createElement("td");
    statusCell.textContent = resume.status;
    const scoreCell = document.createElement("td");
    scoreCell.appendChild(scoreBadge(resume.score || 0));
    row.appendChild(nameCell);
    row.appendChild(statusCell);
    row.appendChild(scoreCell);
    body.appendChild(row);
  });
}

function renderShortlist(resumes, threshold) {
  const table = document.getElementById("shortlist-table");
  if (!table) return;
  const body = table.querySelector("tbody");
  body.innerHTML = "";

  const shortlisted = resumes.filter((resume) => (resume.score || 0) >= threshold);
  if (!shortlisted.length) {
    const row = document.createElement("tr");
    row.innerHTML = "<td colspan='2'>No shortlisted candidates yet.</td>";
    body.appendChild(row);
    return;
  }

  shortlisted.forEach((resume) => {
    const row = document.createElement("tr");
    const nameCell = document.createElement("td");
    nameCell.textContent = resume.file_name;
    const scoreCell = document.createElement("td");
    scoreCell.appendChild(scoreBadge(resume.score || 0));
    row.appendChild(nameCell);
    row.appendChild(scoreCell);
    body.appendChild(row);
  });
}

async function loadJobsOptions() {
  const selects = document.querySelectorAll(".job-select");
  if (!selects.length) return;
  try {
    const jobs = await apiRequest("/jobs", { headers: { ...authHeaders() } });
    selects.forEach((select) => {
      select.innerHTML = "";
      const placeholder = document.createElement("option");
      placeholder.value = "";
      placeholder.textContent = "Select a job";
      select.appendChild(placeholder);
      jobs.forEach((job) => {
        const option = document.createElement("option");
        option.value = job.id;
        option.textContent = `${job.title} (#${job.id})`;
        select.appendChild(option);
      });
    });
  } catch (err) {
    const status = document.getElementById("jobs-select-status");
    if (status) {
      setStatus(status, err.message, false);
    }
  }
}

function setStatus(el, message, ok = true) {
  if (!el) return;
  el.textContent = message;
  el.dataset.status = ok ? "ok" : "error";
}

function getQueryParam(name) {
  const params = new URLSearchParams(window.location.search);
  return params.get(name) || "";
}

const inviteForm = document.getElementById("invite-form");
if (inviteForm) {
  inviteForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = inviteForm.inviteEmail.value;
    const result = document.getElementById("invite-result");
    try {
      const data = await apiRequest("/auth/invite", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ email }),
      });
      setStatus(result, `Invite sent. Link: ${data.signup_link}`);
    } catch (err) {
      setStatus(result, err.message, false);
    }
  });
}

const signupForm = document.getElementById("signup-form");
if (signupForm) {
  const tokenField = signupForm.querySelector("input[name='inviteToken']");
  const emailField = signupForm.querySelector("input[name='email']");
  if (tokenField) tokenField.value = getQueryParam("token");
  if (emailField) emailField.value = getQueryParam("email");

  signupForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      invite_token: signupForm.inviteToken.value,
      email: signupForm.email.value,
      password: signupForm.password.value,
      full_name: signupForm.fullName.value,
    };
    const result = document.getElementById("signup-result");
    try {
      const data = await apiRequest("/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      setToken(data.access_token);
      setStatus(result, "Login complete.");

      setTimeout(() => {
        window.location.href = "/jobs.html";
      }, 1000);
    } catch (err) {
      setStatus(result, err.message, false);
    }
  });
}

const loginForm = document.getElementById("login-form");
if (loginForm) {
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      email: loginForm.email.value,
      password: loginForm.password.value,
    };
    const result = document.getElementById("login-result");
    try {
      const data = await apiRequest("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      setToken(data.access_token);
      setStatus(result, "Login successful. Redirecting...");
      setTimeout(() => {
        window.location.href = "/jobs.html";
      }, 1000);
    } catch (err) {
      setStatus(result, err.message, false);
    }
  });
}

const jobForm = document.getElementById("job-form");
if (jobForm) {
  jobForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      title: jobForm.title.value,
      jd_text: jobForm.jdText.value,
    };
    const result = document.getElementById("job-result");
    try {
      const data = await apiRequest("/jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify(payload),
      });
      setStatus(result, `Job created: ${data.title}`);
      setTimeout(() => {
        window.location.href = "/resumes.html";
      }, 1000);
    } catch (err) {
      setStatus(result, err.message, false);
    }
  });
}

const loadJobs = document.getElementById("load-jobs");
if (loadJobs) {
  loadJobs.addEventListener("click", async () => {
    const output = document.getElementById("jobs-output");
    try {
      const data = await apiRequest("/jobs", { headers: { ...authHeaders() } });
      output.textContent = JSON.stringify(data, null, 2);
    } catch (err) {
      output.textContent = err.message;
    }
  });
}

const onboardingForm = document.getElementById("onboarding-form");
if (onboardingForm) {
  onboardingForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      organization: onboardingForm.organization.value,
      notes: onboardingForm.notes.value,
    };
    const result = document.getElementById("onboarding-result");
    try {
      await apiRequest("/users/onboarding", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify(payload),
      });
      setStatus(result, "Onboarding saved.");
    } catch (err) {
      setStatus(result, err.message, false);
    }
  });
}

const onboardedBtn = document.getElementById("load-onboarded");
if (onboardedBtn) {
  onboardedBtn.addEventListener("click", async () => {
    const output = document.getElementById("onboarded-output");
    try {
      const data = await apiRequest("/users/onboarded", { headers: { ...authHeaders() } });
      output.textContent = JSON.stringify(data, null, 2);
    } catch (err) {
      output.textContent = err.message;
    }
  });
}

const resumeForm = document.getElementById("resume-form");
if (resumeForm) {
  resumeForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const jobId = resumeForm.jobId.value;
    const files = resumeForm.resumes.files;
    const result = document.getElementById("resume-result");
    if (!jobId || !files.length) {
      setStatus(result, "Select a job and upload files.", false);
      return;
    }
    const formData = new FormData();
    for (const file of files) {
      formData.append("files", file);
    }
    try {
      const data = await apiRequest(`/jobs/${jobId}/resumes/bulk`, {
        method: "POST",
        headers: { ...authHeaders() },
        body: formData,
      });
      setStatus(result, `Uploaded ${data.length} resumes.`);
    } catch (err) {
      setStatus(result, err.message, false);
    }
  });
}

const screenBtn = document.getElementById("screen-resumes");
if (screenBtn) {
  screenBtn.addEventListener("click", async () => {
    const jobId = document.getElementById("screen-job-id").value;
    const output = document.getElementById("screen-result");
    if (!jobId) {
      setStatus(output, "Select a job first.", false);
      return;
    }
    try {
      const data = await apiRequest(`/jobs/${jobId}/screen`, {
        method: "POST",
        headers: { ...authHeaders() },
      });
      setStatus(output, `Scored ${data.count} resumes.`);
    } catch (err) {
      setStatus(output, err.message, false);
    }
  });
}

const loadResumesBtn = document.getElementById("load-resumes");
if (loadResumesBtn) {
  loadResumesBtn.addEventListener("click", async () => {
    const jobId = document.getElementById("resumes-job-id").value;
    if (!jobId) return;
    try {
      const data = await apiRequest(`/jobs/${jobId}/resumes`, { headers: { ...authHeaders() } });
      lastResumes = data;
      renderResumesTable(data);
      const thresholdInput = document.getElementById("shortlist-threshold");
      const threshold = thresholdInput ? Number(thresholdInput.value || 0) : 0;
      renderShortlist(data, threshold);
    } catch (err) {
      const status = document.getElementById("screen-result");
      if (status) setStatus(status, err.message, false);
    }
  });
}

const buildShortlistBtn = document.getElementById("build-shortlist");
if (buildShortlistBtn) {
  buildShortlistBtn.addEventListener("click", () => {
    const thresholdInput = document.getElementById("shortlist-threshold");
    const threshold = thresholdInput ? Number(thresholdInput.value || 0) : 0;
    const shortlisted = lastResumes.filter(resume => (resume.score || 0) >= threshold);
    renderShortlist(lastResumes, threshold);
    localStorage.setItem("shortlistedCandidates", JSON.stringify(shortlisted));
    const jobId = document.getElementById("resumes-job-id").value;
    localStorage.setItem("currentJobId", jobId);
    if (shortlisted.length === 0) {
      alert("No candidates met the shortlist threshold.");
      return;
    }
    const uniqueCandidates = [...new Set(shortlisted.map(r => r.file_name))];
    alert(`${uniqueCandidates.length} unique candidate(s) shortlisted.`);
    window.location.href = "/video.html";
  });
}

const videoForm = document.getElementById("video-form");
if (videoForm) {
  videoForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      candidate_email: videoForm.candidateEmail.value,
      scheduled_at: videoForm.scheduledAt.value || null,
    };
    const jobId = videoForm.jobId.value;
    const result = document.getElementById("video-result");
    try {
      const data = await apiRequest(`/jobs/${jobId}/video-invite`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify(payload),
      });
      setStatus(result, `Invite sent. Meet: ${data.meet_link}`);
    } catch (err) {
      setStatus(result, err.message, false);
    }
  });
}

const logoutBtn = document.getElementById("logout-btn");
if (logoutBtn) {
  logoutBtn.addEventListener("click", async () => {
    const result = document.getElementById("logout-result");
    try {
      await apiRequest("/auth/logout", { method: "POST", headers: { ...authHeaders() } });
    } catch (err) {
      setStatus(result, err.message, false);
    }
    localStorage.removeItem("token");
    setStatus(result, "Logged out.");
  });
}

const refreshJobsBtn = document.getElementById("refresh-jobs");
if (refreshJobsBtn) {
  refreshJobsBtn.addEventListener("click", async () => {
    await loadJobsOptions();
  });
}

loadJobsOptions();

const shortlistedTable = document.getElementById("shortlisted-table");
if (shortlistedTable) {
  const shortlisted = JSON.parse(localStorage.getItem("shortlistedCandidates") || "[]");
  shortlistedTable.innerHTML = "";
  if (!shortlisted.length) {
    shortlistedTable.innerHTML = `<tr><td colspan="4">No shortlisted candidates found.</td></tr>`;
  } else {
    shortlisted.forEach(candidate => {
      shortlistedTable.innerHTML += `
        <tr>
          <td>${candidate.file_name}</td>
          <td>${candidate.candidate_email || "No Email"}</td>
          <td>${candidate.score}</td>
          <td>Shortlisted</td>
        </tr>
      `;
    });
  }
}

// ✅ FIXED: Added missing declaration
const sendAllInvites = document.getElementById("send-all-invites");

if (sendAllInvites) {

  sendAllInvites.addEventListener(
    "click",
    async () => {

      const shortlisted =
        JSON.parse(
          localStorage.getItem(
            "shortlistedCandidates"
          ) || "[]"
        );

      const jobId =
        localStorage.getItem(
          "currentJobId"
        );

      const meetLink =
        document.getElementById(
          "meet-link"
        ).value.trim();

      const scheduledAt =
        document.getElementById(
          "scheduled-at"
        ).value;

      if (!meetLink) {
        alert("Please enter Google Meet Link");
        return;
      }

      if (!scheduledAt) {
        alert("Please select interview date & time");
        return;
      }

      let sent = 0;

      for (const candidate of shortlisted) {

        if (!candidate.candidate_email)
          continue;

        try {

          await apiRequest(
            `/jobs/${jobId}/video-invite`,
            {
              method: "POST",

              headers: {
                "Content-Type":
                  "application/json",
                ...authHeaders()
              },

              body: JSON.stringify({

                candidate_email:
                  candidate.candidate_email,

                scheduled_at:
                  scheduledAt,

                meet_link:
                  meetLink

              }),
            }
          );

          sent++;

        } catch (err) {

          console.error(
            "Invite failed:",
            candidate.candidate_email,
            err
          );

        }
      }

      alert(
        `${sent} interview invitation(s) sent successfully.`
      );
    }
  );
}

const verifyBtn = document.getElementById("verify-documents");
if (verifyBtn) {
  verifyBtn.addEventListener("click", async () => {
    const aadharFile = document.getElementById("aadhar-file").files[0];
    const panFile = document.getElementById("pan-file").files[0];
    const marksheet10File = document.getElementById("marksheet10-file").files[0];
    const marksheet12File = document.getElementById("marksheet12-file").files[0];

    const documentStatus = document.getElementById("document-status");
    const verificationOutput = document.getElementById("verification-output");

    if (!aadharFile || !panFile || !marksheet10File || !marksheet12File) {
      alert("Please upload all documents.");
      return;
    }

    if (documentStatus) documentStatus.textContent = "Verifying... please wait.";
    if (verificationOutput) verificationOutput.textContent = "Processing...";

    const formData = new FormData();
    formData.append("aadhar_number", document.getElementById("aadhar-number").value.trim());
    formData.append("pan_number", document.getElementById("pan-number").value.trim().toUpperCase());
    formData.append("aadhar_file", aadharFile);
    formData.append("pan_file", panFile);
    formData.append("marksheet_10_file", marksheet10File);
    formData.append("marksheet_12_file", marksheet12File);

    try {
      const response = await fetch("/users/documents", {
        method: "POST",
        headers: { ...authHeaders() },
        body: formData,
      });

      const text = await response.text();
      console.log("Verification raw response:", text);

      if (!response.ok) {
        if (documentStatus) documentStatus.textContent = "Verification request failed.";
        if (verificationOutput) verificationOutput.innerHTML = `<span style="color:red">Error: ${text}</span>`;
        return;
      }

      let data;
      try {
        data = JSON.parse(text);
      } catch {
        if (documentStatus) documentStatus.textContent = "Unexpected server response.";
        if (verificationOutput) verificationOutput.innerHTML = `<span style="color:orange">Raw response: ${text}</span>`;
        return;
      }

      if (documentStatus) documentStatus.textContent = "Verification complete.";

      if (verificationOutput) {
        const overallOk = data.overall === "verified" || data.overall === true || data.overall === "true";
        verificationOutput.innerHTML = `
          <div><strong>Aadhaar:</strong> ${data.aadhar ?? "N/A"}</div>
          <div><strong>PAN:</strong> ${data.pan ?? "N/A"}</div>
          <div style="margin-top:8px;font-size:1.1em;">
            <strong>Overall:</strong>
            <span style="color:${overallOk ? "green" : "red"}; font-weight:700;">
              ${data.overall ?? "N/A"}
            </span>
          </div>
        `;
      }

    } catch (err) {
      console.error("Verification error:", err);
      if (documentStatus) documentStatus.textContent = "Verification failed.";
      if (verificationOutput) verificationOutput.innerHTML = `<span style="color:red">Error: ${err.message}</span>`;
    }
  });
}