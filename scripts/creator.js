const projectTitleInput = document.querySelector("#projectTitle");
const storyInput = document.querySelector("#storyInput");
const storyCounter = document.querySelector("[data-story-counter]");
const clearStoryButton = document.querySelector("[data-clear-story]");
const enhanceStoryButton = document.querySelector("[data-enhance-story]");
const generatePageButton = document.querySelector("[data-generate-page]");
const regenerateSceneButton = document.querySelector("[data-regenerate-scene]");
const suggestScenesButton = document.querySelector("[data-suggest-scenes]");
const styleSelect = document.querySelector("#styleSelect");
const styleSwatches = Array.from(document.querySelectorAll("[data-style]"));
const toneButtons = Array.from(document.querySelectorAll("[data-tone]"));
const sceneList = document.querySelector("[data-scene-list]");
const sceneCounter = document.querySelector("[data-scene-counter]");
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
const tabButtons = Array.from(document.querySelectorAll("[data-tab]"));
const tabContents = Array.from(document.querySelectorAll("[data-tab-content]"));
const sideTabButtons = Array.from(document.querySelectorAll("[data-side-tab]"));
const sidePanes = Array.from(document.querySelectorAll("[data-side-pane]"));
const burgerToggle = document.querySelector("[data-burger-toggle]");
const burgerMenu = document.querySelector("[data-burger-menu]");
const configBanner = document.querySelector("[data-config-banner]");
const selectedSceneTitle = document.querySelector("[data-selected-scene-title]");

const PLACEHOLDER_IMAGES = [
  "assets/comic-preview-fantasy.png",
  "assets/comic-preview-japan.png",
  "assets/comic-preview-action.png",
  "assets/comicly-reference.png",
];

const DEFAULT_SCENES = [
  { title: "Сцена 1", description: "Широкий план разрушенного города под мертвым небом.", dialogue: "В МИРЕ, ГДЕ ЗВЕЗДЫ ПОГАСЛИ...", caption: "" },
  { title: "Сцена 2", description: "Странник находит древнюю силу в руинах.", dialogue: "ОДИНОКИЙ СТРАННИК НАХОДИТ ДРЕВНЮЮ СИЛУ...", caption: "" },
  { title: "Сцена 3", description: "Тени выходят из города и преследуют героя.", dialogue: "ТЕНИ ПРОСЫПАЮТСЯ В ГЛУБИНЕ ГОРОДА...", caption: "" },
];

let pages = [createPlaceholderDataUrl(1), createPlaceholderDataUrl(2)];
let pageImages = ["assets/comic-preview-fantasy.png", "assets/comic-preview-japan.png"];
let scenes = DEFAULT_SCENES.map((scene) => ({ ...scene }));
let activePage = 0;
let activeTone = "emotional";
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

function getSnapshot() {
  return {
    title: projectTitleInput?.value || "",
    story: storyInput?.value || "",
    style: styleSelect?.value || "Аниме",
    tone: activeTone,
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
  pages = [...snapshot.pages];
  scenes = snapshot.scenes.map((scene) => ({ ...scene }));
  credits = snapshot.credits;

  renderPageStrip();
  renderScenes();
  updateStoryCounter();
  updateCreditBalance();
  setStyle(snapshot.style, false);
  setTone(snapshot.tone, false);
  setScene(Math.min(snapshot.activeScene, scenes.length - 1), false);
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
      <rect x="34" y="34" width="832" height="1132" rx="28" fill="#0b1025" stroke="#7e55ff" stroke-width="4"/>
      <path d="M450 360l44 112 112 42-112 43-44 112-44-112-112-43 112-42 44-112z" fill="#a77bff"/>
      <text x="450" y="760" text-anchor="middle" fill="#f5f6ff" font-family="Arial, sans-serif" font-size="48" font-weight="700">Страница ${pageNumber}</text>
      <text x="450" y="820" text-anchor="middle" fill="#aeb3c7" font-family="Arial, sans-serif" font-size="28">Нажмите «Сгенерировать страницу»</text>
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

function setStyle(style, save = true) {
  if (styleSelect) styleSelect.value = style;

  styleSwatches.forEach((swatch) => {
    swatch.classList.toggle("is-selected", swatch.dataset.style === style);
  });

  if (save) pushHistory();
}

function setTone(tone, save = true) {
  activeTone = tone;

  toneButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.tone === tone);
  });

  if (save) pushHistory();
}

