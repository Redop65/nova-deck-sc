const state = {
  profiles: [], activeProfile: "default", pages: [], activePage: null,
  forceTestMode: false, editingId: null, configWarnings: [],
};
const colors = new Set(["cyan", "blue", "violet", "amber", "orange", "green", "red"]);
const customIconPattern = /^assets\/icons\/[A-Za-z0-9][A-Za-z0-9._-]*\.(svg|png|webp|jpe?g)$/i;

const grid = document.querySelector("#button-grid");
const nav = document.querySelector("#page-nav");
const title = document.querySelector("#page-title");
const testToggle = document.querySelector("#test-mode");
const profileSelect = document.querySelector("#profile-select");
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
document.querySelector("#field-type").addEventListener("change", updateActionFields);
document.querySelector("#field-name").addEventListener("input", (event) => {
  const idField = document.querySelector("#field-id");
  if (state.editingId === null && !idField.dataset.manual) idField.value = slugify(event.target.value);
});
document.querySelector("#field-id").addEventListener("input", (event) => {
  event.target.dataset.manual = event.target.value ? "true" : "";
});
profileSelect.addEventListener("change", async () => {
  const previous = state.activeProfile;
  profileSelect.disabled = true;
  try {
    await loadProfile(profileSelect.value);
    writeLog(`PROFILE LOADED // ${profileSelect.options[profileSelect.selectedIndex].text.toUpperCase()}`);
  } catch (error) {
    profileSelect.value = previous;
    showToast(error.message);
  } finally {
    profileSelect.disabled = false;
  }
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

function renderProfileOptions() {
  profileSelect.replaceChildren(...state.profiles.map((profile) => {
    const option = document.createElement("option");
    option.value = profile.id;
    option.textContent = profile.name;
    option.selected = profile.id === state.activeProfile;
    return option;
  }));
}

async function loadProfile(profileId) {
  const result = await requestJson(`/api/profiles/${encodeURIComponent(profileId)}`);
  state.activeProfile = result.profile.id;
  state.pages = result.profile.pages;
  state.activePage = state.pages[0]?.id || null;
  state.editingId = null;
  state.configWarnings = result.warnings || [];
  localStorage.setItem("nova-deck-profile", state.activeProfile);
  renderProfileOptions();
  if (state.activePage) selectPage(state.activePage);
  showConfigurationWarnings();
}

function showConfigurationWarnings() {
  if (!state.configWarnings.length) return;
  const first = state.configWarnings[0];
  writeLog(`CONFIG WARNING // ${first.path} // ${first.message}`, "warning");
  showToast(`${state.configWarnings.length} botón(es) con error; fueron deshabilitados.`);
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

function actionType(item = {}) {
  return item.type || (item.macro ? "macro" : "hotkey");
}

function updateActionFields() {
  const type = document.querySelector("#field-type").value;
  document.querySelector(".hotkey-option").hidden = type !== "hotkey";
  document.querySelector('[data-action="macro"]').hidden = type !== "macro";
  document.querySelector('[data-action="obs"]').hidden = type !== "obs";
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
      keys.textContent = item._config_error ? "CONFIG ERROR" : (actionType(item) === "obs" ? `OBS · ${item.obsAction}` : (item.macro ? `MACRO ×${item.macro.length}` : item.keys));
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
  document.querySelector("#field-type").value = "hotkey";
  updateActionFields();
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
  document.querySelector("#field-keys").value = item.keys || "";
  document.querySelector("#field-type").value = actionType(item);
  document.querySelector("#field-hold").value = Number(item.hold_ms) || 0;
  document.querySelector("#field-macro").value = item.macro
    ? JSON.stringify(item.macro, null, 2)
    : "";
  document.querySelector("#field-icon").value = item.icon || "";
  document.querySelector("#field-color").value = colors.has(item.color) ? item.color : "cyan";
  document.querySelector("#field-disabled").checked = Boolean(item.disabled);
  document.querySelector("#field-obs-action").value = item.obsAction || "toggle_recording";
  document.querySelector("#field-scene-name").value = item.sceneName || "";
  document.querySelector("#field-input-name").value = item.inputName || "";
  document.querySelector("#field-source-name").value = item.sourceName || "";
  document.querySelector("#field-visible").value = String(item.visible ?? true);
  updateActionFields();
  populatePageSelect(pageId);
  document.querySelector("#form-title").textContent = item.name;
  document.querySelector("#form-state").textContent = "EDITING";
  deleteButton.hidden = false;
  deleteConfirm.hidden = true;
  setFormMessage("");
  renderEditorList();
}

function formPayload() {
  const type = document.querySelector("#field-type").value;
  const icon = document.querySelector("#field-icon").value.trim();
  const macroText = document.querySelector("#field-macro").value.trim();
  let macro = null;
  if (type === "macro" && macroText) {
    macro = JSON.parse(macroText);
    if (!Array.isArray(macro)) throw new Error("Macro JSON must be an array of steps.");
  }
  return {
    profile_id: state.activeProfile,
    page_id: document.querySelector("#field-page").value,
    button: {
      id: document.querySelector("#field-id").value.trim(),
      name: document.querySelector("#field-name").value.trim(),
      type,
      keys: type === "hotkey" ? document.querySelector("#field-keys").value.trim() : null,
      macro: type === "macro" ? macro : null,
      obsAction: type === "obs" ? document.querySelector("#field-obs-action").value : null,
      sceneName: type === "obs" ? document.querySelector("#field-scene-name").value.trim() || null : null,
      inputName: type === "obs" ? document.querySelector("#field-input-name").value.trim() || null : null,
      sourceName: type === "obs" ? document.querySelector("#field-source-name").value.trim() || null : null,
      visible: type === "obs" ? document.querySelector("#field-visible").value === "true" : null,
      hold_ms: Number.parseInt(document.querySelector("#field-hold").value, 10) || 0,
      icon: icon || null,
      color: document.querySelector("#field-color").value,
      disabled: document.querySelector("#field-disabled").checked,
    },
  };
}

async function requestJson(url, options = {}) {
  let response;
  try {
    response = await fetch(url, options);
  } catch (error) {
    throw new Error(`No se pudo conectar con el servidor: ${error.message}`);
  }
  const raw = await response.text();
  let body = {};
  try {
    body = raw ? JSON.parse(raw) : {};
  } catch {
    throw new Error(`El servidor respondió con un formato inesperado (HTTP ${response.status}).`);
  }
  if (!response.ok) {
    const detail = Array.isArray(body.detail) ? body.detail.map((item) => item.msg).join("; ") : body.detail;
    throw new Error(detail || `HTTP ${response.status}`);
  }
  return body;
}

async function reloadConfiguration() {
  const config = await requestJson(`/api/profiles/${encodeURIComponent(state.activeProfile)}`);
  state.pages = config.profile.pages;
  state.configWarnings = config.warnings || [];
  if (!state.pages.some((page) => page.id === state.activePage)) state.activePage = state.pages[0].id;
  selectPage(state.activePage);
  renderEditorList();
  showConfigurationWarnings();
}

async function saveButton(event) {
  event.preventDefault();
  const originalId = state.editingId;
  const url = originalId === null ? "/api/buttons" : `/api/buttons/${encodeURIComponent(originalId)}`;
  const method = originalId === null ? "POST" : "PUT";
  setFormMessage("SAVING // WRITING CONFIG...", "");
  try {
    const payload = formPayload();
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
    await requestJson(
      `/api/buttons/${encodeURIComponent(id)}?profile_id=${encodeURIComponent(state.activeProfile)}`,
      { method: "DELETE" },
    );
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
  button.title = item._config_error || (item.disabled ? "Configura una acción válida para habilitar este botón" : item.name);

  let icon = null;
  if (customIconPattern.test(item.icon || "")) {
    icon = document.createElement("span");
    icon.className = "key-icon custom-icon";
    const image = document.createElement("img");
    image.src = `/${item.icon}`;
    image.alt = "";
    image.setAttribute("aria-hidden", "true");
    image.addEventListener("error", () => {
      icon?.remove();
      button.classList.remove("has-image");
      button.classList.add("no-icon");
    }, { once: true });
    icon.append(image);
    button.classList.add("has-image");
  } else if (item.icon) {
    icon = document.createElement("span");
    icon.className = "key-icon";
    icon.textContent = item.icon;
    button.classList.add("has-symbol");
  } else {
    button.classList.add("no-icon");
  }
  const name = document.createElement("span");
  name.className = "key-name";
  name.textContent = item.name;
  const binding = document.createElement("span");
  binding.className = "key-binding";
  const holdMs = Number(item.hold_ms) || 0;
  const holdLabel = holdMs > 0 ? ` · HOLD ${(holdMs / 1000).toFixed(1)}S` : "";
  const actionLabel = item._config_error ? "CONFIG ERROR" : (actionType(item) === "obs" ? `OBS · ${item.obsAction}` : (item.macro ? `MACRO · ${item.macro.length} STEPS` : `${item.keys}${holdLabel}`));
  binding.textContent = item.disabled ? `${actionLabel} // DISABLED` : actionLabel;
  if (icon) button.append(icon);
  button.append(name, binding);
  button.addEventListener("click", () => sendCommand(item, button));
  return button;
}

async function sendCommand(item, element) {
  element.classList.add("firing");
  navigator.vibrate?.(25);
  const outgoing = actionType(item) === "obs" ? `OBS · ${item.obsAction}` : (item.macro ? `MACRO ×${item.macro.length}` : item.keys);
  writeLog(`TX // ${item.name.toUpperCase()} [${outgoing}]`);
  try {
    const response = await fetch("/api/commands", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        profile_id: state.activeProfile,
        button_id: item.id,
        test_mode: testToggle.checked,
      }),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || `HTTP ${response.status}`);
    const mode = body.test_mode ? "SIMULATED" : "SENT";
    if (body.action_type === "macro") {
      writeLog(`ACK // ${body.button.toUpperCase()} // MACRO ${body.steps} STEPS // ${mode}`, "success");
    } else if (body.action_type === "obs") {
      writeLog(`ACK // ${body.button.toUpperCase()} // OBS ${body.obs_action} // ${mode}`, "success");
      showToast(`OBS: ${body.button} // ${mode}`);
    } else {
      const hold = body.hold_ms > 0 ? ` // HOLD ${body.hold_ms}MS` : "";
      writeLog(`ACK // ${body.button.toUpperCase()} // ${body.keys}${hold} // ${mode}`, "success");
    }
  } catch (error) {
    writeLog(`ERROR // ${error.message}`, "error");
    showToast(error.message);
  } finally {
    setTimeout(() => element.classList.remove("firing"), 140);
  }
}

async function boot() {
  try {
    const [config, status] = await Promise.all([requestJson("/api/profiles"), requestJson("/api/status")]);
    state.profiles = config.profiles;
    state.forceTestMode = status.force_test_mode;
    document.querySelector("#deck-title").textContent = config.title || "NOVA DECK // SC";
    if (state.forceTestMode) {
      testToggle.checked = true;
      testToggle.disabled = true;
      writeLog("SERVER TEST MODE // KEY OUTPUT HARD-LOCKED");
    }
    setConnection("online", state.forceTestMode ? "TEST LOCK" : "SYSTEM ONLINE");
    if (!status.configuration?.ok) throw new Error(`Configuración inválida: ${status.configuration?.error || "error desconocido"}`);
    const savedProfile = localStorage.getItem("nova-deck-profile");
    const initialProfile = state.profiles.some((profile) => profile.id === savedProfile)
      ? savedProfile
      : (state.profiles.find((profile) => profile.id === "default")?.id || state.profiles[0]?.id);
    if (!initialProfile) throw new Error("No hay perfiles configurados.");
    await loadProfile(initialProfile);
  } catch (error) {
    setConnection("error", "OFFLINE");
    writeLog(`BOOT ERROR // ${error.message}`, "error");
    showToast(error.message);
  }
}

boot();
