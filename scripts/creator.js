const projectTitleInput = document.querySelector("#projectTitle");
const storyInput = document.querySelector("#storyInput");
const storyCounter = document.querySelector("[data-story-counter]");
const clearStoryButton = document.querySelector("[data-clear-story]");
const enhanceStoryButton = document.querySelector("[data-enhance-story]");
const generatePageButton = document.querySelector("[data-generate-page]");
const regenerateSceneButton = document.querySelector("[data-regenerate-scene]");
const suggestScenesButton = document.querySelector("[data-suggest-scenes]");
const addSceneButton = document.querySelector("[data-add-scene]");
const sceneList = document.querySelector("[data-scene-list]");
const sceneCounter = document.querySelector("[data-scene-counter]");
const selectedSceneBlock = document.querySelector("[data-selected-scene]");
const pageStrip = document.querySelector(".page-strip");
let pageThumbs = Array.from(document.querySelectorAll("[data-page-thumb]"));
const pageStatus = document.querySelector("[data-page-status]");
const comicCanvas = document.querySelector("[data-comic-canvas]");
const comicOutput = document.querySelector("[data-comic-output]");
const comicLoading = document.querySelector("[data-loading]");
const loadingLabel = document.querySelector("[data-loading-label]");
const emptyState = document.querySelector("[data-empty-state]");
const toast = document.querySelector("[data-toast]");
const downloadButton = document.querySelector("[data-download-page]");
const shareButton = document.querySelector("[data-share-project]");
const addPageButton = document.querySelector("[data-add-page]");
const sceneTitleInput = document.querySelector("#sceneTitleInput");
const sceneDescriptionInput = document.querySelector("#sceneDescriptionInput");
const dialogueInput = document.querySelector("#dialogueInput");
const captionInput = document.querySelector("#captionInput");
const regenerateDialogueButton = document.querySelector("[data-regenerate-dialogue]");
const generateCaptionButton = document.querySelector("[data-generate-caption]");
const creditInfoButton = document.querySelector("[data-credit-info]");
const addCreditsButton = document.querySelector("[data-add-credits]");
const creditBalance = document.querySelector("[data-credit-balance]");
const notificationsButton = document.querySelector("[data-notifications]");
const profileToggle = document.querySelector("[data-profile-toggle]");
const profileMenu = document.querySelector("[data-profile-menu]");
const profileActions = Array.from(document.querySelectorAll("[data-profile-action]"));
const renameButton = document.querySelector("[data-rename-project]");
const undoButton = document.querySelector("[data-undo]");
const redoButton = document.querySelector("[data-redo]");
const zoomSelect = document.querySelector("#zoomSelect");
const zoomLabel = document.querySelector("[data-zoom-label]");
const burgerToggle = document.querySelector("[data-burger-toggle]");
const burgerMenu = document.querySelector("[data-burger-menu]");
const configBanner = document.querySelector("[data-config-banner]");
const selectedSceneTitle = document.querySelector("[data-selected-scene-title]");
const styleValueLabel = document.querySelector("[data-style-value]");
const styleOptionButtons = Array.from(document.querySelectorAll("[data-style-option]"));
const modelValueLabel = document.querySelector("[data-model-value]");
const modelOptionButtons = Array.from(document.querySelectorAll("[data-model-id]"));
const dropdowns = Array.from(document.querySelectorAll("[data-dropdown]"));
const characterListEl = document.querySelector("[data-character-list]");
const addCharacterButton = document.querySelector("[data-add-character]");
const pageCountInput = document.querySelector("#pageCountInput");
const pageCountSteps = Array.from(document.querySelectorAll("[data-page-count-step]"));
const dialogueLanguageSelect = document.querySelector("#dialogueLanguage");
const costValueEl = document.querySelector("[data-cost]");
const continueButton = document.querySelector("[data-continue-story]");
const authOverlay = document.querySelector("[data-auth-overlay]");
const authLoginLinks = Array.from(document.querySelectorAll("[data-auth-login]"));
const authError = document.querySelector("[data-auth-error]");
const saveStatus = document.querySelector("[data-save-status]");
const profileName = document.querySelector("[data-profile-name]");
const profileEmail = document.querySelector("[data-profile-email]");
const profileAvatar = document.querySelector("[data-profile-avatar]");

const DEFAULT_MODEL_ID = "bytedance-seed/seedream-4.5";
const PRICE_PER_PAGE = 20;
const MAX_PAGE_COUNT = 10;
const API_BASE_URL = resolveApiBaseUrl();

const MODEL_LABELS = {
  "bytedance-seed/seedream-4.5": "Seedream",
  "google/gemini-3-pro-image-preview": "Nano Banana Pro",
  "openai/gpt-5.4-image-2": "GPT Image 2",
};

const PLACEHOLDER_IMAGES = [
  "assets/comic-preview-fantasy.png",
  "assets/comic-preview-japan.png",
  "assets/comic-preview-action.png",
  "assets/comicly-reference.png",
];

function createDefaultPageContext(overrides = {}) {
  return {
    story: "",
    pageOutline: "",
    scenes: [],
    characters: [],
    pageCount: 1,
    summary: "",
    generated: false,
    ...overrides,
  };
}

const initialStoryValue = (typeof storyInput?.value === "string" ? storyInput.value : "") || "";
let pageContexts = [createDefaultPageContext({ story: initialStoryValue })];
let pages = [createPlaceholderDataUrl(1)];
let pageImages = ["assets/comic-preview-fantasy.png"];
let scenes = pageContexts[0].scenes;
let characters = pageContexts[0].characters;

let activeStyle = "Аниме";
let activeModel = DEFAULT_MODEL_ID;
let pageCount = 1;
let dialogueLanguage = "ru";

let activePage = 0;
let activeScene = 0;
let credits = 0;
let isRestoring = false;
let historyIndex = -1;
let history = [];
let currentAccount = null;
let currentComicId = null;
let saveTimer = null;
let activeGenerationButton = null;

class ApiClientError extends Error {
  constructor(message, { status = 0, code = "API_ERROR", payload = null } = {}) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = code;
    this.payload = payload;
  }
}

function resolveApiBaseUrl() {
  const configured = typeof window.COMICLY_API_BASE_URL === "string"
    ? window.COMICLY_API_BASE_URL.trim()
    : "";
  if (configured) return configured.replace(/\/+$/, "");

  const hostname = window.location.hostname;
  if (hostname === "localhost" || hostname === "127.0.0.1" || hostname === "::1") {
    return "http://localhost:8000";
  }
  if (hostname.endsWith(".vercel.app")) {
    return "https://comicly-backend.vercel.app";
  }
  return "https://api.comicly.ai";
}

function buildApiUrl(path) {
  return `${API_BASE_URL}${path}`;
}

async function apiFetch(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const init = {
    ...options,
    credentials: "include",
    headers,
  };

  if (init.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(buildApiUrl(path), init);
  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const envelope = data?.error || {};
    const message = envelope.message || data?.message || data?.detail || "Backend недоступен.";
    throw new ApiClientError(message, {
      status: response.status,
      code: envelope.code || data?.code || "API_ERROR",
      payload: data,
    });
  }

  return data;
}

function isPlaceholderImage(src) {
  return typeof src === "string" && src.startsWith("data:image/svg+xml");
}

function saveCurrentToContext() {
  const ctx = pageContexts[activePage];
  if (!ctx) return;
  ctx.story = storyInput?.value || "";
  ctx.pageCount = pageCount;
}

function loadActivePageContext() {
  let ctx = pageContexts[activePage];
  if (!ctx) {
    ctx = createDefaultPageContext();
    pageContexts[activePage] = ctx;
  }
  if (storyInput) storyInput.value = ctx.story || "";
  scenes = ctx.scenes;
  characters = ctx.characters;
  pageCount = ctx.pageCount || 1;
  if (pageCountInput) pageCountInput.value = String(pageCount);
  activeScene = 0;
  renderCharacters();
  renderScenes();
  updateStoryCounter();
  updateCostNote();
}

function showToast(message) {
  if (!toast) return;
  toast.textContent = message;
  toast.hidden = false;

  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => {
    toast.hidden = true;
  }, 3800);
}

function setAuthOverlayVisible(isVisible, message = "") {
  if (authOverlay) authOverlay.hidden = !isVisible;
  if (authError) {
    authError.textContent = message;
    authError.hidden = !message;
  }
}

function resetTrustedState() {
  currentAccount = null;
  currentComicId = null;
  credits = 0;
  updateCreditBalance();
  updateProfileDisplay(null);
}