function renderScenes() {
  if (!sceneList) return;
  sceneList.innerHTML = "";

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
        <h2>${scene.title}</h2>
        <p>${scene.description}</p>
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

function refreshSceneSelection() {
  const items = sceneList ? Array.from(sceneList.querySelectorAll("[data-scene]")) : [];
  items.forEach((item) => {
    item.classList.toggle("is-selected", Number(item.dataset.scene) === activeScene);
  });
  if (sceneCounter) sceneCounter.textContent = `${activeScene + 1} из ${scenes.length}`;
  if (selectedSceneTitle) {
    selectedSceneTitle.textContent = scenes[activeScene]?.title || "Выбранная сцена";
  }
}

function setScene(sceneIndex, save = true) {
  if (sceneIndex < 0 || sceneIndex >= scenes.length) return;
  activeScene = sceneIndex;
  const scene = scenes[sceneIndex];

  refreshSceneSelection();
  if (dialogueInput) dialogueInput.value = scene.dialogue || "";
  if (captionInput) captionInput.value = scene.caption || "";

  if (save) pushHistory();
}

function syncSceneFromInputs() {
  const scene = scenes[activeScene];
  if (!scene) return;
  if (dialogueInput) scene.dialogue = dialogueInput.value;
  if (captionInput) scene.caption = captionInput.value;
}

async function callAiText(task) {
  const scene = scenes[activeScene] || {};
  const response = await fetch("/api/ai-text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      task,
      story: storyInput?.value.trim() || "",
      style: styleSelect?.value || "Аниме",
      tone: activeTone,
      sceneTitle: scene.title,
      sceneDescription: scene.description,
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
      dialogue: scenes[index]?.dialogue || "",
      caption: scenes[index]?.caption || "",
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

function toggleBusy(button, isBusy) {
  if (!button) return;
  button.disabled = isBusy;
  button.classList.toggle("is-busy", isBusy);
}

function buildScenePayload() {
  return {
    story: storyInput?.value.trim() || "",
    style: styleSelect?.value || "Аниме",
    tone: activeTone,
    page: activePage + 1,
    selectedScene: activeScene + 1,
    scenes: scenes.map((scene) => `${scene.title}: ${scene.description}`),
    dialogue: dialogueInput?.value.trim() || "",
    caption: captionInput?.value.trim() || "",
    layout: "single full comic page, cinematic panel layout, readable speech bubbles, high contrast",
  };
}

async function generateComicPage() {
  const payload = buildScenePayload();

  if (!payload.story) {
    showToast("Добавьте описание истории перед генерацией.");
    return;
  }

  setLoading(true, "Генерируем страницу...");

  try {
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

    pages[activePage] = data.imageUrl;
    if (comicOutput) comicOutput.src = data.imageUrl;

    const activeThumb = pageThumbs.find((thumb) => Number(thumb.dataset.pageThumb) === activePage);
    const thumbImage = activeThumb?.querySelector("img");
    if (thumbImage) thumbImage.src = data.imageUrl;

    if (emptyState) emptyState.hidden = true;
    credits = Math.max(0, credits - 20);
    updateCreditBalance();
    pushHistory();
    showToast("Страница сгенерирована.");
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
  comicCanvas.style.width = `min(100%, ${Math.round(790 * (numeric / 100))}px)`;
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

function setTab(tab) {
  tabButtons.forEach((button) => {
    const isActive = button.dataset.tab === tab;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-selected", String(isActive));
  });
  tabContents.forEach((content) => {
    const isActive = content.dataset.tabContent === tab;
    content.classList.toggle("is-active", isActive);
    content.hidden = !isActive;
  });
}

function setSideTab(tab) {
  sideTabButtons.forEach((button) => {
    const isActive = button.dataset.sideTab === tab;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-selected", String(isActive));
  });
  sidePanes.forEach((pane) => {
    const isActive = pane.dataset.sidePane === tab;
    pane.classList.toggle("is-active", isActive);
    pane.hidden = !isActive;
  });
}

function toggleBurgerMenu(force) {
  if (!burgerMenu || !burgerToggle) return;
  const shouldOpen = typeof force === "boolean" ? force : burgerMenu.hidden;
  burgerMenu.hidden = !shouldOpen;
  burgerToggle.setAttribute("aria-expanded", String(shouldOpen));
  if (shouldOpen) toggleProfileMenu(false);
}

function moveScene(index) {
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
  captionInput?.focus();
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
downloadButton?.addEventListener("click", () => { downloadCurrentPage(); toggleBurgerMenu(false); });
shareButton?.addEventListener("click", () => { shareProject(); toggleBurgerMenu(false); });
addPageButton?.addEventListener("click", addPage);
regenerateDialogueButton?.addEventListener("click", regenerateDialogue);
generateCaptionButton?.addEventListener("click", generateCaption);
creditInfoButton?.addEventListener("click", () =>
  showToast(`Доступно ${credits} кредитов. Генерация страницы стоит 20.`)
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

tabButtons.forEach((button) => {
  button.addEventListener("click", () => setTab(button.dataset.tab));
});

sideTabButtons.forEach((button) => {
  button.addEventListener("click", () => setSideTab(button.dataset.sideTab));
});

burgerToggle?.addEventListener("click", () => toggleBurgerMenu());

styleSwatches.forEach((swatch) => {
  swatch.addEventListener("click", () => setStyle(swatch.dataset.style));
});

styleSelect?.addEventListener("change", () => setStyle(styleSelect.value));

toneButtons.forEach((button) => {
  button.addEventListener("click", () => setTone(button.dataset.tone));
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
});

renderPageStrip();
renderScenes();
updateStoryCounter();
updateCreditBalance();
setPage(activePage, false);
setStyle(styleSelect?.value || "Аниме", false);
setTone(activeTone, false);
setScene(activeScene, false);
setZoom(zoomSelect?.value || "100%");
setTab("scenes");
setSideTab("story");
pushHistory();
checkHealth();
