(function () {
  const paymentPlaceholder = document.querySelector("[data-payment-placeholder]");
  const paymentMessage = document.querySelector("[data-payment-message]");
  const paymentClose = document.querySelector("[data-payment-close]");
  const buttons = Array.from(document.querySelectorAll("[data-plan][data-package-code]"));

  if (buttons.length === 0) return;

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
    return window.location.origin;
  }

  const API_BASE_URL = resolveApiBaseUrl();

  function showNotice(strongText, message) {
    if (!paymentPlaceholder || !paymentMessage) return;
    const strong = paymentPlaceholder.querySelector("strong");
    if (strong) strong.textContent = strongText;
    paymentMessage.textContent = message;
    paymentPlaceholder.hidden = false;
  }

  async function apiFetch(path, options) {
    const init = Object.assign({ credentials: "include" }, options || {});
    init.headers = Object.assign({}, init.headers || {});
    if (init.body && !init.headers["Content-Type"]) {
      init.headers["Content-Type"] = "application/json";
    }
    const response = await fetch(API_BASE_URL + path, init);
    let data = null;
    try { data = await response.json(); } catch (_) { data = null; }
    if (!response.ok) {
      const err = (data && data.error) || {};
      const error = new Error(err.message || (data && data.message) || "Не удалось связаться с сервером.");
      error.status = response.status;
      error.code = err.code || (data && data.code) || "API_ERROR";
      throw error;
    }
    return data;
  }

  let packagesPromise = null;
  function loadPackages() {
    if (!packagesPromise) {
      packagesPromise = apiFetch("/api/v1/coin-packages").catch((err) => {
        packagesPromise = null;
        throw err;
      });
    }
    return packagesPromise;
  }

  async function startCheckout(button) {
    const planLabel = button.dataset.plan || "пакет";
    const code = button.dataset.packageCode;
    if (!code) return;

    if (button.dataset.busy === "1") return;
    button.dataset.busy = "1";
    const originalText = button.textContent;
    button.textContent = "Перенаправляем...";
    button.disabled = true;

    try {
      const packages = await loadPackages();
      const match = Array.isArray(packages)
        ? packages.find((pkg) => pkg && pkg.code === code)
        : null;
      if (!match) {
        throw Object.assign(new Error("Тариф недоступен."), {
          code: "COIN_PACKAGE_NOT_FOUND",
        });
      }

      const checkout = await apiFetch("/api/v1/payments", {
        method: "POST",
        body: JSON.stringify({ coin_package_id: match.id }),
      });

      if (!checkout || !checkout.confirmation_url) {
        throw new Error("Платежный шлюз не вернул ссылку для оплаты.");
      }

      window.location.assign(checkout.confirmation_url);
    } catch (error) {
      button.dataset.busy = "0";
      button.disabled = false;
      button.textContent = originalText;

      if (error.status === 401) {
        showNotice(
          "Войдите, чтобы оплатить",
          `Чтобы купить тариф «${planLabel}», нужно сначала войти в comicly.ai.`,
        );
        return;
      }
      if (error.code === "PAYMENTS_UNAVAILABLE") {
        showNotice(
          "Оплата временно недоступна",
          "Мы уже занимаемся восстановлением. Попробуйте позже.",
        );
        return;
      }
      showNotice(
        "Не удалось начать оплату",
        error.message || "Попробуйте еще раз через минуту.",
      );
    }
  }

  buttons.forEach((button) => {
    button.addEventListener("click", () => startCheckout(button));
  });

  paymentClose?.addEventListener("click", () => {
    if (paymentPlaceholder) paymentPlaceholder.hidden = true;
  });

  async function pollPaymentStatus(paymentId) {
    showNotice(
      "Проверяем оплату...",
      "Уточняем у платежного шлюза, пришел ли платеж.",
    );
    const attempts = 6;
    const delayMs = 2500;
    for (let i = 0; i < attempts; i += 1) {
      try {
        const result = await apiFetch(`/api/v1/payments/${paymentId}/refresh`, {
          method: "POST",
        });
        if (result && result.credited) {
          showNotice(
            "Оплата получена!",
            `Начислено ${result.coin_amount} монет. Можно возвращаться к созданию комикса.`,
          );
          return;
        }
        if (result && result.status === "canceled") {
          showNotice(
            "Платеж отменен",
            "Списания не было. Если это ошибка, попробуйте оплатить еще раз.",
          );
          return;
        }
      } catch (error) {
        if (error.status === 401) {
          showNotice(
            "Войдите, чтобы увидеть статус",
            "Авторизуйтесь, чтобы мы могли проверить статус вашей оплаты.",
          );
          return;
        }
        if (error.status === 404) {
          showNotice(
            "Платеж не найден",
            "Похоже, ссылка устарела. Если списание было, монеты придут после подтверждения.",
          );
          return;
        }
      }
      if (i < attempts - 1) {
        await new Promise((resolve) => setTimeout(resolve, delayMs));
      }
    }
    showNotice(
      "Ждем подтверждения от банка",
      "Это может занять до нескольких минут. Монеты появятся на балансе автоматически.",
    );
  }

  const params = new URLSearchParams(window.location.search);
  if (params.get("payment") === "return") {
    const paymentId = params.get("payment_id");
    if (paymentId) {
      pollPaymentStatus(paymentId);
    } else {
      showNotice(
        "Спасибо! Платеж в обработке",
        "Если оплата прошла успешно, монеты появятся на балансе в течение нескольких минут.",
      );
    }
  }
})();