function updateProfileDisplay(account) {
  const displayName = account?.display_name || account?.email || "Профиль";
  const email = account?.email || "Автор";
  const initial = displayName.trim().charAt(0).toUpperCase() || "?";

  if (profileName) profileName.textContent = displayName;
  if (profileEmail) profileEmail.textContent = email;
  if (profileAvatar) profileAvatar.textContent = initial;
}

function setSaveStatus(state, text) {
  if (!saveStatus) return;
  saveStatus.textContent = text;
  saveStatus.classList.toggle("is-saving", state === "saving");
  saveStatus.classList.toggle("is-saved", state === "saved");
  saveStatus.classList.toggle("is-error", state === "error");
}

function updateSessionState(data) {
  currentAccount = data?.account || null;
  credits = Number(data?.wallet?.balance ?? 0);
  updateCreditBalance();
  updateProfileDisplay(currentAccount);
  setAuthOverlayVisible(false);
}

async function bootstrapSession() {
  setAuthOverlayVisible(false);
  setSaveStatus("saving", "Проверяем вход...");

  authLoginLinks.forEach((link) => {
    const provider = link.dataset.authLogin;
    link.href = buildApiUrl(`/api/v1/auth/${provider}/login`);
  });

  try {
    const data = await apiFetch("/api/v1/me");
    updateSessionState(data);
    setSaveStatus("saved", "Готово");
  } catch (error) {
    resetTrustedState();
    if (error instanceof ApiClientError && error.status === 401) {
      setAuthOverlayVisible(true);
      setSaveStatus("error", "Войдите");
      return;
    }
    showConfigBanner();
    setAuthOverlayVisible(true, "Не удалось подключиться к backend. Попробуйте обновить страницу.");
    setSaveStatus("error", "Backend недоступен");
  }
}

function escapeHtml(value = "") {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[char]);
}

function getSnapshot() {
  saveCurrentToContext();
  return {
    title: projectTitleInput?.value || "",
    style: activeStyle,
    model: activeModel,
    dialogueLanguage,
    activePage,
    activeScene,
    pages: [...pages],
    pageContexts: pageContexts.map((c) => ({
      story: c.story || "",
      pageOutline: c.pageOutline || "",
      scenes: (c.scenes || []).map((s) => ({ ...s })),
      characters: (c.characters || []).map((ch) => ({ ...ch })),
      pageCount: c.pageCount || 1,
      summary: c.summary || "",
      generated: Boolean(c.generated),
    })),
    credits,
  };
}

function updateUndoRedoButtons() {
  if (undoButton) undoButton.disabled = historyIndex <= 0;
  if (redoButton) redoButton.disabled = historyIndex >= history.length - 1;
}

function pushHistory() {
  if (isRestoring) return;

  const snapshot = getSnapshot();
  const serialized = JSON.stringify(snapshot);
  if (history[historyIndex] && JSON.stringify(history[historyIndex]) === serialized) return;

  history = history.slice(0, historyIndex + 1);
  history.push(snapshot);
  if (history.length > 60) history.shift();
  historyIndex = history.length - 1;
  updateUndoRedoButtons();
  scheduleBackendSave();
}

function restoreSnapshot(snapshot) {
  isRestoring = true;

  if (projectTitleInput) projectTitleInput.value = snapshot.title || "";
  pages = Array.isArray(snapshot.pages) && snapshot.pages.length
    ? [...snapshot.pages]
    : [createPlaceholderDataUrl(1)];

  const restoredContexts = Array.isArray(snapshot.pageContexts) ? snapshot.pageContexts : [];
  pageContexts = restoredContexts.map((c) => ({
    story: c.story || "",
    pageOutline: c.pageOutline || "",
    scenes: (c.scenes || []).map((s) => ({ ...s })),
    characters: (c.characters || []).map((ch) => ({ ...ch })),
    pageCount: c.pageCount || 1,
    summary: c.summary || "",
    generated: Boolean(c.generated),
  }));
  while (pageContexts.length < pages.length) pageContexts.push(createDefaultPageContext());
  if (pageContexts.length > pages.length) pageContexts.length = pages.length;

  credits = typeof snapshot.credits === "number" ? snapshot.credits : credits;
  dialogueLanguage = snapshot.dialogueLanguage || "ru";
  if (dialogueLanguageSelect) dialogueLanguageSelect.value = dialogueLanguage;

  activePage = Math.min(Math.max(0, Number(snapshot.activePage) || 0), pages.length - 1);
  loadActivePageContext();
  if (scenes.length) {
    activeScene = Math.min(Math.max(0, Number(snapshot.activeScene) || 0), scenes.length - 1);
  } else {
    activeScene = 0;
  }

  renderPageStrip();
  updateCreditBalance();
  setStyle(snapshot.style, false);
  setModel(snapshot.model || DEFAULT_MODEL_ID, false);

  if (scenes.length) setScene(activeScene, false);
  else refreshSceneSelection();

  if (comicOutput) {
    comicOutput.src = pages[activePage];
    comicOutput.hidden = false;
  }
  if (emptyState) emptyState.hidden = true;
  pageThumbs.forEach((thumb) => {
    thumb.classList.toggle("is-active", Number(thumb.dataset.pageThumb) === activePage);
  });
  if (pageStatus) pageStatus.textContent = `Страница ${activePage + 1} из ${pages.length}`;
  refreshContinueButton();

  isRestoring = false;
  updateUndoRedoButtons();
}

function undo() {
  if (historyIndex <= 0) return;
  historyIndex -= 1;
  restoreSnapshot(history[historyIndex]);
  showToast("Изменение отменено.");
}

function redo() {
  if (historyIndex >= history.length - 1) return;
  historyIndex += 1;
  restoreSnapshot(history[historyIndex]);
  showToast("Изменение возвращено.");
}

function updateStoryCounter() {
  if (!storyInput || !storyCounter) return;
  storyCounter.textContent = `${storyInput.value.length} / 2000`;
}

function updateCreditBalance() {
  if (creditBalance) creditBalance.textContent = `${credits} монет`;
}

function updateCostNote() {
  if (costValueEl) costValueEl.textContent = String(PRICE_PER_PAGE * pageCount);
}

function getPrimaryStory() {
  saveCurrentToContext();
  return (pageContexts[0]?.story || storyInput?.value || "").trim();
}

function buildComicMetadata() {
  return {
    title: (projectTitleInput?.value || "").trim() || "Новый комикс",
    story: getPrimaryStory() || null,
    characters: buildCharactersTextFor(pageContexts[0]?.characters || characters) || null,
    style: activeStyle || null,
    tone: dialogueLanguage ? `dialogue:${dialogueLanguage}` : null,
    selected_model: activeModel || null,
    status: "draft",
  };
}

function buildSceneRequests() {
  saveCurrentToContext();
  const primaryScenes = pageContexts[activePage]?.scenes || scenes;
  return primaryScenes.map((scene, index) => ({
    position: index + 1,
    title: scene.title || null,
    description: scene.description || null,
    dialogue: scene.dialogue || null,
    caption: scene.caption || null,
  }));
}

function buildPageRequests() {
  return pages.map((src, index) => {
    const ctx = pageContexts[index] || {};
    return {
      page_number: index + 1,
      status: ctx.generated ? "succeeded" : "pending",
      model: activeModel,
      coin_cost: ctx.generated ? PRICE_PER_PAGE : null,
      image_url: src && !isPlaceholderImage(src) && !src.startsWith("data:") ? src : null,
      scene_id: ctx.backendSceneId || null,
    };
  });
}

async function ensureCurrentComic() {
  if (!currentAccount) {
    throw new ApiClientError("Войдите, чтобы создавать комиксы.", { status: 401, code: "AUTH_REQUIRED" });
  }
  if (currentComicId) return currentComicId;

  setSaveStatus("saving", "Сохраняем...");
  const comic = await apiFetch("/api/v1/comics", {
    method: "POST",
    body: JSON.stringify(buildComicMetadata()),
  });
  currentComicId = comic.id;
  setSaveStatus("saved", "Сохранено");
  return currentComicId;
}

