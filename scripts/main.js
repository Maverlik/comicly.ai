const previewCards = Array.from(document.querySelectorAll("[data-carousel-card]"));

const prevButton = document.querySelector("[data-carousel-prev]");
const nextButton = document.querySelector("[data-carousel-next]");

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

prevButton?.addEventListener("click", () => moveCarousel(activePage - 1));
nextButton?.addEventListener("click", () => moveCarousel(activePage + 1));

setCarousel(0);
