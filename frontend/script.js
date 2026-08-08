/**
 * TaskFlow — script.js
 *
 * Rules followed:
 *  - DOM built with document.createElement / appendChild (never innerHTML for user data)
 *  - textContent used for all user-supplied text values
 *  - Every interactive control uses addEventListener (no inline onclick)
 *  - add-task form uses event.preventDefault()
 *  - Client-side validation: empty title shows error message
 *  - localStorage cache: written on every change, read on page load before fetch
 *  - All data ultimately comes from / goes to the real FastAPI backend
 */

const API = "http://127.0.0.1:8000";

// ---- State ----------------------------------------------------------------
let currentProjectId = null;
let currentUserId    = null;
let taskCache        = [];          // in-memory mirror of what's on screen

// ---- localStorage helpers -------------------------------------------------
const LS_USER_KEY    = "tf_user_id";
const LS_PROJECT_KEY = "tf_project_id";
const LS_TASKS_KEY   = "tf_tasks_cache";

function saveTasks(tasks) {
  taskCache = tasks;
  localStorage.setItem(LS_TASKS_KEY, JSON.stringify(tasks));
}

function loadCachedTasks() {
  try {
    const raw = localStorage.getItem(LS_TASKS_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (_) {
    return [];
  }
}

// ---- DOM references -------------------------------------------------------
const projectSelect   = document.getElementById("projectSelect");
const newProjectBtn   = document.getElementById("newProjectBtn");
const newProjectForm  = document.getElementById("newProjectForm");
const projNameInput   = document.getElementById("projNameInput");
const projOwnerInput  = document.getElementById("projOwnerInput");
const cancelProjBtn   = document.getElementById("cancelProjectBtn");
const projError       = document.getElementById("projError");
const statsBtn        = document.getElementById("statsBtn");
const statsPanel      = document.getElementById("statsPanel");
const statsContent    = document.getElementById("statsContent");

const taskForm        = document.getElementById("taskForm");
const taskTitle       = document.getElementById("taskTitle");
const taskPriority    = document.getElementById("taskPriority");
const taskDueDate     = document.getElementById("taskDueDate");
const taskStatus      = document.getElementById("taskStatus");
const titleError      = document.getElementById("titleError");

const quickAddForm    = document.getElementById("quickAddForm");
const quickAddInput   = document.getElementById("quickAddInput");
const quickAddError   = document.getElementById("quickAddError");

const searchInput     = document.getElementById("searchInput");
const searchBtn       = document.getElementById("searchBtn");
const sortSelect      = document.getElementById("sortSelect");
const sortBtn         = document.getElementById("sortBtn");
const refreshBtn      = document.getElementById("refreshBtn");
const taskList        = document.getElementById("taskList");
const listStatus      = document.getElementById("listStatus");

const editModal       = document.getElementById("editModal");
const editForm        = document.getElementById("editForm");
const editTitle       = document.getElementById("editTitle");
const editPriority    = document.getElementById("editPriority");
const editDueDate     = document.getElementById("editDueDate");
const editStatus      = document.getElementById("editStatus");
const editTaskId      = document.getElementById("editTaskId");
const editTitleError  = document.getElementById("editTitleError");
const cancelEditBtn   = document.getElementById("cancelEditBtn");

const userModal       = document.getElementById("userModal");
const userForm        = document.getElementById("userForm");
const userName        = document.getElementById("userName");
const userEmail       = document.getElementById("userEmail");
const userError       = document.getElementById("userError");

// ---- Utility: fetch wrapper ------------------------------------------------
async function apiFetch(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw Object.assign(new Error(err.detail || res.statusText), { status: res.status });
  }
  return res.json();
}

// ---- Render helpers -------------------------------------------------------
function setStatus(msg) {
  listStatus.textContent = msg;
}

function clearError(el) { el.textContent = ""; }

function showError(el, msg) { el.textContent = msg; }

/** Render a priority badge using createElement (safe, no innerHTML). */
function makeBadge(text, cssClass) {
  const span = document.createElement("span");
  span.className = `badge ${cssClass}`;
  span.textContent = text;
  return span;
}

/** Build a single <li> task item via DOM methods. */
function buildTaskElement(task) {
  const li = document.createElement("li");
  li.className = `task-item priority-${task.priority}`;
  li.dataset.id = task.id;

  // Body
  const body = document.createElement("div");
  body.className = "task-body";

  const titleEl = document.createElement("p");
  titleEl.className = "task-title";
  titleEl.textContent = task.title;           // textContent — never innerHTML
  body.appendChild(titleEl);

  const meta = document.createElement("div");
  meta.className = "task-meta";
  meta.appendChild(makeBadge(task.priority, `badge-priority-${task.priority}`));
  meta.appendChild(makeBadge(task.status.replace("_", " "), `badge-status-${task.status}`));

  if (task.due_date) {
    const due = document.createElement("span");
    due.className = "task-due";
    due.textContent = "Due: " + task.due_date;   // textContent
    meta.appendChild(due);
  }
  body.appendChild(meta);
  li.appendChild(body);

  // Actions
  const actions = document.createElement("div");
  actions.className = "task-actions";

  const editBtn = document.createElement("button");
  editBtn.className = "btn-edit";
  editBtn.textContent = "Edit";
  editBtn.addEventListener("click", () => openEditModal(task));   // addEventListener

  const delBtn = document.createElement("button");
  delBtn.className = "btn-danger";
  delBtn.textContent = "Delete";
  delBtn.addEventListener("click", () => deleteTask(task.id));    // addEventListener

  actions.appendChild(editBtn);
  actions.appendChild(delBtn);
  li.appendChild(actions);

  return li;
}

/** Replace the task list DOM from an array of task objects. */
function renderTasks(tasks) {
  while (taskList.firstChild) taskList.removeChild(taskList.firstChild);
  if (!tasks.length) {
    const empty = document.createElement("li");
    empty.textContent = "No tasks yet. Add one above.";
    empty.style.color = "var(--text-muted)";
    empty.style.padding = "1rem 0";
    taskList.appendChild(empty);
    return;
  }
  tasks.forEach(t => taskList.appendChild(buildTaskElement(t)));
}

// ---- Data loaders ---------------------------------------------------------
async function loadProjects() {
  try {
    const projects = await apiFetch("/projects");
    while (projectSelect.options.length > 1) projectSelect.remove(1);
    projects.forEach(p => {
      const opt = document.createElement("option");
      opt.value = p.id;
      opt.textContent = p.name;                  // textContent
      projectSelect.appendChild(opt);
    });

    // Restore last selected project
    const saved = localStorage.getItem(LS_PROJECT_KEY);
    if (saved) {
      projectSelect.value = saved;
      if (projectSelect.value) {
        currentProjectId = parseInt(saved, 10);
        await loadTasks();
      }
    }
  } catch (e) {
    setStatus("Could not load projects: " + e.message);
  }
}

async function loadTasks(sortBy = null) {
  if (!currentProjectId) { setStatus("Select a project first."); return; }

  // Render cached copy immediately so the page isn't blank while fetching
  const cached = loadCachedTasks();
  if (cached.length) {
    renderTasks(cached);
    setStatus("Loading fresh data…");
  }

  try {
    let path = `/tasks?project_id=${currentProjectId}`;
    if (sortBy) path += `&sort=${sortBy}`;
    const tasks = await apiFetch(path);
    saveTasks(tasks);
    renderTasks(tasks);
    setStatus(`${tasks.length} task(s) in this project.`);
  } catch (e) {
    setStatus("Error loading tasks: " + e.message);
  }
}

// ---- User bootstrap -------------------------------------------------------
async function bootstrapUser() {
  const saved = localStorage.getItem(LS_USER_KEY);
  if (saved) {
    currentUserId = parseInt(saved, 10);
    // Pre-fill owner field
    projOwnerInput.value = currentUserId;
    userModal.classList.add("hidden");
    await loadProjects();
    return;
  }
  // Show creation modal
  userModal.classList.remove("hidden");
}

userForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  clearError(userError);
  const name  = userName.value.trim();
  const email = userEmail.value.trim();
  if (!name || !email) { showError(userError, "Both fields required."); return; }
  try {
    const user = await apiFetch("/users", {
      method: "POST",
      body: JSON.stringify({ name, email }),
    });
    currentUserId = user.id;
    localStorage.setItem(LS_USER_KEY, currentUserId);
    projOwnerInput.value = currentUserId;
    userModal.classList.add("hidden");
    await loadProjects();
  } catch (err) {
    showError(userError, err.message);
  }
});

