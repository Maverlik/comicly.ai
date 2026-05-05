const previewCards = Array.from(document.querySelectorAll("[data-carousel-card]"));

const prevButton = document.querySelector("[data-carousel-prev]");
const nextButton = document.querySelector("[data-carousel-next]");
const feedbackForm = document.querySelector("[data-feedback-form]");
const feedbackStatus = document.querySelector("[data-feedback-status]");
const feedbackImageTypes = new Set(["image/jpeg", "image/png", "image/webp", "image/gif"]);
const feedbackMaxFiles = 3;
const feedbackMaxFileBytes = 5 * 1024 * 1024;

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

feedbackForm?.addEventListener("submit", (event) => {
  event.preventDefault();

  const formData = new FormData(feedbackForm);
  const message = String(formData.get("message") || "").trim();
  const images = formData.getAll("images").filter((file) => file && file.size > 0);
  const submitButton = feedbackForm.querySelector("button[type='submit']");

  if (!message) {
    feedbackForm.reportValidity();
    return;
  }
  if (images.length > feedbackMaxFiles) {
    showFeedbackStatus("error", "Можно прикрепить максимум 3 картинки.");
    return;
  }
  if (images.some((file) => !feedbackImageTypes.has(file.type))) {
    showFeedbackStatus("error", "Поддерживаются только PNG, JPG, WebP и GIF.");
    return;
  }
  if (images.some((file) => file.size > feedbackMaxFileBytes)) {
    showFeedbackStatus("error", "Каждая картинка должна быть до 5 МБ.");
    return;
  }

  showFeedbackStatus("pending", "Отправляем...");
  if (submitButton) submitButton.disabled = true;

  fetch("/api/v1/feedback", {
    method: "POST",
    credentials: "include",
    body: formData,
  })
    .then(async (response) => {
      if (!response.ok) {
        let data = null;
        try { data = await response.json(); } catch (_) { data = null; }
        const code = data && data.error && data.error.code;
        throw new Error(code || "FEEDBACK_FAILED");
      }
      feedbackForm.reset();
      showFeedbackStatus("success", "Спасибо. Сообщение отправлено.");
    })
    .catch((error) => {
      showFeedbackStatus("error", error.message === "FEEDBACK_UNAVAILABLE"
        ? "Отправка пока не настроена. Нужны SMTP-данные для сервера."
        : "Не удалось отправить сообщение. Попробуйте позже.");
    })
    .finally(() => {
      if (submitButton) submitButton.disabled = false;
    });
});

function showFeedbackStatus(state, message) {
  if (!feedbackStatus) return;
  feedbackStatus.hidden = false;
  feedbackStatus.dataset.state = state;
  feedbackStatus.textContent = message;
}