async function saveCurrentComic({ required = false, includePages = false } = {}) {
  if (!currentAccount) {
    if (required) {
      throw new ApiClientError("Войдите, чтобы создавать комиксы.", { status: 401, code: "AUTH_REQUIRED" });
    }
    return null;
  }

  try {
    const comicId = await ensureCurrentComic();
    setSaveStatus("saving", "Сохраняем...");
    await apiFetch(`/api/v1/comics/${comicId}`, {
      method: "PATCH",
      body: JSON.stringify(buildComicMetadata()),
    });

    const sceneResponses = await apiFetch(`/api/v1/comics/${comicId}/scenes`, {
      method: "PUT",
      body: JSON.stringify({ scenes: buildSceneRequests() }),
    });
    const targetScenes = pageContexts[activePage]?.scenes || scenes;
    sceneResponses.forEach((scene, index) => {
      if (targetScenes[index]) targetScenes[index].backendSceneId = scene.id;
    });

    if (includePages) {
      await apiFetch(`/api/v1/comics/${comicId}/pages`, {
        method: "PUT",
        body: JSON.stringify({ pages: buildPageRequests() }),
      });
    }

    setSaveStatus("saved", "Сохранено");
    return comicId;
  } catch (error) {
    setSaveStatus("error", "Не сохранено");
    if (required) throw error;
    return null;
  }
}

function scheduleBackendSave() {
  if (!currentAccount || !currentComicId || isRestoring) return;
  window.clearTimeout(saveTimer);
  saveTimer = window.setTimeout(() => {
    void saveCurrentComic();
  }, 900);
}

function setLoading(isLoading, label = "Генерируем страницу/изображение...") {
  if (comicLoading) comicLoading.hidden = !isLoading;
  if (loadingLabel && label) loadingLabel.textContent = label;
  if (!isLoading) refreshContinueButton();
}

