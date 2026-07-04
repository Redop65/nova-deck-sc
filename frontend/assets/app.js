const state = {
  profiles: [], activeProfile: "default", pages: [], activePage: null,
  forceTestMode: false, editingId: null, editingProfile: null,
  editingPage: null, editingPosition: null, editingItem: null,
  deckEditMode: false, cockpitMode: false, configWarnings: [],
};
const colors = new Set(["cyan", "blue", "violet", "amber", "orange", "green", "red"]);
const themes = new Set(["dark-default", "space-blue", "amber-cockpit", "red-alert", "industrial-mining"]);
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
const backupFile = document.querySelector("#backup-file");
const reminderWidget = document.querySelector("#activity-reminder");
const reminderToggle = document.querySelector("#reminder-toggle");
const reminderCountdown = document.querySelector("#reminder-countdown");
const reminderState = { armed: false, dueAt: 0, interval: null, sending: false };
const fullscreenToggle = document.querySelector("#fullscreen-toggle");
const cockpitToggle = document.querySelector("#cockpit-toggle");
const themeSelect = document.querySelector("#theme-select");

document.querySelector("#open-editor").addEventListener("click", toggleDeckEditMode);
document.querySelector("#close-editor").addEventListener("click", () => setEditorMode(false));
document.querySelector("#new-button").addEventListener("click", startNewButton);
document.querySelector("#edit-new-button").addEventListener("click", openNewButtonEditor);
document.querySelector("#exit-edit-mode").addEventListener("click", toggleDeckEditMode);
document.querySelector("#duplicate-button").addEventListener("click", duplicateCurrentButton);
document.querySelector("#move-up-button").addEventListener("click", () => moveCurrentButton(-1));
document.querySelector("#move-down-button").addEventListener("click", () => moveCurrentButton(1));
deleteButton.addEventListener("click", () => { deleteConfirm.hidden = false; });
document.querySelector("#cancel-delete").addEventListener("click", () => { deleteConfirm.hidden = true; });
document.querySelector("#confirm-delete").addEventListener("click", deleteCurrentButton);
buttonForm.addEventListener("submit", saveButton);
document.querySelector("#field-type").addEventListener("change", updateActionFields);
document.querySelector("#field-profile").addEventListener("change", async (event) => {
  await populatePagesForProfile(event.target.value);
});
document.querySelector("#export-backup").addEventListener("click", exportBackup);
document.querySelector("#import-backup").addEventListener("click", () => backupFile.click());
backupFile.addEventListener("change", importBackup);
reminderToggle.addEventListener("click", toggleActivityReminder);
fullscreenToggle.addEventListener("click", toggleFullscreen);
cockpitToggle.addEventListener("click", () => applyCockpitMode(!state.cockpitMode));
themeSelect.addEventListener("change", () => applyTheme(themeSelect.value));
document.addEventListener("fullscreenchange", updateFullscreenControl);
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
applyCockpitMode(localStorage.getItem("nova-deck-cockpit") === "true", false);
updateFullscreenControl();

function writeLog(message, type = "") {
  log.className = `command-log ${type}`;
  logText.textContent = message;
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2800);
}

async function toggleFullscreen() {
  try {
    if (document.fullscreenElement) {
      await document.exitFullscreen();
    } else if (document.documentElement.requestFullscreen) {
      await document.documentElement.requestFullscreen();
    } else {
      showToast("Pantalla completa no disponible. Usa Añadir a pantalla de inicio en el menú del navegador.");
    }
  } catch (error) {
    showToast(`No se pudo activar pantalla completa: ${error.message}`);
  }
}

function updateFullscreenControl() {
  const active = Boolean(document.fullscreenElement);
  fullscreenToggle.textContent = active ? "EXIT FULL" : "FULL";
  fullscreenToggle.classList.toggle("active", active);
  fullscreenToggle.setAttribute("aria-pressed", String(active));
}

function applyCockpitMode(enabled, persist = true) {
  state.cockpitMode = enabled;
  if (enabled && state.deckEditMode) toggleDeckEditMode();
  if (enabled) setEditorMode(false);
  document.body.classList.toggle("cockpit-mode", enabled);
  cockpitToggle.textContent = enabled ? "EXIT CABIN" : "CABIN";
  cockpitToggle.classList.toggle("active", enabled);
  cockpitToggle.setAttribute("aria-pressed", String(enabled));
  if (persist) localStorage.setItem("nova-deck-cockpit", String(enabled));
}

