(function () {
  const root = document.querySelector("[data-header-auth]");
  if (!root) return;

  const cta = root.querySelector("[data-header-cta]");
  const account = root.querySelector("[data-header-account]");
  const creditBalance = root.querySelector("[data-credit-balance]");
  const profileToggle = root.querySelector("[data-profile-toggle]");
  const profileMenu = root.querySelector("[data-profile-menu]");
  const profileName = root.querySelector("[data-profile-name]");
  const profileEmail = root.querySelector("[data-profile-email]");
  const profileAvatar = root.querySelector("[data-profile-avatar]");
  const logoutButton = root.querySelector("[data-profile-logout]");

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
      const error = new Error(err.message || (data && data.message) || "API_ERROR");
      error.status = response.status;
      throw error;
    }
    return data;
  }

  function showLoggedOut() {
    if (cta) cta.hidden = false;
    if (account) account.hidden = true;
  }

  function showLoggedIn(data) {
    const acc = data && data.account ? data.account : null;
    const balance = Number((data && data.wallet && data.wallet.balance) || 0);
    const displayName = (acc && (acc.display_name || acc.email)) || "Профиль";
    const email = (acc && acc.email) || "Автор";
    const initial = displayName.trim().charAt(0).toUpperCase() || "?";

    if (creditBalance) creditBalance.textContent = `${balance} монет`;
    if (profileName) profileName.textContent = displayName;
    if (profileEmail) profileEmail.textContent = email;
    if (profileAvatar) profileAvatar.textContent = initial;

    if (cta) cta.hidden = true;
    if (account) account.hidden = false;
  }

  function toggleProfileMenu(force) {
    if (!profileMenu || !profileToggle) return;
    const shouldOpen = typeof force === "boolean" ? force : profileMenu.hidden;
    profileMenu.hidden = !shouldOpen;
    profileToggle.setAttribute("aria-expanded", String(shouldOpen));
  }

  profileToggle?.addEventListener("click", (event) => {
    event.stopPropagation();
    toggleProfileMenu();
  });

  document.addEventListener("click", (event) => {
    if (!profileMenu || profileMenu.hidden) return;
    if (profileMenu.contains(event.target) || profileToggle?.contains(event.target)) return;
    toggleProfileMenu(false);
  });

  logoutButton?.addEventListener("click", async () => {
    toggleProfileMenu(false);
    try {
      await apiFetch("/api/v1/me/logout", { method: "POST" });
    } catch (_) {
      // proceed regardless — local UI returns to logged-out state
    }
    showLoggedOut();
  });

  (async function bootstrap() {
    try {
      const data = await apiFetch("/api/v1/me");
      showLoggedIn(data);
    } catch (_) {
      showLoggedOut();
    }
  })();
})();
