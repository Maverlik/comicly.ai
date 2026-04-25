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

const DEFAULT_MODEL_ID = "bytedance-seed/seedream-4.5";
const PRICE_PER_PAGE = 20;
const MAX_PAGE_COUNT = 10;

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

let pages = [createPlaceholderDataUrl(1)];
let pageImages = ["assets/comic-preview-fantasy.png"];
let scenes = [];
let characters = [];

let activeStyle = "Аниме";
let activeModel = DEFAULT_MODEL_ID;
let pageCount = 1;
let dialogueLanguage = "ru";

let activePage = 0;
let activeScene = 0;
let credits = 240;
let apiKeyReady = false;
let isRestoring = false;
let historyIndex = -1;
let history = [];

function showToast(message) {
  if (!toast) return;
  toast.textContent = message;
  toast.hidden = false;

  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => {
    toast.hidden = true;
  }, 3800);
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
  return {
    title: projectTitleInput?.value || "",
    story: storyInput?.value || "",
    characters: characters.map((c) => ({ ...c })),
    style: activeStyle,
    model: activeModel,
    pageCount,
    dialogueLanguage,
    activePage,
    activeScene,
    pages: [...pages],
    scenes: scenes.map((scene) => ({ ...scene })),
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
}

function restoreSnapshot(snapshot) {
  isRestoring = true;

  if (projectTitleInput) projectTitleInput.value = snapshot.title;
  if (storyInput) storyInput.value = snapshot.story;
  characters = (snapshot.characters || []).map((c) => ({ ...c }));
  pages = [...snapshot.pages];
  scenes = snapshot.scenes.map((scene) => ({ ...scene }));
  credits = snapshot.credits;
  pageCount = snapshot.pageCount || 1;
  dialogueLanguage = snapshot.dialogueLanguage || "ru";

  if (pageCountInput) pageCountInput.value = String(pageCount);
  if (dialogueLanguageSelect) dialogueLanguageSelect.value = dialogueLanguage;

  renderCharacters();
  renderPageStrip();
  renderScenes();
  updateStoryCounter();
  updateCreditBalance();
  updateCostNote();
  setStyle(snapshot.style, false);
  setModel(snapshot.model || DEFAULT_MODEL_ID, false);
  if (scenes.length) setScene(Math.min(snapshot.activeScene, scenes.length - 1), false);
  else refreshSceneSelection();
  setPage(Math.min(snapshot.activePage, pages.length - 1), false);

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
  if (creditBalance) creditBalance.textContent = `${credits} кредитов`;
}

function updateCostNote() {
  if (costValueEl) costValueEl.textContent = String(PRICE_PER_PAGE * pageCount);
}

function setLoading(isLoading, label = "Генерируем страницу...") {
  if (comicLoading) comicLoading.hidden = !isLoading;
  if (loadingLabel && label) loadingLabel.textContent = label;
  if (generatePageButton) generatePageButton.disabled = isLoading;
  if (regenerateSceneButton) regenerateSceneButton.disabled = isLoading;
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

  pageThumbs.forEach((thumb) => thumb.remove());
  pageThumbs = pages.map((src, index) => {
    const button = document.createElement("button");
    button.className = "page-thumb";
    button.type = "button";
    button.dataset.pageThumb = String(index);
    button.innerHTML = `<img src="${src}" alt="Страница ${index + 1}" /><span>${index + 1}</span>`;
    button.addEventListener("click", () => setPage(index));
    pageStrip.insertBefore(button, addPageButton);
    return button;
  });
  pageThumbs.forEach((thumb) => {
    thumb.classList.toggle("is-active", Number(thumb.dataset.pageThumb) === activePage);
  });
  if (pageStatus) pageStatus.textContent = `Страница ${activePage + 1} из ${pages.length}`;
}

function setPage(index, save = true) {
  if (!pages[index]) return;
  activePage = index;

  pageThumbs.forEach((thumb) => {
    thumb.classList.toggle("is-active", Number(thumb.dataset.pageThumb) === index);
  });

  if (pageStatus) pageStatus.textContent = `Страница ${index + 1} из ${pages.length}`;
  if (comicOutput) {
    comicOutput.src = pages[index];
    comicOutput.hidden = false;
  }
  if (emptyState) emptyState.hidden = true;
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
      if (!name && !desc) return "";
      if (name && desc) return `${name}: ${desc}`;
      return name || desc;
    })
    .filter(Boolean)
    .join("\n");
}