function applyTheme(theme, persist = true) {
  const selected = themes.has(theme) ? theme : "dark-default";
  document.body.dataset.theme = selected;
  themeSelect.value = selected;
  if (persist) localStorage.setItem("nova-deck-theme", selected);
}

function randomReminderDelay() {
  return 210000 + Math.floor(Math.random() * 60001);
}

function toggleActivityReminder() {
  if (reminderState.armed) stopActivityReminder();
  else startActivityReminder();
}

function startActivityReminder() {
  reminderState.armed = true;
  reminderState.sending = false;
  reminderState.dueAt = Date.now() + randomReminderDelay();
  reminderWidget.classList.add("armed");
  reminderToggle.setAttribute("aria-pressed", "true");
  clearInterval(reminderState.interval);
  reminderState.interval = setInterval(updateReminderCountdown, 1000);
  writeLog("AFK MODE ENABLED // AUTOMATIC F2 CYCLE ARMED", "success");
  updateReminderCountdown();
}

function stopActivityReminder() {
  clearInterval(reminderState.interval);
  Object.assign(reminderState, { armed: false, dueAt: 0, interval: null, sending: false });
  reminderWidget.classList.remove("armed");
  reminderToggle.setAttribute("aria-pressed", "false");
  reminderCountdown.textContent = "OFF";
  writeLog("AFK MODE DISABLED // AUTOMATIC CYCLE STOPPED");
}

function updateReminderCountdown() {
  if (!reminderState.armed) return;
  const remaining = Math.max(0, reminderState.dueAt - Date.now());
  if (remaining === 0 && !reminderState.sending) void sendReminderKey();
  const totalSeconds = Math.ceil(remaining / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = String(totalSeconds % 60).padStart(2, "0");
  reminderCountdown.textContent = `${minutes}:${seconds}`;
}

async function sendReminderKey() {
  if (!reminderState.armed || reminderState.sending) return;
  reminderState.sending = true;
  reminderCountdown.textContent = "F2";
  try {
    const result = await requestJson("/api/commands", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        profile_id: "default", button_id: "star-map", test_mode: testToggle.checked,
      }),
    });
    writeLog(
      `AFK MODE // F2 ${result.test_mode ? "SIMULATED" : "SENT"} // NEXT CYCLE ARMED`,
      "success",
    );
  } catch (error) {
    writeLog(`AFK MODE ERROR // ${error.message} // RETRY CYCLE ARMED`, "error");
  } finally {
    if (reminderState.armed) {
      reminderState.sending = false;
      reminderState.dueAt = Date.now() + randomReminderDelay();
      updateReminderCountdown();
    }
  }
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

function toggleDeckEditMode() {
  state.deckEditMode = !state.deckEditMode;
  document.body.classList.toggle("deck-editing", state.deckEditMode);
  document.querySelector("#edit-toolbar").hidden = !state.deckEditMode;
  const control = document.querySelector("#open-editor");
  control.classList.toggle("active", state.deckEditMode);
  control.textContent = state.deckEditMode ? "DONE" : "EDIT";
  control.setAttribute("aria-label", state.deckEditMode ? "Desactivar modo Edit" : "Activar modo Edit");
  if (!state.deckEditMode) setEditorMode(false);
  if (state.activePage) selectPage(state.activePage);
}

function openNewButtonEditor() {
  startNewButton();
  setEditorMode(true);
}