// ---- Project controls -----------------------------------------------------
projectSelect.addEventListener("change", async () => {
  currentProjectId = projectSelect.value ? parseInt(projectSelect.value, 10) : null;
  if (currentProjectId) {
    localStorage.setItem(LS_PROJECT_KEY, currentProjectId);
    saveTasks([]);      // clear old cache
    await loadTasks();
  } else {
    renderTasks([]);
    setStatus("");
  }
});

newProjectBtn.addEventListener("click", () => {
  newProjectForm.classList.toggle("hidden");
});

cancelProjBtn.addEventListener("click", () => {
  newProjectForm.classList.add("hidden");
  clearError(projError);
});

newProjectForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  clearError(projError);
  const name    = projNameInput.value.trim();
  const ownerId = parseInt(projOwnerInput.value, 10);
  if (!name) { showError(projError, "Project name is required."); return; }
  if (!ownerId) { showError(projError, "Owner ID is required."); return; }
  try {
    const proj = await apiFetch("/projects", {
      method: "POST",
      body: JSON.stringify({ name, owner_id: ownerId }),
    });
    const opt = document.createElement("option");
    opt.value = proj.id;
    opt.textContent = proj.name;              // textContent
    projectSelect.appendChild(opt);
    projectSelect.value = proj.id;
    currentProjectId = proj.id;
    localStorage.setItem(LS_PROJECT_KEY, proj.id);
    newProjectForm.classList.add("hidden");
    projNameInput.value = "";
    saveTasks([]);
    await loadTasks();
  } catch (err) {
    showError(projError, err.message);
  }
});