function createPlaceholderDataUrl(pageNumber) {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="900" height="1200" viewBox="0 0 900 1200">
      <rect width="900" height="1200" fill="#060917"/>
      <rect x="34" y="34" width="832" height="1132" rx="28" fill="#0b1428" stroke="#1874d9" stroke-width="4"/>
      <path d="M450 360l44 112 112 42-112 43-44 112-44-112-112-43 112-42 44-112z" fill="#56a7ff"/>
      <text x="450" y="760" text-anchor="middle" fill="#f7fbff" font-family="Arial, sans-serif" font-size="48" font-weight="700">Страница ${pageNumber}</text>
      <text x="450" y="820" text-anchor="middle" fill="#8bc2ff" font-family="Arial, sans-serif" font-size="28">Нажмите «Сгенерировать страницу»</text>
    </svg>`;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

function renderPageStrip() {
  if (!pageStrip || !addPageButton) return;

  Array.from(pageStrip.querySelectorAll(".page-thumb-cell")).forEach((cell) => cell.remove());
  pageThumbs = pages.map((src, index) => {
    const cell = document.createElement("div");
    cell.className = "page-thumb-cell";
    cell.dataset.pageThumbCell = String(index);

    const button = document.createElement("button");
    button.className = "page-thumb";
    button.type = "button";
    button.dataset.pageThumb = String(index);
    button.innerHTML = `<img src="${src}" alt="Страница ${index + 1}" /><span>${index + 1}</span>`;
    button.addEventListener("click", () => setPage(index));
    cell.appendChild(button);

    const removeBtn = document.createElement("button");
    removeBtn.className = "page-thumb-remove";
    removeBtn.type = "button";
    removeBtn.dataset.pageRemove = String(index);
    removeBtn.setAttribute("aria-label", `Удалить страницу ${index + 1}`);
    removeBtn.title = "Удалить страницу";
    removeBtn.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 21a2 2 0 0 1-2-2V7H4V5h5V3h6v2h5v2h-1v12a2 2 0 0 1-2 2H7zm2-3h2V8H9v10zm4 0h2V8h-2v10z" /></svg>';
    removeBtn.addEventListener("click", (event) => {
      event.stopPropagation();
      removePage(index);
    });
    cell.appendChild(removeBtn);

    pageStrip.insertBefore(cell, addPageButton);
    return button;
  });
  pageThumbs.forEach((thumb) => {
    thumb.classList.toggle("is-active", Number(thumb.dataset.pageThumb) === activePage);
  });
  if (pageStatus) pageStatus.textContent = `Страница ${activePage + 1} из ${pages.length}`;
}

function removePage(index) {
  if (typeof index !== "number" || index < 0 || index >= pages.length) return;

  saveCurrentToContext();

  if (pages.length <= 1) {
    pages[0] = createPlaceholderDataUrl(1);
    pageContexts[0] = createDefaultPageContext();
    activePage = 0;
    activeScene = 0;
    renderPageStrip();
    setPage(0, false);
    pushHistory();
    showToast("Страница очищена.");
    return;
  }

  pages.splice(index, 1);
  pageContexts.splice(index, 1);

  pages.forEach((src, i) => {
    if (isPlaceholderImage(src)) pages[i] = createPlaceholderDataUrl(i + 1);
  });

  let nextActive;
  if (activePage === index) {
    nextActive = Math.max(0, index - 1);
  } else if (activePage > index) {
    nextActive = activePage - 1;
  } else {
    nextActive = activePage;
  }
  nextActive = Math.min(nextActive, pages.length - 1);
  activePage = nextActive;
  activeScene = 0;

  renderPageStrip();
  setPage(activePage, false);
  pushHistory();
  showToast(`Страница удалена. Осталось страниц: ${pages.length}.`);
}

function setPage(index, save = true) {
  if (!pages[index]) return;
  if (!isRestoring && index !== activePage) {
    saveCurrentToContext();
  }
  activePage = index;
  if (!isRestoring) {
    loadActivePageContext();
  }

  pageThumbs.forEach((thumb) => {
    thumb.classList.toggle("is-active", Number(thumb.dataset.pageThumb) === index);
  });

  if (pageStatus) pageStatus.textContent = `Страница ${index + 1} из ${pages.length}`;
  if (comicOutput) {
    comicOutput.src = pages[index];
    comicOutput.hidden = false;
  }
  if (emptyState) emptyState.hidden = true;
  refreshContinueButton();
  if (save) pushHistory();
}

/* ───────── Стиль (выпадающий список) ───────── */
function setStyle(style, save = true) {
  activeStyle = style || "Аниме";
  if (styleValueLabel) styleValueLabel.textContent = activeStyle;
  styleOptionButtons.forEach((btn) => {
    btn.classList.toggle("is-selected", btn.dataset.styleOption === activeStyle);
  });
  if (save) pushHistory();
}

/* ───────── Модель (выпадающий список) ───────── */
function setModel(modelId, save = true) {
  const exists = modelOptionButtons.some((btn) => btn.dataset.modelId === modelId);
  activeModel = exists ? modelId : DEFAULT_MODEL_ID;

  if (modelValueLabel) modelValueLabel.textContent = MODEL_LABELS[activeModel] || activeModel;
  modelOptionButtons.forEach((btn) => {
    btn.classList.toggle("is-selected", btn.dataset.modelId === activeModel);
  });

  if (save) pushHistory();
}

/* ───────── Универсальный dropdown ───────── */
function closeAllDropdowns(except) {
  dropdowns.forEach((wrap) => {
    if (wrap === except) return;
    const toggle = wrap.querySelector("[data-dropdown-toggle]");
    const menu = wrap.querySelector("[data-dropdown-menu]");
    if (toggle) toggle.setAttribute("aria-expanded", "false");
    if (menu) menu.hidden = true;
  });
}

function toggleDropdown(wrap, force) {
  const toggle = wrap.querySelector("[data-dropdown-toggle]");
  const menu = wrap.querySelector("[data-dropdown-menu]");
  if (!toggle || !menu) return;
  const shouldOpen = typeof force === "boolean" ? force : menu.hidden;
  closeAllDropdowns(shouldOpen ? wrap : null);
  menu.hidden = !shouldOpen;
  toggle.setAttribute("aria-expanded", String(shouldOpen));
}

dropdowns.forEach((wrap) => {
  const toggle = wrap.querySelector("[data-dropdown-toggle]");
  toggle?.addEventListener("click", (event) => {
    event.stopPropagation();
    toggleDropdown(wrap);
  });
});

styleOptionButtons.forEach((btn) => {
  btn.addEventListener("click", (event) => {
    event.stopPropagation();
    setStyle(btn.dataset.styleOption);
    closeAllDropdowns();
  });
});

modelOptionButtons.forEach((btn) => {
  btn.addEventListener("click", (event) => {
    event.stopPropagation();
    setModel(btn.dataset.modelId);
    closeAllDropdowns();
  });
});

/* ───────── Сцены ───────── */
function renderScenes() {
  if (!sceneList) return;
  sceneList.innerHTML = "";

  if (!scenes.length) {
    sceneList.innerHTML = '<div class="scene-empty">Сцены не заданы. При генерации страница будет раскадрована автоматически.</div>';
    activeScene = 0;
    refreshSceneSelection();
    return;
  }

  scenes.forEach((scene, index) => {
    const thumbSrc = pageImages[index % pageImages.length];
    const article = document.createElement("article");
    article.className = "scene-item";
    article.dataset.scene = String(index);
    article.innerHTML = `
      <button class="drag-handle" type="button" aria-label="Переместить сцену" data-move-scene>
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5h2v2H8V5zm6 0h2v2h-2V5zM8 11h2v2H8v-2zm6 0h2v2h-2v-2zM8 17h2v2H8v-2zm6 0h2v2h-2v-2z" /></svg>
      </button>
      <img src="${thumbSrc}" alt="" />
      <div>
        <h2>${escapeHtml(scene.title || `Сцена ${index + 1}`)}</h2>
        <p>${escapeHtml(scene.description || "Описание появится при генерации.")}</p>
      </div>
      <button class="icon-action small" type="button" aria-label="Меню сцены" data-scene-menu>
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 10a2 2 0 1 1 0 4 2 2 0 0 1 0-4zm7 0a2 2 0 1 1 0 4 2 2 0 0 1 0-4zm7 0a2 2 0 1 1 0 4 2 2 0 0 1 0-4z" /></svg>
      </button>
    `;
    article.addEventListener("click", () => setScene(index));
    article.querySelector("[data-move-scene]").addEventListener("click", (event) => {
      event.stopPropagation();
      moveScene(index);
    });
    article.querySelector("[data-scene-menu]").addEventListener("click", (event) => {
      event.stopPropagation();
      openSceneMenu(index);
    });
    sceneList.appendChild(article);
  });

  refreshSceneSelection();
}

function updateSelectedSceneForm() {
  const scene = scenes[activeScene];
  const hasScene = Boolean(scene);

  if (selectedSceneBlock) selectedSceneBlock.hidden = !hasScene;

  const fields = [
    sceneTitleInput,
    sceneDescriptionInput,
    dialogueInput,
    captionInput,
    regenerateDialogueButton,
    generateCaptionButton,
    regenerateSceneButton,
  ];

  fields.forEach((field) => {
    if (field) field.disabled = !hasScene;
  });

  if (!hasScene) {
    if (sceneTitleInput) sceneTitleInput.value = "";
    if (sceneDescriptionInput) sceneDescriptionInput.value = "";
    if (dialogueInput) dialogueInput.value = "";
    if (captionInput) captionInput.value = "";
  }
}

function refreshSceneSelection() {
  const items = sceneList ? Array.from(sceneList.querySelectorAll("[data-scene]")) : [];
  items.forEach((item) => {
    const sceneIndex = Number(item.dataset.scene);
    const scene = scenes[sceneIndex];
    item.classList.toggle("is-selected", sceneIndex === activeScene);
    const title = item.querySelector("h2");
    const description = item.querySelector("p");
    if (title) title.textContent = scene?.title || `Сцена ${sceneIndex + 1}`;
    if (description) description.textContent = scene?.description || "Описание появится при генерации.";
  });
  if (sceneCounter) sceneCounter.textContent = scenes.length ? `${activeScene + 1} из ${scenes.length}` : "0 из 0";
  if (selectedSceneTitle) {
    selectedSceneTitle.textContent = scenes[activeScene]?.title || "Сцена не выбрана";
  }
  updateSelectedSceneForm();
}

function setScene(sceneIndex, save = true) {
  if (sceneIndex < 0 || sceneIndex >= scenes.length) return;
  activeScene = sceneIndex;
  const scene = scenes[sceneIndex];

  refreshSceneSelection();
  if (sceneTitleInput) sceneTitleInput.value = scene.title || "";
  if (sceneDescriptionInput) sceneDescriptionInput.value = scene.description || "";
  if (dialogueInput) dialogueInput.value = scene.dialogue || "";
  if (captionInput) captionInput.value = scene.caption || "";

  if (save) pushHistory();
}

function syncSceneFromInputs() {
  const scene = scenes[activeScene];
  if (!scene) return;
  if (sceneTitleInput) scene.title = sceneTitleInput.value;
  if (sceneDescriptionInput) scene.description = sceneDescriptionInput.value;
  if (dialogueInput) scene.dialogue = dialogueInput.value;
  if (captionInput) scene.caption = captionInput.value;
  refreshSceneSelection();
}

/* ───────── Персонажи ───────── */
function buildCharactersText() {
  return characters
    .map((c) => {
      const name = (c.name || "").trim();
      const desc = (c.description || "").trim();
      const hasReference = Boolean(c.referenceImage);
      const referenceNote = hasReference ? "есть фото-референс" : "";
      if (!name && !desc && !hasReference) return "";
      if (name && desc && referenceNote) return `${name}: ${desc} (${referenceNote})`;
      if (name && desc) return `${name}: ${desc}`;
      if (name && referenceNote) return `${name}: ${referenceNote}`;
      if (desc && referenceNote) return `${desc} (${referenceNote})`;
      return name || desc || referenceNote;
    })
    .filter(Boolean)
    .join("\n");
}

function renderCharacters() {
  if (!characterListEl) return;
  characterListEl.innerHTML = "";

  characters.forEach((character, index) => {
    const hasReference = Boolean(character.referenceImage);
    const card = document.createElement("div");
    card.className = "character-card";
    card.dataset.characterIndex = String(index);
    card.innerHTML = `
      <div class="character-card-head">
        <input type="text" data-character-name placeholder="Имя персонажа" value="${escapeHtml(character.name || "")}" />
        <button class="character-remove" type="button" aria-label="Удалить персонажа" data-character-remove>
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 21a2 2 0 0 1-2-2V7H4V5h5V3h6v2h5v2h-1v12a2 2 0 0 1-2 2H7zm2-3h2V8H9v10zm4 0h2V8h-2v10z" /></svg>
        </button>
      </div>
      <div class="character-reference">
        <div class="character-reference-preview ${hasReference ? "" : "is-empty"}">
          ${hasReference
            ? `<img src="${escapeHtml(character.referenceImage)}" alt="Референс персонажа" />`
            : `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5a4 4 0 1 1 0 8 4 4 0 0 1 0-8zm0 10c4.4 0 8 2.2 8 5v1H4v-1c0-2.8 3.6-5 8-5z" /></svg>`}
        </div>
        <label class="character-reference-upload">
          <input type="file" accept="image/*" data-character-reference />
          <span>${hasReference ? "Заменить фото" : "Добавить фото"}</span>
        </label>
        <button class="character-reference-clear" type="button" data-character-reference-clear ${hasReference ? "" : "hidden"}>Убрать</button>
      </div>
      <textarea data-character-description placeholder="Внешность, характер, роль">${escapeHtml(character.description || "")}</textarea>
    `;

    const nameInput = card.querySelector("[data-character-name]");
    const descInput = card.querySelector("[data-character-description]");
    const removeBtn = card.querySelector("[data-character-remove]");
    const referenceInput = card.querySelector("[data-character-reference]");
    const referenceClear = card.querySelector("[data-character-reference-clear]");

    let nameTimer;
    let descTimer;
    nameInput.addEventListener("input", () => {
      characters[index].name = nameInput.value;
      window.clearTimeout(nameTimer);
      nameTimer = window.setTimeout(pushHistory, 600);
    });
    descInput.addEventListener("input", () => {
      characters[index].description = descInput.value;
      window.clearTimeout(descTimer);
      descTimer = window.setTimeout(pushHistory, 600);
    });
    referenceInput?.addEventListener("change", async () => {
      const file = referenceInput.files?.[0];
      if (!file) return;
      if (!file.type.startsWith("image/")) {
        showToast("Выберите файл изображения.");
        referenceInput.value = "";
        return;
      }
      characters[index].referenceImage = await readImageFileAsDataUrl(file);
      renderCharacters();
      pushHistory();
      showToast("Фото персонажа добавлено как референс.");
    });
    referenceClear?.addEventListener("click", () => {
      delete characters[index].referenceImage;
      renderCharacters();
      pushHistory();
      showToast("Фото персонажа убрано.");
    });
    removeBtn.addEventListener("click", () => removeCharacter(index));

    characterListEl.appendChild(card);
  });
}

function readImageFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const img = new Image();
      img.onload = () => {
        const maxSide = 1024;
        const scale = Math.min(1, maxSide / Math.max(img.naturalWidth, img.naturalHeight));
        const canvas = document.createElement("canvas");
        canvas.width = Math.max(1, Math.round(img.naturalWidth * scale));
        canvas.height = Math.max(1, Math.round(img.naturalHeight * scale));
        const ctx = canvas.getContext("2d");
        if (!ctx) {
          reject(new Error("Не удалось обработать изображение."));
          return;
        }
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        resolve(canvas.toDataURL("image/jpeg", 0.85));
      };
      img.onerror = () => reject(new Error("Не удалось загрузить изображение."));
      img.src = String(reader.result || "");
    };
    reader.onerror = () => reject(reader.error || new Error("Не удалось прочитать изображение."));
    reader.readAsDataURL(file);
  });
}

function addCharacter() {
  characters.push({ name: "", description: "" });
  renderCharacters();
  pushHistory();
  const inputs = characterListEl?.querySelectorAll("[data-character-name]");
  inputs?.[inputs.length - 1]?.focus();
}

function removeCharacter(index) {
  characters.splice(index, 1);
  renderCharacters();
  pushHistory();
  showToast("Персонаж удален.");
}

/* ───────── Кол-во страниц ───────── */
function setPageCount(value) {
  const next = Math.max(1, Math.min(MAX_PAGE_COUNT, Math.round(Number(value) || 1)));
  pageCount = next;
  if (pageCountInput) pageCountInput.value = String(next);
  updateCostNote();
  pushHistory();
}

/* ───────── Язык диалогов ───────── */
function setDialogueLanguage(value, save = true) {
  dialogueLanguage = value || "ru";
  if (dialogueLanguageSelect) dialogueLanguageSelect.value = dialogueLanguage;
  if (save) pushHistory();
}

/* ───────── AI вызовы ───────── */
async function callAiText(task, extra = {}) {
  const scene = scenes[activeScene] || {};
  const basePayload = {
    task,
    story: storyInput?.value.trim() || "",
    characters: buildCharactersText(),
    style: activeStyle,
    tone: dialogueLanguage,
    language: dialogueLanguage,
    pageCount,
    sceneTitle: scene.title,
    sceneDescription: scene.description,
    selected_scene: [scene.title, scene.description].filter(Boolean).join(": "),
    dialogue: scene.dialogue,
    caption: scene.caption,
  };
  return apiFetch("/api/v1/ai-text", {
    method: "POST",
    body: JSON.stringify({ ...basePayload, ...extra }),
  });
}

async function enhanceStory() {
  if (!storyInput) return;
  const story = storyInput.value.trim();
  if (!story) {
    showToast("Сначала напишите хотя бы несколько слов истории.");
    return;
  }
  toggleBusy(enhanceStoryButton, true);
  try {
    const { text } = await callAiText("enhance");
    if (text) {
      storyInput.value = text;
      updateStoryCounter();
      pushHistory();
      showToast("История улучшена AI.");
    }
  } catch (error) {
    showToast(error.message);
  } finally {
    toggleBusy(enhanceStoryButton, false);
  }
}

async function regenerateDialogue() {
  if (!dialogueInput) return;
  if (!scenes.length) {
    showToast("Добавьте или сгенерируйте сцену для диалога.");
    return;
  }
  if (!storyInput?.value.trim()) {
    showToast("Добавьте описание истории для генерации диалога.");
    return;
  }
  toggleBusy(regenerateDialogueButton, true);
  try {
    const { text } = await callAiText("dialogue");
    if (text) {
      dialogueInput.value = text;
      syncSceneFromInputs();
      pushHistory();
      showToast("Диалог обновлен.");
    }
  } catch (error) {
    showToast(error.message);
  } finally {
    toggleBusy(regenerateDialogueButton, false);
  }
}

async function generateCaption() {
  if (!captionInput) return;
  if (!scenes.length) {
    showToast("Добавьте или сгенерируйте сцену для подписи.");
    return;
  }
  if (!storyInput?.value.trim()) {
    showToast("Добавьте описание истории для генерации подписи.");
    return;
  }
  toggleBusy(generateCaptionButton, true);
  try {
    const { text } = await callAiText("caption");
    if (text) {
      captionInput.value = text;
      syncSceneFromInputs();
      pushHistory();
      showToast("Подпись создана.");
    }
  } catch (error) {
    showToast(error.message);
  } finally {
    toggleBusy(generateCaptionButton, false);
  }
}

async function suggestScenes() {
  if (!storyInput?.value.trim()) {
    showToast("Сначала опишите историю.");
    return;
  }
  toggleBusy(suggestScenesButton, true);
  try {
    saveCurrentToContext();
    const ctx = pageContexts[activePage];
    const { scenes: aiScenes } = await callAiText("scenes", {
      story: (ctx?.pageOutline || ctx?.story || storyInput?.value || "").trim(),
      page: activePage + 1,
      pagesTotal: Math.max(1, pageCount),
    });
    if (!Array.isArray(aiScenes) || !aiScenes.length) {
      throw new Error("Модель не вернула сцены.");
    }
    const mapped = mapAiScenes(aiScenes, scenes);
    if (!mapped.length) {
      throw new Error("Модель не вернула подходящие сцены.");
    }
    scenes.length = 0;
    mapped.forEach((s) => scenes.push(s));
    activeScene = 0;
    renderScenes();
    setScene(0);
    pushHistory();
    showToast(`Раскадровка готова: ${scenes.length} сцен.`);
  } catch (error) {
    showToast(error.message);
  } finally {
    toggleBusy(suggestScenesButton, false);
  }
}

function addScene(save = true) {
  const sceneNumber = scenes.length + 1;
  scenes.push({
    title: `Сцена ${sceneNumber}`,
    description: "",
    dialogue: "",
    caption: "",
  });
  activeScene = scenes.length - 1;
  renderScenes();
  setScene(activeScene, false);
  if (save) pushHistory();
  showToast("Сцена добавлена.");
}

function hasMeaningfulScenes(list) {
  return (list || []).some((scene) => {
    const title = (scene?.title || "").trim();
    const defaultTitle = /^\u0421\u0446\u0435\u043d\u0430\s+\d+$/i.test(title);
    return (
      (title && !defaultTitle) ||
      (scene?.description || "").trim() ||
      (scene?.dialogue || "").trim() ||
      (scene?.caption || "").trim()
    );
  });
}

function mapAiScenes(aiScenes, existingScenes = []) {
  return (aiScenes || [])
    .map((scene, index) => {
      if (typeof scene === "string") {
        return {
          title: `Сцена ${index + 1}`,
          description: scene,
          dialogue: existingScenes[index]?.dialogue || "",
          caption: existingScenes[index]?.caption || "",
        };
      }
      return {
        title: scene?.title || `Сцена ${index + 1}`,
        description: scene?.description || "",
        dialogue: scene?.dialogue || existingScenes[index]?.dialogue || "",
        caption: scene?.caption || existingScenes[index]?.caption || "",
      };
    })
    .filter((scene) =>
      scene.title.trim() ||
      scene.description.trim() ||
      scene.dialogue.trim() ||
      scene.caption.trim()
    );
}

function buildPagePlanContext(ctx) {
  const outline = (ctx?.pageOutline || "").trim();
  if (outline) return outline;

  const summary = (ctx?.summary || "").trim();
  if (summary) return summary;

  const pageScenes = (ctx?.scenes || [])
    .map((scene, index) => {
      const title = (scene.title || `Сцена ${index + 1}`).trim();
      const description = (scene.description || "").trim();
      const dialogue = (scene.dialogue || "").trim();
      const caption = (scene.caption || "").trim();
      return [title, description, dialogue, caption].filter(Boolean).join("; ");
    })
    .filter(Boolean)
    .join(" | ");

  return pageScenes || (ctx?.story || "").trim();
}

async function autoGenerateScenesIfNeeded(pageIndex, options = {}) {
  const ctx = pageContexts[pageIndex];
  if (ctx && !Array.isArray(ctx.scenes)) ctx.scenes = [];
  if (!ctx || hasMeaningfulScenes(ctx.scenes)) return;

  const story = (ctx.pageOutline || ctx.story || pageContexts[0]?.story || storyInput?.value || "").trim();
  if (!story) return;

  const totalPages = Math.max(1, Number(options.pagesTotal) || pageCount || 1);
  const previousPagesContext = pageContexts
    .slice(0, pageIndex)
    .map(buildPagePlanContext)
    .filter(Boolean);

  setLoading(true, options.label || "Создаём сцены для страницы...");
  const { scenes: aiScenes } = await callAiText("scenes", {
    story,
    characters: buildCharactersTextFor(ctx.characters),
    pageCount: totalPages,
    pagesTotal: totalPages,
    page: Math.max(1, Number(options.pageNumber) || pageIndex + 1),
    previousPagesContext,
  });

  if (!Array.isArray(aiScenes) || !aiScenes.length) {
    throw new Error("Модель не вернула сцены.");
  }

  const mapped = mapAiScenes(aiScenes, ctx.scenes);
  if (!mapped.length) {
    throw new Error("Модель не вернула подходящие сцены.");
  }

  ctx.scenes.length = 0;
  mapped.forEach((scene) => ctx.scenes.push(scene));

  if (pageIndex === activePage) {
    scenes = ctx.scenes;
    activeScene = 0;
    renderScenes();
    setScene(0, false);
  }
}

function mapPageOutlines(aiPages, totalPages) {
  const byPage = new Map();
  (aiPages || []).forEach((item, index) => {
    const page = Math.max(1, Number(item?.page) || index + 1);
    const outline = String(item?.summary || item?.story || item?.outline || "").trim();
    if (outline && page <= totalPages) byPage.set(page, outline);
  });
  return Array.from({ length: totalPages }, (_, index) => byPage.get(index + 1) || "");
}

async function ensurePageOutlinesForGeneration(startIndex, totalPages, sourceCtx) {
  if (totalPages <= 1) return;

  const needsOutline = Array.from({ length: totalPages }, (_, i) => {
    const ctx = pageContexts[startIndex + i];
    return !(ctx?.pageOutline || "").trim();
  }).some(Boolean);
  if (!needsOutline) return;

  const story = (sourceCtx?.story || storyInput?.value || "").trim();
  if (!story) return;

  setLoading(true, "Планируем сюжет по страницам...");
  const { pages: aiPages } = await callAiText("pagePlan", {
    story,
    characters: buildCharactersTextFor(sourceCtx?.characters || characters),
    pageCount: totalPages,
    pagesTotal: totalPages,
  });

  const outlines = mapPageOutlines(aiPages, totalPages);
  if (outlines.filter(Boolean).length !== totalPages) {
    throw new Error("Модель не смогла разложить сюжет по страницам.");
  }

  outlines.forEach((outline, i) => {
    const ctx = pageContexts[startIndex + i];
    if (ctx) ctx.pageOutline = outline;
  });
}

function toggleBusy(button, isBusy) {
  if (!button) return;
  button.disabled = isBusy;
  button.classList.toggle("is-busy", isBusy);
}

function buildCharactersTextFor(list) {
  return (list || [])
    .map((c) => {
      const name = (c.name || "").trim();
      const desc = (c.description || "").trim();
      const hasReference = Boolean(c.referenceImage);
      const referenceNote = hasReference ? "есть фото-референс" : "";
      if (!name && !desc && !hasReference) return "";
      if (name && desc && referenceNote) return `${name}: ${desc} (${referenceNote})`;
      if (name && desc) return `${name}: ${desc}`;
      if (name && referenceNote) return `${name}: ${referenceNote}`;
      if (desc && referenceNote) return `${desc} (${referenceNote})`;
      return name || desc || referenceNote;
    })
    .filter(Boolean)
    .join("\n");
}

function buildCharacterImageRefsFor(list) {
  return (list || [])
    .map((c, index) => ({
      name: (c.name || `Character ${index + 1}`).trim() || `Character ${index + 1}`,
      imageUrl: c.referenceImage || "",
    }))
    .filter((c) => c.imageUrl);
}

function buildScenePayload(pageIndex, options = {}) {
  saveCurrentToContext();
  const ctx = pageContexts[pageIndex] || pageContexts[activePage] || createDefaultPageContext();
  const ctxScenes = ctx.scenes || [];
  const ctxStory = (ctx.pageOutline || ctx.story || "").trim();

  const scenePrompts = ctxScenes
    .map((scene, index) => {
      const parts = [
        scene.title || `Сцена ${index + 1}`,
        scene.description ? `описание: ${scene.description}` : "",
        scene.dialogue ? `диалог: ${scene.dialogue}` : "",
        scene.caption ? `подпись: ${scene.caption}` : "",
      ].filter(Boolean);
      return parts.length > 1 || scene.description || scene.dialogue || scene.caption
        ? parts.join("; ")
        : "";
    })
    .filter(Boolean);

  const isActivePage = pageIndex === activePage;
  const focusScene = isActivePage ? ctxScenes[activeScene] : null;

  const previousPagesContext = pageContexts
    .slice(0, pageIndex)
    .map((c) => (c?.summary || c?.story || "").trim())
    .filter(Boolean);

  const resolvedPagesTotal = typeof options.pagesTotal === "number"
    ? Math.max(1, options.pagesTotal)
    : (ctx.pageCount && isActivePage ? ctx.pageCount : 1);

  return {
    story: ctxStory,
    characters: buildCharactersTextFor(ctx.characters),
    characterImages: buildCharacterImageRefsFor(ctx.characters),
    style: activeStyle,
    language: dialogueLanguage,
    model: activeModel,
    page: Math.max(1, Number(options.pageNumber) || pageIndex + 1),
    pagesTotal: resolvedPagesTotal,
    selectedScene: ctxScenes.length && isActivePage ? activeScene + 1 : null,
    scenes: scenePrompts,
    dialogue: focusScene?.dialogue || (isActivePage ? (dialogueInput?.value.trim() || "") : ""),
    caption: focusScene?.caption || (isActivePage ? (captionInput?.value.trim() || "") : ""),
    layout: "single full comic page, cinematic panel layout, readable speech bubbles, high contrast",
    previousPagesContext,
  };
}

function createIdempotencyKey(pageIndex) {
  if (window.crypto?.randomUUID) return window.crypto.randomUUID();
  return `comicly-${Date.now()}-${pageIndex}-${Math.random().toString(16).slice(2)}`;
}

function buildGenerationPayload(pageIndex, options = {}) {
  const snapshot = buildScenePayload(pageIndex, options);
  const ctx = pageContexts[pageIndex] || pageContexts[activePage] || {};
  const scene = pageIndex === activePage ? scenes[activeScene] : (ctx.scenes || [])[0];

  return {
    comic_id: currentComicId,
    scene_id: scene?.backendSceneId || null,
    page_number: Math.max(1, pageIndex + 1),
    story: snapshot.story,
    characters: snapshot.characters,
    style: snapshot.style,
    tone: dialogueLanguage,
    selected_scene: snapshot.selectedScene ? String(snapshot.selectedScene) : null,
    scenes: snapshot.scenes,
    dialogue: snapshot.dialogue,
    caption: snapshot.caption,
    layout: snapshot.layout,
    model_id: snapshot.model,
  };
}

async function generateSinglePage(pageIndex, label, options = {}) {
  while (pages.length <= pageIndex) {
    pages.push(createPlaceholderDataUrl(pages.length + 1));
  }
  while (pageContexts.length <= pageIndex) {
    const inheritFrom = pageContexts[activePage] || pageContexts[0];
    pageContexts.push(createDefaultPageContext({
      story: inheritFrom?.story || "",
      characters: (inheritFrom?.characters || []).map((c) => ({ ...c })),
    }));
  }
  const ctx = pageContexts[pageIndex];
  const inheritFrom = pageContexts[activePage] || pageContexts[0];
  if (ctx && !(ctx.story || "").trim()) ctx.story = inheritFrom?.story || "";
  if (ctx && !(ctx.characters || []).length) {
    ctx.characters = (inheritFrom?.characters || []).map((c) => ({ ...c }));
  }
  await autoGenerateScenesIfNeeded(pageIndex, {
    pagesTotal: options.pagesTotal,
    pageNumber: options.pageNumber,
    label: "Создаём сцены для страницы...",
  });
  await saveCurrentComic({ required: true });
  const payload = buildGenerationPayload(pageIndex, options);
  setLoading(true, label);

  const data = await apiFetch("/api/v1/generations", {
    method: "POST",
    headers: { "Idempotency-Key": createIdempotencyKey(pageIndex) },
    body: JSON.stringify(payload),
  });

  const imageUrl = data.image_url || data.page?.image_url;
  if (!imageUrl) {
    throw new Error("Backend не вернул ссылку на изображение.");
  }

  pages[pageIndex] = imageUrl;
  if (pageContexts[pageIndex]) {
    pageContexts[pageIndex].generated = true;
    pageContexts[pageIndex].backendPageId = data.page?.id || pageContexts[pageIndex].backendPageId;
    pageContexts[pageIndex].backendSceneId = data.page?.scene_id || pageContexts[pageIndex].backendSceneId;
  }
  if (typeof data.balance === "number") {
    credits = data.balance;
    updateCreditBalance();
  }

  setPage(pageIndex, false);
  renderPageStrip();
  if (comicOutput) comicOutput.src = imageUrl;
  if (emptyState) emptyState.hidden = true;
  refreshContinueButton();
  await saveCurrentComic({ includePages: true });

  return data;
}

function hasMeaningfulCharacters(list) {
  return (list || []).some((c) =>
    (c?.name || "").trim() || (c?.description || "").trim() || c?.referenceImage
  );
}

function isFirstGeneration() {
  return !pageContexts.some((c) => c?.generated);
}

async function autoExtractCharactersIfNeeded() {
  const ctx = pageContexts[activePage];
  if (!ctx) return;
  if (!isFirstGeneration()) return;
  if (hasMeaningfulCharacters(ctx.characters)) return;

  const story = (ctx.story || storyInput?.value || "").trim();
  if (!story) return;

  setLoading(true, "Создаём персонажей по истории...");
  try {
    const { characters: aiChars } = await callAiText("characters");
    if (!Array.isArray(aiChars) || !aiChars.length) return;
    const mapped = aiChars
      .map((c) => ({
        name: typeof c?.name === "string" ? c.name.trim() : "",
        description: typeof c?.description === "string" ? c.description.trim() : "",
      }))
      .filter((c) => c.name || c.description);
    if (!mapped.length) return;

    ctx.characters.length = 0;
    mapped.forEach((c) => ctx.characters.push(c));
    // characters — это ссылка на ctx.characters, поэтому достаточно перерисовать
    renderCharacters();
    showToast(`AI создал ${mapped.length} персонажей по истории — можете отредактировать в «Расширенных настройках».`);
  } catch {
    // best-effort — даже без авто-персонажей продолжаем основную генерацию
  }
}

async function generateComicPage(triggerButton = generatePageButton) {
  saveCurrentToContext();
  if (!storyInput?.value.trim()) {
    showToast("Добавьте описание истории перед генерацией.");
    return;
  }

  const totalPages = Math.max(1, pageCount);
  const startIndex = activePage;
  const sourceCtx = pageContexts[startIndex];

  activeGenerationButton = triggerButton;
  toggleBusy(activeGenerationButton, true);
  try {
    await ensureCurrentComic();
    await autoExtractCharactersIfNeeded();

    for (let i = 0; i < totalPages; i += 1) {
      const targetIndex = totalPages > 1 ? startIndex + i : startIndex;
      while (pages.length <= targetIndex) {
        pages.push(createPlaceholderDataUrl(pages.length + 1));
      }
      while (pageContexts.length <= targetIndex) {
        pageContexts.push(createDefaultPageContext({
          story: sourceCtx?.story || "",
          characters: (sourceCtx?.characters || []).map((c) => ({ ...c })),
        }));
      }
      const targetCtx = pageContexts[targetIndex];
      if (targetCtx && !(targetCtx.story || "").trim()) {
        targetCtx.story = sourceCtx?.story || "";
      }
      if (targetCtx && !(targetCtx.characters || []).length) {
        targetCtx.characters = (sourceCtx?.characters || []).map((c) => ({ ...c }));
      }
    }

    await ensurePageOutlinesForGeneration(startIndex, totalPages, sourceCtx);

    for (let i = 0; i < totalPages; i += 1) {
      const targetIndex = totalPages > 1 ? startIndex + i : startIndex;
      const label = totalPages > 1
        ? `Генерируем страницу ${i + 1} из ${totalPages}...`
        : "Генерируем страницу/изображение...";
      await generateSinglePage(targetIndex, label, { pagesTotal: totalPages, pageNumber: i + 1 });
      void generatePageSummary(targetIndex);
    }
    pushHistory();
    showToast(totalPages > 1 ? `Готово: ${totalPages} страниц.` : "Страница сгенерирована.");
  } catch (error) {
    if (error instanceof ApiClientError && error.status === 401) {
      setAuthOverlayVisible(true);
    }
    showToast(error.message || "Не удалось сгенерировать страницу.");
  } finally {
    toggleBusy(activeGenerationButton, false);
    activeGenerationButton = null;
    setLoading(false);
  }
}

async function generatePageSummary(pageIndex) {
  const ctx = pageContexts[pageIndex];
  if (!ctx) return;
  const baseStory = (ctx.pageOutline || ctx.story || "").trim();
  if (!baseStory) return;

  const sceneDescription = (ctx.scenes || [])
    .map((s) => {
      const t = (s.title || "").trim();
      const d = (s.description || "").trim();
      if (!t && !d) return "";
      if (t && d) return `${t}: ${d}`;
      return t || d;
    })
    .filter(Boolean)
    .join("; ");
  const dialogue = (ctx.scenes || [])
    .map((s) => (s.dialogue || "").trim())
    .filter(Boolean)
    .join("\n");
  const charsText = buildCharactersTextFor(ctx.characters);

  try {
    const { text } = await callAiText("summarize", {
      story: baseStory,
      characters: charsText,
      sceneDescription,
      dialogue,
    });
    if (text && pageContexts[pageIndex]) {
      pageContexts[pageIndex].summary = text.trim();
    }
  } catch {
    // Резюме — best-effort, без него продолжение работает по основному сюжету.
  }
}

function findLastGeneratedIndex() {
  for (let i = pageContexts.length - 1; i >= 0; i -= 1) {
    if (pageContexts[i]?.generated) return i;
  }
  for (let i = pages.length - 1; i >= 0; i -= 1) {
    if (typeof pages[i] === "string" && !isPlaceholderImage(pages[i])) return i;
  }
  return -1;
}

function refreshContinueButton() {
  if (!continueButton) return;
  const hasAnyGenerated = findLastGeneratedIndex() >= 0;
  continueButton.disabled = !hasAnyGenerated;
  continueButton.title = hasAnyGenerated
    ? "AI продолжит сюжет на основе уже сгенерированных страниц"
    : "Сначала сгенерируйте хотя бы одну страницу — потом её можно будет продолжать";
}

async function continueStory() {
  saveCurrentToContext();

  const ctx = pageContexts[activePage];
  if (!ctx) return;

  const lastGenerated = findLastGeneratedIndex();
  if (lastGenerated < 0) {
    showToast("Сначала сгенерируйте хотя бы одну страницу — потом я смогу её продолжить.");
    return;
  }

  const baseStory = (pageContexts[0]?.story || ctx.story || "").trim();
  if (!baseStory) {
    showToast("Опишите историю в сюжете, чтобы я знал, что продолжать.");
    return;
  }

  // Решаем: заполнить текущую пустую страницу ИЛИ создать новую после.
  const currentIsEmptyDraft =
    !ctx.generated &&
    !(ctx.story || "").trim() &&
    !(ctx.scenes || []).length;
  // Самый нижний контекст для продолжения — последняя сгенерированная страница до текущего слота.
  const refIndex = currentIsEmptyDraft
    ? Math.min(lastGenerated, activePage - 1)
    : lastGenerated;
  const summarySource = pageContexts.slice(0, refIndex + 1);

  toggleBusy(continueButton, true);
  setLoading(true, "Придумываем продолжение...");
  try {
    await ensureCurrentComic();
    const previousSummaries = summarySource
      .map((c) => (c?.summary || c?.story || "").trim())
      .filter(Boolean);

    const charsMap = new Map();
    summarySource.forEach((c) => {
      (c?.characters || []).forEach((ch) => {
        const key = (ch.name || "").trim().toLowerCase() || `__anon_${charsMap.size}`;
        if (!charsMap.has(key)) charsMap.set(key, ch);
      });
    });
    const allCharsText = buildCharactersTextFor(Array.from(charsMap.values()));

    const { text } = await callAiText("continue", {
      story: baseStory,
      characters: allCharsText,
      previousPagesContext: previousSummaries,
    });
    const continuationText = (text || "").trim();
    if (!continuationText) throw new Error("Модель не вернула продолжение.");

    let targetIndex;
    if (currentIsEmptyDraft) {
      targetIndex = activePage;
      ctx.story = continuationText;
      if (!(ctx.characters || []).length && pageContexts[refIndex]) {
        ctx.characters = (pageContexts[refIndex].characters || []).map((c) => ({ ...c }));
      }
      loadActivePageContext();
    } else {
      targetIndex = activePage + 1;
      pages.splice(targetIndex, 0, createPlaceholderDataUrl(targetIndex + 1));
      pageContexts.splice(targetIndex, 0, createDefaultPageContext({
        story: continuationText,
        characters: (ctx.characters || pageContexts[refIndex]?.characters || []).map((c) => ({ ...c })),
      }));
      renderPageStrip();
      setPage(targetIndex, false);
    }

    setLoading(true, "Генерируем страницу...");
    await generateSinglePage(targetIndex, "Генерируем страницу...", { pagesTotal: 1 });
    void generatePageSummary(targetIndex);

    pushHistory();
    showToast("Продолжение готово.");
  } catch (error) {
    if (error instanceof ApiClientError && error.status === 401) {
      setAuthOverlayVisible(true);
    }
    showToast(error.message || "Не удалось продолжить историю.");
  } finally {
    toggleBusy(continueButton, false);
    setLoading(false);
    refreshContinueButton();
  }
}

function downloadCurrentPage() {
  if (!comicOutput?.src) return;

  const link = document.createElement("a");
  link.href = comicOutput.src;
  link.download = `comicly-page-${activePage + 1}.png`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  showToast("Скачивание страницы начато.");
}

async function shareProject() {
  const shareData = {
    title: projectTitleInput?.value || "comicly.ai",
    text: "Черновик комикса, созданный на comicly.ai",
    url: window.location.href,
  };

  try {
    if (navigator.share) {
      await navigator.share(shareData);
      return;
    }
  } catch {
    // пользователь отменил системный шеринг — падаем в копирование
  }

  try {
    await navigator.clipboard.writeText(shareData.url);
    showToast("Ссылка на проект скопирована.");
  } catch {
    showToast("Не удалось поделиться. Скопируйте адрес вручную.");
  }
}

function addPage() {
  saveCurrentToContext();
  const inheritFrom = pageContexts[activePage];
  pages.push(createPlaceholderDataUrl(pages.length + 1));
  pageContexts.push(createDefaultPageContext({
    characters: (inheritFrom?.characters || []).map((c) => ({ ...c })),
  }));
  renderPageStrip();
  setPage(pages.length - 1);
  pushHistory();
  showToast("Новая страница добавлена. Опишите её сюжет или нажмите «Продолжить историю».");
}

function addCredits() {
  showToast("Пополнение баланса появится после подключения платежей.");
}

function setZoom(value) {
  if (!comicCanvas || !zoomLabel) return;
  const numeric = Number.parseInt(value, 10) || 100;
  zoomLabel.textContent = `${numeric}%`;
  comicCanvas.style.width = `min(100%, ${Math.round(620 * (numeric / 100))}px)`;
}

function toggleProfileMenu(force) {
  if (!profileMenu || !profileToggle) return;
  const shouldOpen = typeof force === "boolean" ? force : profileMenu.hidden;
  profileMenu.hidden = !shouldOpen;
  profileToggle.setAttribute("aria-expanded", String(shouldOpen));
  if (shouldOpen && burgerMenu) {
    burgerMenu.hidden = true;
    burgerToggle?.setAttribute("aria-expanded", "false");
  }
}

function toggleBurgerMenu(force) {
  if (!burgerMenu || !burgerToggle) return;
  const shouldOpen = typeof force === "boolean" ? force : burgerMenu.hidden;
  burgerMenu.hidden = !shouldOpen;
  burgerToggle.setAttribute("aria-expanded", String(shouldOpen));
  if (shouldOpen) toggleProfileMenu(false);
}

function moveScene(index) {
  if (!scenes.length) return;
  if (index <= 0 || index >= scenes.length) {
    const moved = scenes.shift();
    if (moved) scenes.push(moved);
    activeScene = scenes.length - 1;
    showToast("Сцена перемещена в конец списка.");
  } else {
    const [item] = scenes.splice(index, 1);
    scenes.splice(index - 1, 0, item);
    if (activeScene === index) activeScene = index - 1;
    else if (activeScene === index - 1) activeScene = index;
    showToast("Сцена перемещена выше.");
  }
  renderScenes();
  pushHistory();
}

function openSceneMenu(index) {
  setScene(index);
  sceneDescriptionInput?.focus();
  showToast(`${scenes[index]?.title || "Сцена"}: описание готово к редактированию.`);
}

function showConfigBanner() {
  if (!configBanner) return;
  configBanner.hidden = false;
}

async function checkHealth() {
  try {
    await apiFetch("/ready");
  } catch {
    showConfigBanner();
  }
}

async function logout() {
  toggleProfileMenu(false);
  try {
    await apiFetch("/api/v1/me/logout", { method: "POST" });
  } catch {
    // Even if the request fails, local trusted state is cleared.
  }
  resetTrustedState();
  setAuthOverlayVisible(true);
  setSaveStatus("error", "Войдите");
  showToast("Вы вышли из аккаунта.");
}

let storyInputTimer;

storyInput?.addEventListener("input", () => {
  updateStoryCounter();
  window.clearTimeout(storyInputTimer);
  storyInputTimer = window.setTimeout(pushHistory, 700);
});

projectTitleInput?.addEventListener("change", pushHistory);
sceneTitleInput?.addEventListener("input", () => {
  syncSceneFromInputs();
});
sceneTitleInput?.addEventListener("change", pushHistory);
sceneDescriptionInput?.addEventListener("input", () => {
  syncSceneFromInputs();
});
sceneDescriptionInput?.addEventListener("change", pushHistory);
dialogueInput?.addEventListener("input", () => {
  syncSceneFromInputs();
});
dialogueInput?.addEventListener("change", pushHistory);
captionInput?.addEventListener("input", () => {
  syncSceneFromInputs();
});
captionInput?.addEventListener("change", pushHistory);

clearStoryButton?.addEventListener("click", () => {
  if (!storyInput) return;
  storyInput.value = "";
  updateStoryCounter();
  pushHistory();
  showToast("История очищена.");
});

enhanceStoryButton?.addEventListener("click", enhanceStory);
generatePageButton?.addEventListener("click", (event) => generateComicPage(event.currentTarget));
regenerateSceneButton?.addEventListener("click", (event) => generateComicPage(event.currentTarget));
suggestScenesButton?.addEventListener("click", suggestScenes);
addSceneButton?.addEventListener("click", () => addScene());
downloadButton?.addEventListener("click", () => { downloadCurrentPage(); toggleBurgerMenu(false); });
shareButton?.addEventListener("click", () => { shareProject(); toggleBurgerMenu(false); });
addPageButton?.addEventListener("click", addPage);
continueButton?.addEventListener("click", continueStory);
regenerateDialogueButton?.addEventListener("click", regenerateDialogue);
generateCaptionButton?.addEventListener("click", generateCaption);
creditInfoButton?.addEventListener("click", () => {
  window.location.href = "pricing.html";
});
addCreditsButton?.addEventListener("click", addCredits);
notificationsButton?.addEventListener("click", () => showToast("Новых уведомлений нет."));
renameButton?.addEventListener("click", () => {
  projectTitleInput?.focus();
  projectTitleInput?.select();
});
undoButton?.addEventListener("click", () => { undo(); toggleBurgerMenu(false); });
redoButton?.addEventListener("click", () => { redo(); toggleBurgerMenu(false); });
zoomSelect?.addEventListener("change", () => setZoom(zoomSelect.value));
profileToggle?.addEventListener("click", () => toggleProfileMenu());

profileActions.forEach((button) => {
  button.addEventListener("click", () => {
    if (button.dataset.profileAction === "logout") {
      void logout();
      return;
    }
    const labels = {
      profile: "Профиль загружен из backend.",
      settings: "Настройки профиля появятся позже.",
    };
    toggleProfileMenu(false);
    showToast(labels[button.dataset.profileAction] || "Действие выполнено.");
  });
});

burgerToggle?.addEventListener("click", () => toggleBurgerMenu());

addCharacterButton?.addEventListener("click", addCharacter);

pageCountSteps.forEach((btn) => {
  btn.addEventListener("click", () => {
    const delta = Number(btn.dataset.pageCountStep) || 0;
    setPageCount(pageCount + delta);
  });
});

pageCountInput?.addEventListener("input", () => {
  setPageCount(pageCountInput.value);
});

dialogueLanguageSelect?.addEventListener("change", () => {
  setDialogueLanguage(dialogueLanguageSelect.value);
});

document.addEventListener("click", (event) => {
  if (profileMenu && !profileMenu.hidden) {
    if (!profileMenu.contains(event.target) && !profileToggle?.contains(event.target)) {
      toggleProfileMenu(false);
    }
  }
  if (burgerMenu && !burgerMenu.hidden) {
    if (!burgerMenu.contains(event.target) && !burgerToggle?.contains(event.target)) {
      toggleBurgerMenu(false);
    }
  }
  const insideDropdown = dropdowns.some((wrap) => wrap.contains(event.target));
  if (!insideDropdown) closeAllDropdowns();
});

renderCharacters();
renderPageStrip();
renderScenes();
updateStoryCounter();
updateCreditBalance();
updateCostNote();
setPage(activePage, false);
setStyle(activeStyle, false);
setModel(activeModel, false);
setScene(activeScene, false);
setZoom(zoomSelect?.value || "100%");
pushHistory();
bootstrapSession();
