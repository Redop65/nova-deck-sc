const state = { pages: [], activePage: null, forceTestMode: false, editingId: null };
const colors = new Set(["cyan", "blue", "violet", "amber", "orange", "green", "red"]);

const grid = document.querySelector("#button-grid");
const nav = document.querySelector("#page-nav");
const title = document.querySelector("#page-title");
const testToggle = document.querySelector("#test-mode");
const log = document.querySelector("#command-log");
const logText = document.querySelector("#log-text");
const toast = document.querySelector("#toast");
const deckView = document.querySelector("#deck-view");
const editorView = document.querySelector("#editor-view");
const editorList = document.querySelector("#editor-list");
const buttonForm = document.querySelector("#button-form");
const formMessage = document.querySelector("#form-message");
const deleteButton = document.querySelector("#delete-button");
const deleteConfirm = document.querySelector("#delete-confirm");

document.querySelector("#open-editor").addEventListener("click", () => setEditorMode(true));
document.querySelector("#close-editor").addEventListener("click", () => setEditorMode(false));
document.querySelector("#new-button").addEventListener("click", startNewButton);
deleteButton.addEventListener("click", () => { deleteConfirm.hidden = false; });
document.querySelector("#cancel-delete").addEventListener("click", () => { deleteConfirm.hidden = true; });
document.querySelector("#confirm-delete").addEventListener("click", deleteCurrentButton);
buttonForm.addEventListener("submit", saveButton);
document.querySelector("#field-name").addEventListener("input", (event) => {
  const idField = document.querySelector("#field-id");
  if (state.editingId === null && !idField.dataset.manual) idField.value = slugify(event.target.value);
});
document.querySelector("#field-id").addEventListener("input", (event) => {
  event.target.dataset.manual = event.target.value ? "true" : "";
});

testToggle.checked = localStorage.getItem("nova-deck-test") === "true";
testToggle.addEventListener("change", () => {
  localStorage.setItem("nova-deck-test", testToggle.checked);
  writeLog(testToggle.checked ? "TEST MODE ENABLED // KEY OUTPUT BLOCKED" : "LIVE MODE ENABLED // KEY OUTPUT ARMED");
});

function writeLog(message, type = "") {
  log.className = `command-log ${type}`;
  logText.textContent = message;
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2800);
}

function setConnection(kind, text) {
  const wrapper = document.querySelector(".system-state");
  wrapper.className = `system-state ${kind}`;
  document.querySelector("#status-text").textContent = text;
}

function renderNav() {
  nav.replaceChildren(...state.pages.map((page) => {
    const button = document.createElement("button");
    button.className = `nav-button ${page.id === state.activePage ? "active" : ""}`;
    button.type = "button";
    const icon = document.createElement("span");
    icon.textContent = page.icon || "·";
    button.append(icon, document.createTextNode(page.name));
    button.addEventListener("click", () => selectPage(page.id));
    return button;
  }));
}

function selectPage(pageId) {
  state.activePage = pageId;
  const page = state.pages.find((item) => item.id === pageId);
  if (!page) return;
  title.textContent = page.name;
  grid.classList.toggle("flight-compact", page.id === "flight");
  grid.replaceChildren(...page.buttons.map(createDeckButton));
  renderNav();
}

function setEditorMode(enabled) {
  document.body.classList.toggle("editing", enabled);
  deckView.hidden = enabled;
  editorView.hidden = !enabled;
  document.querySelector("#open-editor").classList.toggle("active", enabled);
  if (enabled) {
    renderEditorList();
    if (state.editingId === null) startNewButton();
  }
}

function slugify(value) {
  return value.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}

function populatePageSelect(selectedPage) {
  const select = document.querySelector("#field-page");
  select.replaceChildren(...state.pages.map((page) => {
    const option = document.createElement("option");
    option.value = page.id;
    option.textContent = page.name;
    option.selected = page.id === selectedPage;
    return option;
  }));
}