function setEditorMode(enabled) {
  document.body.classList.toggle("editing", enabled);
  deckView.hidden = enabled;
  editorView.hidden = !enabled;
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

function populateProfileSelect(selectedProfile) {
  const select = document.querySelector("#field-profile");
  select.replaceChildren(...state.profiles.map((profile) => {
    const option = document.createElement("option");
    option.value = profile.id;
    option.textContent = profile.name;
    option.selected = profile.id === selectedProfile;
    return option;
  }));
}

async function populatePagesForProfile(profileId, selectedPage = null) {
  if (profileId === state.activeProfile) {
    populatePageSelect(selectedPage || state.pages[0]?.id);
    return;
  }
  const result = await requestJson(`/api/profiles/${encodeURIComponent(profileId)}`);
  const select = document.querySelector("#field-page");
  select.replaceChildren(...result.profile.pages.map((page) => {
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
    page.buttons.forEach((item, index) => {
      const row = document.createElement("button");
      row.type = "button";
      row.className = `catalogue-item ${item.id === state.editingId ? "active" : ""}`;
      row.setAttribute("aria-label", `Editar ${item.name}`);
      const name = document.createElement("span");
      name.textContent = item.name;
      const keys = document.createElement("code");
      keys.textContent = item._config_error ? "CONFIG ERROR" : (actionType(item) === "obs" ? `OBS · ${item.obsAction}` : (item.macro ? `MACRO ×${item.macro.length}` : item.keys));
      row.append(name, keys);
      row.addEventListener("click", () => editButton(page.id, item, index));
      group.append(row);
    });
    return group;
  }));
}

function startNewButton() {
  state.editingId = null;
  state.editingProfile = null;
  state.editingPage = null;
  state.editingPosition = null;
  state.editingItem = null;
  buttonForm.reset();
  document.querySelector("#field-type").value = "hotkey";
  updateActionFields();
  document.querySelector("#field-id").dataset.manual = "";
  populateProfileSelect(state.activeProfile);
  populatePageSelect(state.activePage || state.pages[0]?.id);
  document.querySelector("#form-title").textContent = "New Button";
  document.querySelector("#form-state").textContent = "NEW";
  deleteButton.hidden = true;
  document.querySelector("#duplicate-button").hidden = true;
  document.querySelector("#move-up-button").hidden = true;
  document.querySelector("#move-down-button").hidden = true;
  deleteConfirm.hidden = true;
  setFormMessage("");
  renderEditorList();
  document.querySelector("#field-name").focus();
}

function editButton(pageId, item, position = null) {
  state.editingId = item.id;
  state.editingProfile = state.activeProfile;
  state.editingPage = pageId;
  state.editingPosition = position ?? state.pages.find((page) => page.id === pageId)?.buttons.indexOf(item) ?? 0;
  state.editingItem = structuredClone(item);
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
  populateProfileSelect(state.activeProfile);
  populatePageSelect(pageId);
  document.querySelector("#form-title").textContent = item.name;
  document.querySelector("#form-state").textContent = "EDITING";
  deleteButton.hidden = false;
  document.querySelector("#duplicate-button").hidden = false;
  document.querySelector("#move-up-button").hidden = false;
  document.querySelector("#move-down-button").hidden = false;
  deleteConfirm.hidden = true;
  setFormMessage("");
  renderEditorList();
}

function formPayload() {
  const type = document.querySelector("#field-type").value;
  const targetProfile = document.querySelector("#field-profile").value;
  const icon = document.querySelector("#field-icon").value.trim();
  const macroText = document.querySelector("#field-macro").value.trim();
  let macro = null;
  if (type === "macro" && macroText) {
    macro = JSON.parse(macroText);
    if (!Array.isArray(macro)) throw new Error("Macro JSON must be an array of steps.");
  }
  return {
    profile_id: state.editingId === null ? targetProfile : (state.editingProfile || state.activeProfile),
    target_profile_id: state.editingId === null ? null : targetProfile,
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

async function exportBackup() {
  try {
    const response = await fetch("/api/backup/export");
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || `HTTP ${response.status}`);
    }
    const blob = await response.blob();
    const disposition = response.headers.get("Content-Disposition") || "";
    const filename = disposition.match(/filename="?([^";]+)"?/i)?.[1] || "nova-deck-backup.json";
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
    writeLog(`BACKUP EXPORTED // ${filename} // OBS PASSWORD EXCLUDED`, "success");
    showToast("Backup exportado correctamente");
  } catch (error) {
    writeLog(`BACKUP ERROR // ${error.message}`, "error");
    showToast(error.message);
  }
}