// ---- Stats ----------------------------------------------------------------
statsBtn.addEventListener("click", async () => {
  if (!currentProjectId) { alert("Select a project first."); return; }
  statsPanel.classList.toggle("hidden");
  if (statsPanel.classList.contains("hidden")) return;

  try {
    const data = await apiFetch(`/projects/${currentProjectId}/stats`);
    while (statsContent.firstChild) statsContent.removeChild(statsContent.firstChild);

    const grid = document.createElement("div");
    grid.className = "stats-grid";

    // Total card
    const total = document.createElement("div");
    total.className = "stat-card";
    const tv = document.createElement("div");
    tv.className = "stat-value";
    tv.textContent = data.total_tasks;
    const tl = document.createElement("div");
    tl.className = "stat-label";
    tl.textContent = "Total Tasks";
    total.appendChild(tv);
    total.appendChild(tl);
    grid.appendChild(total);

    // Per-status cards
    data.by_status.forEach(s => {
      const card = document.createElement("div");
      card.className = "stat-card";
      const sv = document.createElement("div");
      sv.className = "stat-value";
      sv.textContent = s.count;
      const sl = document.createElement("div");
      sl.className = "stat-label";
      sl.textContent = s.status.replace("_", " ");   // textContent
      card.appendChild(sv);
      card.appendChild(sl);
      grid.appendChild(card);
    });

    statsContent.appendChild(grid);
  } catch (err) {
    statsContent.textContent = "Error loading stats: " + err.message;
  }
});

// ---- Add task form --------------------------------------------------------
taskForm.addEventListener("submit", async (e) => {
  e.preventDefault();     // required by spec
  clearError(titleError);

  const title = taskTitle.value.trim();
  if (!title) {
    // Client-side validation: show error message, do NOT submit
    showError(titleError, "Title must not be empty.");
    return;
  }
  if (!currentProjectId) { showError(titleError, "Select a project first."); return; }

  try {
    const task = await apiFetch("/tasks", {
      method: "POST",
      body: JSON.stringify({
        title,
        priority: taskPriority.value,
        due_date: taskDueDate.value.trim() || null,
        status:   taskStatus.value,
        project_id: currentProjectId,
      }),
    });
    taskTitle.value = "";
    taskDueDate.value = "";
    // Update cache and re-render
    const updated = [task, ...taskCache];
    saveTasks(updated);
    renderTasks(updated);
    setStatus(`${updated.length} task(s) in this project.`);
  } catch (err) {
    showError(titleError, err.message);
  }
});

