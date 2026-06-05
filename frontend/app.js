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

function authHeaders() {
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
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      setToken(data.access_token);

      setStatus(
        result,
        "Login successful. Redirecting..."
      );

      setTimeout(() => {
        window.location.href = "/jobs.html";
      }, 1000);

    } catch (err) {
      setStatus(
        result,
        err.message,
        false
      );
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
      const data = await apiRequest("/jobs", {
        headers: { ...authHeaders() },
      });
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
      const data = await apiRequest("/users/onboarded", {
        headers: { ...authHeaders() },
      });
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
    if (!jobId) {
      return;
    }
    try {
      const data = await apiRequest(`/jobs/${jobId}/resumes`, {
        headers: { ...authHeaders() },
      });
      lastResumes = data;
      renderResumesTable(data);
      const thresholdInput = document.getElementById("shortlist-threshold");
      const threshold = thresholdInput ? Number(thresholdInput.value || 0) : 0;
      renderShortlist(data, threshold);
    } catch (err) {
      const status = document.getElementById("screen-result");
      if (status) {
        setStatus(status, err.message, false);
      }
    }
  });
}

const buildShortlistBtn = document.getElementById("build-shortlist");

if (buildShortlistBtn) {
  buildShortlistBtn.addEventListener("click", () => {

    const thresholdInput =
      document.getElementById("shortlist-threshold");

    const threshold =
      thresholdInput
        ? Number(thresholdInput.value || 0)
        : 0;

    const shortlisted =
      lastResumes.filter(
        resume => (resume.score || 0) >= threshold
      );

    renderShortlist(lastResumes, threshold);

    localStorage.setItem(
      "shortlistedCandidates",
      JSON.stringify(shortlisted)
    );

    const jobId =
      document.getElementById("resumes-job-id").value;

    localStorage.setItem(
      "currentJobId",
      jobId
    );

if (shortlisted.length === 0) {

  alert(
    "No candidates met the shortlist threshold."
  );

  return;
}

    const uniqueCandidates =
      [...new Set(shortlisted.map(r => r.file_name))];
    
    alert(
      `${uniqueCandidates.length} unique candidate(s) shortlisted.`
    );
  
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
      await apiRequest("/auth/logout", {
        method: "POST",
        headers: { ...authHeaders() },
      });
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
