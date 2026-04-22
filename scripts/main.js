const previewCards = Array.from(document.querySelectorAll("[data-carousel-card]"));

const toneDirections = {
  "Эпичный sci-fi":
    "Кинематографичная sci-fi страница на 5 панелей: общий план города, маршрут героя, вспышка действия, технологическая деталь и финальный крупный план.",
  "Темное фэнтези":
    "Мрачная фэнтези-страница на 5 панелей: силуэт героя, древний знак, столкновение с угрозой, пауза перед выбором и драматичный финал.",
  "Детективный нуар":
    "Нуарная страница на 6 панелей: дождливая улица, улика, напряженный диалог, тень преследователя, разворот и жесткий финальный кадр.",
  "Теплое приключение":
    "Приключенческая страница на 5 панелей: яркое место, знакомство с героем, маленькая опасность, смелое решение и открытый финал.",
};

const prevButton = document.querySelector("[data-carousel-prev]");
const nextButton = document.querySelector("[data-carousel-next]");
const generateButton = document.querySelector("[data-generate]");
const toneSelect = document.querySelector("#toneSelect");
const storyPrompt = document.querySelector("#storyPrompt");
const output = document.querySelector("[data-output]");

let activePage = 0;
let isSwitching = false;

function normalizeIndex(index) {
  return (index + previewCards.length) % previewCards.length;
}

function slotForPage(pageIndex) {
  if (pageIndex === activePage) return "main";
  if (pageIndex === normalizeIndex(activePage + 1)) return "right";
  return "left";
}

function setCarousel(index) {
  activePage = normalizeIndex(index);

  previewCards.forEach((card) => {
    const pageIndex = Number(card.dataset.page);
    card.dataset.slot = slotForPage(pageIndex);
  });
}

function moveCarousel(index) {
  if (isSwitching || previewCards.length === 0) return;

  isSwitching = true;
  if (prevButton) prevButton.disabled = true;
  if (nextButton) nextButton.disabled = true;

  setCarousel(index);

  window.setTimeout(() => {
    isSwitching = false;
    if (prevButton) prevButton.disabled = false;
    if (nextButton) nextButton.disabled = false;
  }, 640);
}

function updateDirection() {
  if (!toneSelect || !storyPrompt || !output) return;

  const prompt = storyPrompt.value.trim();
  const baseDirection = toneDirections[toneSelect.value] || toneDirections["Эпичный sci-fi"];
  const storyHook = prompt
    ? ` Основа сцены: ${prompt.slice(0, 150)}${prompt.length > 150 ? "..." : ""}`
    : "";

  output.value = `${baseDirection}${storyHook}`;
}

prevButton?.addEventListener("click", () => moveCarousel(activePage - 1));
nextButton?.addEventListener("click", () => moveCarousel(activePage + 1));
generateButton?.addEventListener("click", updateDirection);
toneSelect?.addEventListener("change", updateDirection);

setCarousel(0);