// Clear error when user types
taskTitle.addEventListener("input", () => {
  if (taskTitle.value.trim()) clearError(titleError);
});

// ---- Quick-add form -------------------------------------------------------
quickAddForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  clearError(quickAddError);

  const desc = quickAddInput.value.trim();
  if (!desc) { showError(quickAddError, "Description must not be empty."); return; }
  if (!currentProjectId) { showError(quickAddError, "Select a project first."); return; }

  try {
    const task = await apiFetch("/tasks/quick-add", {
      method: "POST",
      body: JSON.stringify({ description: desc, project_id: currentProjectId }),
    });
    quickAddInput.value = "";
    const updated = [task, ...taskCache];
    saveTasks(updated);
    renderTasks(updated);
    setStatus(`Task "${task.title}" added via AI Quick-Add.`);
  } catch (err) {
    showError(quickAddError, err.message);
  }
});

quickAddInput.addEventListener("input", () => {
  if (quickAddInput.value.trim()) clearError(quickAddError);
});

// ---- Sort & Search --------------------------------------------------------
sortBtn.addEventListener("click", async () => {
  const sortBy = sortSelect.value;
  if (!sortBy) { setStatus("Pick a sort field."); return; }
  await loadTasks(sortBy);
});

searchBtn.addEventListener("click", async () => {
  const q = searchInput.value.trim();
  if (!q) { setStatus("Enter a title to search."); return; }
  if (!currentProjectId) { setStatus("Select a project first."); return; }

  try {
    const task = await apiFetch(
      `/tasks/search?title=${encodeURIComponent(q)}&algo=binary&project_id=${currentProjectId}`
    );
    saveTasks([task]);
    renderTasks([task]);
    setStatus(`Found: "${task.title}"`);
  } catch (err) {
    if (err.status === 404) {
      renderTasks([]);
      setStatus(`No task found with title "${q}".`);
    } else {
      setStatus("Search error: " + err.message);
    }
  }
});

refreshBtn.addEventListener("click", () => loadTasks());

// ---- Edit modal -----------------------------------------------------------
function openEditModal(task) {
  editTaskId.value    = task.id;
  editTitle.value     = task.title;
  editPriority.value  = task.priority;
  editDueDate.value   = task.due_date || "";
  editStatus.value    = task.status;
  clearError(editTitleError);
  editModal.classList.remove("hidden");
}

cancelEditBtn.addEventListener("click", () => {
  editModal.classList.add("hidden");
});

// Close modal when clicking outside the box
editModal.addEventListener("click", (e) => {
  if (e.target === editModal) editModal.classList.add("hidden");
});

editForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  clearError(editTitleError);

  const title = editTitle.value.trim();
  if (!title) { showError(editTitleError, "Title must not be empty."); return; }

  const id = parseInt(editTaskId.value, 10);
  try {
    const updated = await apiFetch(`/tasks/${id}`, {
      method: "PUT",
      body: JSON.stringify({
        title,
        priority: editPriority.value,
        due_date: editDueDate.value.trim() || null,
        status:   editStatus.value,
      }),
    });
    editModal.classList.add("hidden");

    // Update cache entry
    const newCache = taskCache.map(t => t.id === id ? updated : t);
    saveTasks(newCache);
    renderTasks(newCache);
    setStatus("Task updated.");
  } catch (err) {
    showError(editTitleError, err.message);
  }
});

// ---- Delete ---------------------------------------------------------------
async function deleteTask(id) {
  if (!confirm("Delete this task?")) return;
  try {
    await apiFetch(`/tasks/${id}`, { method: "DELETE" });
    const newCache = taskCache.filter(t => t.id !== id);
    saveTasks(newCache);
    renderTasks(newCache);
    setStatus(`Task deleted. ${newCache.length} task(s) remaining.`);
  } catch (err) {
    setStatus("Delete failed: " + err.message);
  }
}

// ---- Bootstrap ------------------------------------------------------------
bootstrapUser();