async function importBackup(event) {
  const file = event.target.files?.[0];
  event.target.value = "";
  if (!file) return;
  if (file.size > 2 * 1024 * 1024) {
    showToast("El backup supera el límite de 2 MB.");
    return;
  }
  let text;
  let parsed;
  try {
    text = await file.text();
    parsed = JSON.parse(text);
  } catch (error) {
    writeLog(`IMPORT REJECTED // JSON mal formado: ${error.message}`, "error");
    showToast("El archivo no contiene JSON válido");
    return;
  }
  const containsPassword = Boolean(parsed?.secrets?.obs_password_included);
  const warning = containsPassword
    ? "Este backup declara que contiene una contraseña OBS y reemplazará la configuración actual."
    : "La configuración actual será reemplazada; la contraseña OBS local se conservará.";
  if (!window.confirm(`${warning}\n\nSe creará primero un backup local automático. ¿Continuar?`)) return;
  try {
    const result = await requestJson("/api/backup/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: text,
    });
    const config = await requestJson("/api/profiles");
    state.profiles = config.profiles;
    const nextProfile = state.profiles.some((profile) => profile.id === state.activeProfile)
      ? state.activeProfile
      : (state.profiles.find((profile) => profile.id === "default")?.id || state.profiles[0]?.id);
    await loadProfile(nextProfile);
    renderEditorList();
    startNewButton();
    writeLog(`BACKUP IMPORTED // LOCAL SAFETY COPY: ${result.local_backup}`, "success");
    showToast("Configuración importada correctamente");
  } catch (error) {
    writeLog(`IMPORT REJECTED // ${error.message}`, "error");
    showToast(error.message);
  }
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
    const targetProfile = payload.target_profile_id || payload.profile_id;
    if (targetProfile !== state.activeProfile) await loadProfile(targetProfile);
    else await reloadConfiguration();
    const page = state.pages.find((candidate) => candidate.id === payload.page_id);
    const saved = page?.buttons.find((candidate) => candidate.id === result.button.id);
    if (saved) editButton(page.id, saved, page.buttons.indexOf(saved));
    setFormMessage(`SAVED // ${result.button.id} // BACKUP ${result.local_backup}`);
    showToast("Button saved to config/buttons.json");
  } catch (error) {
    setFormMessage(`ERROR // ${error.message}`, "error");
  }
}

async function duplicateCurrentButton() {
  if (!state.editingItem || !state.editingProfile || !state.editingPage) return;
  const existingIds = new Set(state.pages.flatMap((page) => page.buttons.map((button) => button.id)));
  let copyId = `${state.editingItem.id}-copy`;
  let suffix = 2;
  while (existingIds.has(copyId)) copyId = `${state.editingItem.id}-copy-${suffix++}`;
  const copy = structuredClone(state.editingItem);
  delete copy._config_error;
  copy.id = copyId;
  copy.name = `${copy.name} Copy`;
  try {
    const result = await requestJson("/api/buttons", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        profile_id: state.editingProfile,
        page_id: state.editingPage,
        button: copy,
      }),
    });
    await reloadConfiguration();
    const page = state.pages.find((candidate) => candidate.id === state.editingPage);
    const duplicate = page?.buttons.find((candidate) => candidate.id === copyId);
    if (duplicate) editButton(page.id, duplicate, page.buttons.indexOf(duplicate));
    setFormMessage(`DUPLICATED // ${copyId} // BACKUP ${result.local_backup}`);
  } catch (error) {
    setFormMessage(`ERROR // ${error.message}`, "error");
  }
}

async function moveCurrentButton(direction) {
  if (state.editingId === null || state.editingPosition === null) return;
  const payload = formPayload();
  payload.position = Math.max(0, state.editingPosition + direction);
  try {
    const result = await requestJson(`/api/buttons/${encodeURIComponent(state.editingId)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const targetProfile = payload.target_profile_id || payload.profile_id;
    if (targetProfile !== state.activeProfile) await loadProfile(targetProfile);
    else await reloadConfiguration();
    const page = state.pages.find((candidate) => candidate.id === payload.page_id);
    const moved = page?.buttons.find((candidate) => candidate.id === result.button.id);
    if (moved) editButton(page.id, moved, page.buttons.indexOf(moved));
    setFormMessage(`MOVED // POSITION ${(page?.buttons.indexOf(moved) ?? 0) + 1} // BACKUP ${result.local_backup}`);
  } catch (error) {
    setFormMessage(`ERROR // ${error.message}`, "error");
  }
}

async function deleteCurrentButton() {
  if (state.editingId === null) return;
  const id = state.editingId;
  try {
    const result = await requestJson(
      `/api/buttons/${encodeURIComponent(id)}?profile_id=${encodeURIComponent(state.editingProfile || state.activeProfile)}`,
      { method: "DELETE" },
    );
    state.editingId = null;
    await reloadConfiguration();
    startNewButton();
    setFormMessage(`DELETED // ${id} // BACKUP ${result.local_backup}`);
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
  button.disabled = Boolean(item.disabled) && !state.deckEditMode;
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
  button.addEventListener("click", () => {
    if (state.deckEditMode) {
      editButton(state.activePage, item, index);
      setEditorMode(true);
    } else {
      sendCommand(item, button);
    }
  });
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
    const savedTheme = localStorage.getItem("nova-deck-theme");
    applyTheme(themes.has(savedTheme) ? savedTheme : status.default_theme, false);
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
