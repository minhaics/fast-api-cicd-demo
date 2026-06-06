const notesEl = document.querySelector("#notes");
const formEl = document.querySelector("#note-form");
const titleEl = document.querySelector("#title");
const contentEl = document.querySelector("#content");
const statusEl = document.querySelector("#status");

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

function renderNotes(notes) {
  if (notes.length === 0) {
    notesEl.innerHTML = '<p class="empty">Chua co ghi chu nao.</p>';
    return;
  }

  notesEl.innerHTML = notes
    .map(
      (note) => `
        <article class="note ${note.completed ? "done" : ""}">
          <div class="note-title">
            <h2>${escapeHtml(note.title)}</h2>
            <small>#${note.id}</small>
          </div>
          <p>${escapeHtml(note.content || "")}</p>
          <div class="actions">
            <button class="secondary" data-action="toggle" data-id="${note.id}" data-completed="${note.completed}">
              ${note.completed ? "Mo lai" : "Hoan thanh"}
            </button>
            <button class="secondary" data-action="delete" data-id="${note.id}">Xoa</button>
          </div>
        </article>
      `
    )
    .join("");
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (char) => {
    const entities = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    };
    return entities[char];
  });
}

async function loadNotes() {
  const notes = await api("/api/notes");
  renderNotes(notes);
}

async function checkHealth() {
  try {
    await api("/health");
    statusEl.textContent = "api ok";
    statusEl.classList.add("ok");
  } catch {
    statusEl.textContent = "api error";
    statusEl.classList.remove("ok");
  }
}

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  await api("/api/notes", {
    method: "POST",
    body: JSON.stringify({
      title: titleEl.value.trim(),
      content: contentEl.value.trim(),
    }),
  });
  formEl.reset();
  await loadNotes();
});

notesEl.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button) return;

  const id = button.dataset.id;
  if (button.dataset.action === "delete") {
    await api(`/api/notes/${id}`, { method: "DELETE" });
  }

  if (button.dataset.action === "toggle") {
    await api(`/api/notes/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ completed: button.dataset.completed !== "true" }),
    });
  }

  await loadNotes();
});

checkHealth();
loadNotes();
