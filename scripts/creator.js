const projectTitleInput = document.querySelector("#projectTitle");
const storyInput = document.querySelector("#storyInput");
const storyCounter = document.querySelector("[data-story-counter]");
const clearStoryButton = document.querySelector("[data-clear-story]");
const enhanceStoryButton = document.querySelector("[data-enhance-story]");
const generatePageButton = document.querySelector("[data-generate-page]");
const regenerateSceneButton = document.querySelector("[data-regenerate-scene]");
const styleSelect = document.querySelector("#styleSelect");
const styleSwatches = Array.from(document.querySelectorAll("[data-style]"));
const toneButtons = Array.from(document.querySelectorAll("[data-tone]"));
const sceneList = document.querySelector("[data-scene-list]");
const pageStrip = document.querySelector(".page-strip");
let sceneItems = Array.from(document.querySelectorAll("[data-scene]"));
let pageThumbs = Array.from(document.querySelectorAll("[data-page-thumb]"));
const pageStatus = document.querySelector("[data-page-status]");
const comicCanvas = document.querySelector("[data-comic-canvas]");
const comicOutput = document.querySelector("[data-comic-output]");
const comicLoading = document.querySelector("[data-loading]");
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
const panelToggles = Array.from(document.querySelectorAll("[data-panel-toggle]"));
const tabButtons = Array.from(document.querySelectorAll("[data-tab]"));
const rightPanel = document.querySelector(".right-panel");

let pages = [
  "assets/comic-preview-fantasy.png",
  "assets/comic-preview-japan.png",
  "assets/comic-preview-action.png",
  "assets/comicly-reference.png",
];

let activePage = 2;
let activeTone = "emotional";
let activeScene = 1;
let credits = 240;
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
    dialogue: dialogueInput?.value || "",
    caption: captionInput?.value || "",
    pages: [...pages],
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
  if (dialogueInput) dialogueInput.value = snapshot.dialogue;
  if (captionInput) captionInput.value = snapshot.caption;
  pages = [...snapshot.pages];
  credits = snapshot.credits;

  renderPageStrip();
  updateStoryCounter();
  updateCreditBalance();
  setStyle(snapshot.style, false);
  setTone(snapshot.tone, false);
  setScene(snapshot.activeScene, false);
  setPage(snapshot.activePage, false);

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

function setLoading(isLoading) {
  if (comicLoading) comicLoading.hidden = !isLoading;
  if (generatePageButton) generatePageButton.disabled = isLoading;
  if (regenerateSceneButton) regenerateSceneButton.disabled = isLoading;
}