function renderEditorList() {
  editorList.replaceChildren(...state.pages.map((page) => {
    const group = document.createElement("section");
    group.className = "catalogue-group";
    const heading = document.createElement("h3");
    heading.textContent = `${page.icon || "·"} ${page.name}`;
    group.append(heading);
    for (const item of page.buttons) {
      const row = document.createElement("button");
      row.type = "button";
      row.className = `catalogue-item ${item.id === state.editingId ? "active" : ""}`;
      row.setAttribute("aria-label", `Editar ${item.name}`);
      const name = document.createElement("span");
      name.textContent = item.name;
      const keys = document.createElement("code");
      keys.textContent = item.keys;
      row.append(name, keys);
      row.addEventListener("click", () => editButton(page.id, item));
      group.append(row);
    }
    return group;
  }));
}

function startNewButton() {
  state.editingId = null;
  buttonForm.reset();
  document.querySelector("#field-id").dataset.manual = "";
  populatePageSelect(state.activePage || state.pages[0]?.id);
  document.querySelector("#form-title").textContent = "New Button";
  document.querySelector("#form-state").textContent = "NEW";
  deleteButton.hidden = true;
  deleteConfirm.hidden = true;
  setFormMessage("");
  renderEditorList();
  document.querySelector("#field-name").focus();
}

function editButton(pageId, item) {
  state.editingId = item.id;
  document.querySelector("#field-name").value = item.name;
  document.querySelector("#field-id").value = item.id;
  document.querySelector("#field-id").dataset.manual = "true";
  document.querySelector("#field-keys").value = item.keys;
  document.querySelector("#field-hold").value = Number(item.hold_ms) || 0;
  document.querySelector("#field-icon").value = item.icon || "";
  document.querySelector("#field-color").value = colors.has(item.color) ? item.color : "cyan";
  document.querySelector("#field-disabled").checked = Boolean(item.disabled);
  populatePageSelect(pageId);
  document.querySelector("#form-title").textContent = item.name;
  document.querySelector("#form-state").textContent = "EDITING";
  deleteButton.hidden = false;
  deleteConfirm.hidden = true;
  setFormMessage("");
  renderEditorList();
}

function formPayload() {
  const icon = document.querySelector("#field-icon").value.trim();
  return {
    page_id: document.querySelector("#field-page").value,
    button: {
      id: document.querySelector("#field-id").value.trim(),
      name: document.querySelector("#field-name").value.trim(),
      keys: document.querySelector("#field-keys").value.trim(),
      hold_ms: Number.parseInt(document.querySelector("#field-hold").value, 10) || 0,
      icon: icon || null,
      color: document.querySelector("#field-color").value,
      disabled: document.querySelector("#field-disabled").checked,
    },
  };
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const body = await response.json();
  if (!response.ok) {
    const detail = Array.isArray(body.detail) ? body.detail.map((item) => item.msg).join("; ") : body.detail;
    throw new Error(detail || `HTTP ${response.status}`);
  }
  return body;
}

async function reloadConfiguration() {
  const config = await requestJson("/api/buttons");
  state.pages = config.pages;
  if (!state.pages.some((page) => page.id === state.activePage)) state.activePage = state.pages[0].id;
  selectPage(state.activePage);
  renderEditorList();
}