function renderCharacters() {
  if (!characterListEl) return;
  characterListEl.innerHTML = "";

  characters.forEach((character, index) => {
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
      <textarea data-character-description placeholder="Внешность, характер, роль">${escapeHtml(character.description || "")}</textarea>
    `;

    const nameInput = card.querySelector("[data-character-name]");
    const descInput = card.querySelector("[data-character-description]");
    const removeBtn = card.querySelector("[data-character-remove]");

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
    removeBtn.addEventListener("click", () => removeCharacter(index));

    characterListEl.appendChild(card);
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
function setDialogueLanguage(value) {
  dialogueLanguage = value || "ru";
  if (dialogueLanguageSelect) dialogueLanguageSelect.value = dialogueLanguage;
  pushHistory();
}

/* ───────── AI вызовы ───────── */
async function callAiText(task) {
  const scene = scenes[activeScene] || {};
  const response = await fetch("/api/ai-text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      task,
      story: storyInput?.value.trim() || "",
      characters: buildCharactersText(),
      style: activeStyle,
      language: dialogueLanguage,
      pageCount,
      sceneTitle: scene.title,
      sceneDescription: scene.description,
      dialogue: scene.dialogue,
      caption: scene.caption,
    }),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = data?.error || "Сервис AI недоступен.";
    if (data?.code === "MISSING_KEY") showConfigBanner();
    throw new Error(message);
  }
  return data;
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
    const { scenes: aiScenes } = await callAiText("scenes");
    if (!Array.isArray(aiScenes) || !aiScenes.length) {
      throw new Error("Модель не вернула сцены.");
    }
    scenes = aiScenes.map((scene, index) => ({
      title: scene.title || `Сцена ${index + 1}`,
      description: scene.description || "",
      dialogue: scene.dialogue || scenes[index]?.dialogue || "",
      caption: scene.caption || scenes[index]?.caption || "",
    }));
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

function toggleBusy(button, isBusy) {
  if (!button) return;
  button.disabled = isBusy;
  button.classList.toggle("is-busy", isBusy);
}

function buildScenePayload(pageIndex) {
  const scenePrompts = scenes
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

  return {
    story: storyInput?.value.trim() || "",
    characters: buildCharactersText(),
    style: activeStyle,
    language: dialogueLanguage,
    model: activeModel,
    page: pageIndex + 1,
    pagesTotal: pageCount,
    selectedScene: scenes.length ? activeScene + 1 : null,
    scenes: scenePrompts,
    dialogue: dialogueInput?.value.trim() || "",
    caption: captionInput?.value.trim() || "",
    layout: "single full comic page, cinematic panel layout, readable speech bubbles, high contrast",
  };
}

async function generateSinglePage(pageIndex, label) {
  const payload = buildScenePayload(pageIndex);
  setLoading(true, label);

  const response = await fetch("/api/generate-comic-page", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (data?.code === "MISSING_KEY") showConfigBanner();
    throw new Error(data?.error || "Не удалось сгенерировать страницу.");
  }
  if (!data.imageUrl) {
    throw new Error("OpenRouter не вернул изображение.");
  }

  while (pages.length <= pageIndex) {
    pages.push(createPlaceholderDataUrl(pages.length + 1));
  }
  pages[pageIndex] = data.imageUrl;

  setPage(pageIndex, false);
  renderPageStrip();
  if (comicOutput) comicOutput.src = data.imageUrl;
  if (emptyState) emptyState.hidden = true;

  return data;
}

async function generateComicPage() {
  if (!storyInput?.value.trim()) {
    showToast("Добавьте описание истории перед генерацией.");
    return;
  }

  const totalPages = Math.max(1, pageCount);
  const totalCost = PRICE_PER_PAGE * totalPages;
  if (credits < totalCost) {
    showToast(`Недостаточно кредитов. Нужно ${totalCost}.`);
    return;
  }

  const startIndex = activePage;

  try {
    for (let i = 0; i < totalPages; i += 1) {
      const targetIndex = totalPages > 1 ? startIndex + i : startIndex;
      const label = totalPages > 1
        ? `Генерируем страницу ${i + 1} из ${totalPages}...`
        : "Генерируем страницу...";
      await generateSinglePage(targetIndex, label);
      credits = Math.max(0, credits - PRICE_PER_PAGE);
      updateCreditBalance();
    }
    pushHistory();
    showToast(totalPages > 1 ? `Готово: ${totalPages} страниц.` : "Страница сгенерирована.");
  } catch (error) {
    showToast(error.message);
  } finally {
    setLoading(false);
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
  pages.push(createPlaceholderDataUrl(pages.length + 1));
  renderPageStrip();
  setPage(pages.length - 1);
  pushHistory();
  showToast("Новая страница добавлена. Нажмите «Сгенерировать страницу».");
}

function addCredits() {
  credits += 100;
  updateCreditBalance();
  pushHistory();
  showToast("Добавлено 100 кредитов.");
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
    const response = await fetch("/api/health");
    const data = await response.json();
    apiKeyReady = Boolean(data?.hasApiKey);
    if (!apiKeyReady) showConfigBanner();
  } catch {
    // Сервер может не поддерживать эндпоинт; считаем что ключ может быть.
  }
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
generatePageButton?.addEventListener("click", generateComicPage);
regenerateSceneButton?.addEventListener("click", generateComicPage);
suggestScenesButton?.addEventListener("click", suggestScenes);
addSceneButton?.addEventListener("click", () => addScene());
downloadButton?.addEventListener("click", () => { downloadCurrentPage(); toggleBurgerMenu(false); });
shareButton?.addEventListener("click", () => { shareProject(); toggleBurgerMenu(false); });
addPageButton?.addEventListener("click", addPage);
regenerateDialogueButton?.addEventListener("click", regenerateDialogue);
generateCaptionButton?.addEventListener("click", generateCaption);
creditInfoButton?.addEventListener("click", () =>
  showToast(`Доступно ${credits} кредитов. Генерация страницы стоит ${PRICE_PER_PAGE}.`)
);
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
    const labels = {
      profile: "Профиль открыт.",
      settings: "Настройки открыты.",
      logout: "Вы вышли из демо-профиля.",
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
checkHealth();