function createPlaceholderPage(pageNumber) {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="900" height="900" viewBox="0 0 900 900">
      <rect width="900" height="900" fill="#060917"/>
      <rect x="34" y="34" width="832" height="832" rx="28" fill="#0b1025" stroke="#7e55ff" stroke-width="4"/>
      <path d="M450 186l44 112 112 42-112 43-44 112-44-112-112-43 112-42 44-112z" fill="#a77bff"/>
      <text x="450" y="590" text-anchor="middle" fill="#f5f6ff" font-family="Arial, sans-serif" font-size="42" font-weight="700">Страница ${pageNumber}</text>
      <text x="450" y="648" text-anchor="middle" fill="#aeb3c7" font-family="Arial, sans-serif" font-size="28">Нажмите «Сгенерировать страницу»</text>
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

function setScene(sceneIndex, save = true) {
  activeScene = sceneIndex;

  sceneItems.forEach((item) => {
    item.classList.toggle("is-selected", Number(item.dataset.scene) === sceneIndex);
  });

  if (dialogueInput) {
    const sceneTexts = [
      "В МИРЕ, ГДЕ ЗВЕЗДЫ ПОГАСЛИ...",
      "ОДИНОКИЙ СТРАННИК НАХОДИТ ДРЕВНЮЮ СИЛУ...",
      "ТЕНИ ПРОСЫПАЮТСЯ В ГЛУБИНЕ ГОРОДА...",
      "ГЕРОЙ ВЫБИРАЕТ ЗАЖЕЧЬ СВЕТ СНОВА...",
    ];
    dialogueInput.value = sceneTexts[sceneIndex] || sceneTexts[sceneTexts.length - 1];
  }

  if (save) pushHistory();
}

function enhanceStory() {
  if (!storyInput) return;

  const current = storyInput.value.trim();
  const suffix =
    " Добавьте кинематографичные сцены, сильный визуальный конфликт, повторяющийся символ и финальный кадр с эмоциональным выбором героя.";

  storyInput.value = current.includes("кинематографичные сцены") ? current : `${current}${suffix}`;
  updateStoryCounter();
  pushHistory();
  showToast("История дополнена направлением для генерации.");
}

function buildScenePrompt() {
  return {
    story: storyInput?.value.trim() || "",
    style: styleSelect?.value || "Аниме",
    tone: activeTone,
    page: activePage + 1,
    selectedScene: activeScene + 1,
    dialogue: dialogueInput?.value.trim() || "",
    caption: captionInput?.value.trim() || "",
    layout:
      "single full comic page, cinematic panel layout, readable speech bubbles, high contrast, polished finished comic art",
  };
}

async function generateComicPage() {
  const payload = buildScenePrompt();

  if (!payload.story) {
    showToast("Добавьте описание истории перед генерацией.");
    return;
  }

  setLoading(true);

  try {
    const response = await fetch("/api/generate-comic-page", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Не удалось сгенерировать страницу.");
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

function regenerateDialogue() {
  if (!dialogueInput) return;

  const variants = [
    "Я СЛЫШУ СВЕТ ПОД КАМНЕМ...",
    "ЕСЛИ ЗВЕЗДЫ МОЛЧАТ, МЫ ЗАЖЖЕМ ИХ САМИ.",
    "ЭТА СИЛА ЖДАЛА НЕ ГЕРОЯ. ОНА ЖДАЛА ВЫБОР.",
  ];
  dialogueInput.value = variants[Math.floor(Math.random() * variants.length)];
  pushHistory();
  showToast("Диалог обновлен.");
}

function generateCaption() {
  if (!captionInput) return;
  captionInput.value = "Камни города начинают светиться, когда герой поднимает древний знак.";
  pushHistory();
  showToast("Описание сцены добавлено.");
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

  if (navigator.share) {
    await navigator.share(shareData);
    return;
  }

  await navigator.clipboard.writeText(shareData.url);
  showToast("Ссылка на проект скопирована.");
}

function addPage() {
  pages.push(createPlaceholderPage(pages.length + 1));
  renderPageStrip();
  setPage(pages.length - 1);
  pushHistory();
  showToast("Новая страница добавлена.");
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
}

function setTab(tab) {
  tabButtons.forEach((button) => {
    const isActive = button.dataset.tab === tab;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-selected", String(isActive));
  });

  rightPanel?.classList.toggle("is-dialogue-tab", tab === "dialogue");
}

function moveScene(item) {
  if (!sceneList || !item) return;

  const previous = item.previousElementSibling;
  if (previous) {
    sceneList.insertBefore(item, previous);
    showToast("Сцена перемещена выше.");
  } else {
    sceneList.appendChild(item);
    showToast("Сцена перемещена вниз списка.");
  }

  sceneItems = Array.from(document.querySelectorAll("[data-scene]"));
}

function openSceneMenu(item) {
  if (!item) return;
  const title = item.querySelector("h2")?.textContent || "Сцена";
  setScene(Number(item.dataset.scene));
  captionInput?.focus();
  showToast(`${title}: описание готово к редактированию.`);
}

let storyInputTimer;

storyInput?.addEventListener("input", () => {
  updateStoryCounter();
  window.clearTimeout(storyInputTimer);
  storyInputTimer = window.setTimeout(pushHistory, 700);
});

projectTitleInput?.addEventListener("change", pushHistory);
dialogueInput?.addEventListener("change", pushHistory);
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
downloadButton?.addEventListener("click", downloadCurrentPage);
shareButton?.addEventListener("click", () => shareProject().catch(() => showToast("Не удалось поделиться проектом.")));
addPageButton?.addEventListener("click", addPage);
regenerateDialogueButton?.addEventListener("click", regenerateDialogue);
generateCaptionButton?.addEventListener("click", generateCaption);
creditInfoButton?.addEventListener("click", () => showToast(`Доступно ${credits} кредитов. Генерация страницы стоит 20.`));
addCreditsButton?.addEventListener("click", addCredits);
notificationsButton?.addEventListener("click", () => showToast("Новых уведомлений нет."));
renameButton?.addEventListener("click", () => {
  projectTitleInput?.focus();
  projectTitleInput?.select();
});
undoButton?.addEventListener("click", undo);
redoButton?.addEventListener("click", redo);
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

panelToggles.forEach((button) => {
  button.addEventListener("click", () => {
    const card = button.closest(".panel-card");
    card?.classList.toggle("is-collapsed");
  });
});

tabButtons.forEach((button) => {
  button.addEventListener("click", () => setTab(button.dataset.tab));
});

styleSwatches.forEach((swatch) => {
  swatch.addEventListener("click", () => setStyle(swatch.dataset.style));
});

styleSelect?.addEventListener("change", () => setStyle(styleSelect.value));

toneButtons.forEach((button) => {
  button.addEventListener("click", () => setTone(button.dataset.tone));
});

function bindSceneButtons() {
  sceneItems.forEach((item) => {
    item.addEventListener("click", () => setScene(Number(item.dataset.scene)));

    item.querySelector("[data-move-scene]")?.addEventListener("click", (event) => {
      event.stopPropagation();
      moveScene(item);
    });

    item.querySelector("[data-scene-menu]")?.addEventListener("click", (event) => {
      event.stopPropagation();
      openSceneMenu(item);
    });
  });
}

document.addEventListener("click", (event) => {
  if (!profileMenu || profileMenu.hidden) return;
  if (profileMenu.contains(event.target) || profileToggle?.contains(event.target)) return;
  toggleProfileMenu(false);
});

renderPageStrip();
bindSceneButtons();
updateStoryCounter();
updateCreditBalance();
setPage(activePage, false);
setStyle(styleSelect?.value || "Аниме", false);
setTone(activeTone, false);
setScene(activeScene, false);
setZoom(zoomSelect?.value || "100%");
setTab("scenes");
pushHistory();