async function saveButton(event) {
  event.preventDefault();
  const payload = formPayload();
  const originalId = state.editingId;
  const url = originalId === null ? "/api/buttons" : `/api/buttons/${encodeURIComponent(originalId)}`;
  const method = originalId === null ? "POST" : "PUT";
  setFormMessage("SAVING // WRITING CONFIG...", "");
  try {
    const result = await requestJson(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    state.editingId = result.button.id;
    await reloadConfiguration();
    const page = state.pages.find((candidate) => candidate.id === payload.page_id);
    const saved = page?.buttons.find((candidate) => candidate.id === result.button.id);
    if (saved) editButton(page.id, saved);
    setFormMessage(`SAVED // ${result.button.id} // CONFIG UPDATED`);
    showToast("Button saved to config/buttons.json");
  } catch (error) {
    setFormMessage(`ERROR // ${error.message}`, "error");
  }
}

async function deleteCurrentButton() {
  if (state.editingId === null) return;
  const id = state.editingId;
  try {
    await requestJson(`/api/buttons/${encodeURIComponent(id)}`, { method: "DELETE" });
    state.editingId = null;
    await reloadConfiguration();
    startNewButton();
    setFormMessage(`DELETED // ${id} // CONFIG UPDATED`);
    showToast("Button deleted from config/buttons.json");
  } catch (error) {
    deleteConfirm.hidden = true;
    setFormMessage(`ERROR // ${error.message}`, "error");
  }
}

function setFormMessage(message, type = "") {
  formMessage.textContent = message;
  formMessage.className = `form-message ${type}`;
}

function createDeckButton(item, index) {
  const button = document.createElement("button");
  const color = colors.has(item.color) ? item.color : "cyan";
  button.className = `deck-button ${color}`;
  button.type = "button";
  button.disabled = Boolean(item.disabled);
  button.dataset.index = String(index + 1).padStart(2, "0");
  button.title = item.disabled ? "Configura una tecla válida para habilitar esta acción" : item.name;

  const icon = document.createElement("span");
  icon.className = "key-icon";
  icon.textContent = item.icon || "◇";
  const name = document.createElement("span");
  name.className = "key-name";
  name.textContent = item.name;
  const binding = document.createElement("span");
  binding.className = "key-binding";
  const holdMs = Number(item.hold_ms) || 0;
  const holdLabel = holdMs > 0 ? ` · HOLD ${(holdMs / 1000).toFixed(1)}S` : "";
  binding.textContent = item.disabled ? `${item.keys} // DISABLED` : `${item.keys}${holdLabel}`;
  button.append(icon, name, binding);
  button.addEventListener("click", () => sendCommand(item, button));
  return button;
}

async function sendCommand(item, element) {
  element.classList.add("firing");
  navigator.vibrate?.(25);
  writeLog(`TX // ${item.name.toUpperCase()} [${item.keys}]`);
  try {
    const response = await fetch("/api/commands", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ button_id: item.id, test_mode: testToggle.checked }),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || `HTTP ${response.status}`);
    const mode = body.test_mode ? "SIMULATED" : "SENT";
    const hold = body.hold_ms > 0 ? ` // HOLD ${body.hold_ms}MS` : "";
    writeLog(`ACK // ${body.button.toUpperCase()} // ${body.keys}${hold} // ${mode}`, "success");
  } catch (error) {
    writeLog(`ERROR // ${error.message}`, "error");
    showToast(error.message);
  } finally {
    setTimeout(() => element.classList.remove("firing"), 140);
  }
}

async function boot() {
  try {
    const [buttonsResponse, statusResponse] = await Promise.all([fetch("/api/buttons"), fetch("/api/status")]);
    if (!buttonsResponse.ok || !statusResponse.ok) throw new Error("El servidor no respondió correctamente.");
    const config = await buttonsResponse.json();
    const status = await statusResponse.json();
    state.pages = config.pages;
    state.forceTestMode = status.force_test_mode;
    document.querySelector("#deck-title").textContent = config.title || "NOVA DECK // SC";
    if (state.forceTestMode) {
      testToggle.checked = true;
      testToggle.disabled = true;
      writeLog("SERVER TEST MODE // KEY OUTPUT HARD-LOCKED");
    }
    setConnection("online", state.forceTestMode ? "TEST LOCK" : "SYSTEM ONLINE");
    selectPage(state.pages[0].id);
  } catch (error) {
    setConnection("error", "OFFLINE");
    writeLog(`BOOT ERROR // ${error.message}`, "error");
    showToast(error.message);
  }
}

boot();
