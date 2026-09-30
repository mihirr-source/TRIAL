/* =====================================================================
   Authentication Client Module (auth.js)
   Handles Login, Registration, Input Validation, UI Feedback & Auth State
   ===================================================================== */
"use strict";

(function () {
  // Global Toast Function
  function showToast(message, type = "info", duration = 3500) {
    let container = document.getElementById("toast-container");
    if (!container) {
      container = document.createElement("div");
      container.id = "toast-container";
      document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `toast ${type} animate-toast-in`;
    const icon = type === "success" ? "✓" : type === "error" ? "✕" : "ℹ";
    toast.innerHTML = `<span style="font-weight:700">${icon}</span> <span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.classList.remove("animate-toast-in");
      toast.classList.add("animate-toast-out");
      setTimeout(() => toast.remove(), 260);
    }, duration);
  }
  window.showToast = showToast;

  // Logout Handler
  async function doLogout() {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
      showToast("Logged out successfully.", "info");
      setTimeout(() => location.replace("/login"), 300);
    } catch {
      location.replace("/login");
    }
  }

  // Header User Badge & Logout Wireup
  async function checkUserState() {
    try {
      const res = await fetch("/api/auth/me");
      if (res.ok) {
        const data = await res.json();
        if (data.authenticated && data.user) {
          renderNavbarUser(data.user);
          // If on login page and already authenticated, redirect to home
          if (location.pathname === "/login") {
            location.replace("/");
          }
          return;
        }
      }
      renderNavbarUser(null);
    } catch {
      renderNavbarUser(null);
    }
  }

  function renderNavbarUser(user) {
    const actionsContainer = document.querySelector(".header-actions");
    const mobileAuthSection = document.getElementById("mobile-auth-section");

    // Remove existing badges if any
    const existingDesktop = document.getElementById("user-profile-badge");
    if (existingDesktop) existingDesktop.remove();
    const existingSignIn = document.getElementById("nav-signin-link");
    if (existingSignIn) existingSignIn.remove();

    if (user) {
      const initial = (user.name || user.email || "U").trim().charAt(0).toUpperCase();
      const displayName = user.name || user.email.split("@")[0];

      // 1. Desktop Header User Badge & Distinct Logout Button
      if (actionsContainer) {
        const userWrap = document.createElement("div");
        userWrap.id = "user-profile-badge";
        userWrap.className = "user-nav-wrapper";
        userWrap.innerHTML = `
          <div class="user-badge" title="${escapeHtml(user.name || displayName)} (${escapeHtml(user.email)})">
            <span class="user-avatar">${escapeHtml(initial)}</span>
            <span class="user-name-text">${escapeHtml(displayName)}</span>
          </div>
          <button id="btn-logout-nav" class="btn-logout" type="button" title="Log Out" aria-label="Log Out">
            <span class="logout-icon" aria-hidden="true">⏻</span>
            <span class="logout-label">LOGOUT</span>
          </button>
        `;
        // Append at rightmost position in header actions
        actionsContainer.appendChild(userWrap);

        const logoutBtn = document.getElementById("btn-logout-nav");
        if (logoutBtn) logoutBtn.addEventListener("click", doLogout);
      }

      // 2. Mobile Drawer User Badge & Logout
      if (mobileAuthSection) {
        mobileAuthSection.innerHTML = `
          <div class="mobile-user-card">
            <div style="display:flex; align-items:center; gap:0.75rem;">
              <span class="user-avatar" style="width:34px; height:34px; font-size:0.95rem;">${escapeHtml(initial)}</span>
              <div style="overflow:hidden;">
                <div style="font-weight:700; color:var(--text-main); white-space:nowrap; text-overflow:ellipsis; overflow:hidden;">${escapeHtml(displayName)}</div>
                <div style="font-size:0.75rem; color:var(--text-muted); white-space:nowrap; text-overflow:ellipsis; overflow:hidden;">${escapeHtml(user.email)}</div>
              </div>
            </div>
            <button id="btn-logout-mobile" class="btn-logout-mobile" type="button" aria-label="Log Out">
              ⏻ Logout
            </button>
          </div>
        `;
        const mobileLogoutBtn = document.getElementById("btn-logout-mobile");
        if (mobileLogoutBtn) mobileLogoutBtn.addEventListener("click", doLogout);
      }
    } else {
      // Unauthenticated state -> Show Sign In button at rightmost corner
      if (actionsContainer && location.pathname !== "/login") {
        const signinLink = document.createElement("a");
        signinLink.id = "nav-signin-link";
        signinLink.href = "/login";
        signinLink.className = "btn-nav-signin";
        signinLink.textContent = "Sign In";
        actionsContainer.appendChild(signinLink);
      }

      if (mobileAuthSection && location.pathname !== "/login") {
        mobileAuthSection.innerHTML = `
          <a href="/login" class="btn-nav-signin-mobile">Sign In / Register</a>
        `;
      }
    }
  }

  // Login / Register Page Logic
  function initAuthPage() {
    const card = document.getElementById("auth-card");
    const form = document.getElementById("auth-form");
    if (!form || !card) return;

    const tabLogin = document.getElementById("tab-login");
    const tabRegister = document.getElementById("tab-register");
    const nameGroup = document.getElementById("name-group");
    const submitBtn = document.getElementById("submit-btn");
    const submitText = document.getElementById("submit-text");
    const submitSpinner = document.getElementById("submit-spinner");
    const switchLink = document.getElementById("switch-auth-link");
    const pwdToggle = document.getElementById("toggle-password");
    const pwdInput = document.getElementById("password");
    const emailInput = document.getElementById("email");
    const nameInput = document.getElementById("name");

    let isLoginMode = true;

    function setMode(login) {
      isLoginMode = login;
      if (tabLogin && tabRegister) {
        tabLogin.classList.toggle("active", isLoginMode);
        tabRegister.classList.toggle("active", !isLoginMode);
      }
      if (nameGroup) {
        nameGroup.style.display = isLoginMode ? "none" : "block";
      }
      
      const titleEl = document.getElementById("auth-card-title");
      const subEl = document.getElementById("auth-card-sub");
      
      if (titleEl) {
        titleEl.textContent = isLoginMode ? t("auth.login_title") : t("auth.register_title");
        titleEl.setAttribute("data-i18n", isLoginMode ? "auth.login_title" : "auth.register_title");
      }
      if (subEl) {
        subEl.textContent = isLoginMode ? t("auth.login_sub") : t("auth.register_sub");
        subEl.setAttribute("data-i18n", isLoginMode ? "auth.login_sub" : "auth.register_sub");
      }
      if (submitText) {
        submitText.textContent = isLoginMode ? t("auth.signin_btn") : t("auth.signup_btn");
        submitText.setAttribute("data-i18n", isLoginMode ? "auth.signin_btn" : "auth.signup_btn");
      }
      if (switchLink) {
        switchLink.textContent = isLoginMode ? t("auth.need_account") : t("auth.have_account");
        switchLink.setAttribute("data-i18n", isLoginMode ? "auth.need_account" : "auth.have_account");
      }

      clearErrors();
    }

    function clearErrors() {
      document.querySelectorAll(".inline-error").forEach((el) => {
        el.classList.remove("visible");
        el.textContent = "";
      });
      document.querySelectorAll(".form-input").forEach((el) => {
        el.classList.remove("error");
      });
    }

    function showError(inputEl, errorElId, message) {
      if (inputEl) inputEl.classList.add("error");
      const errEl = document.getElementById(errorElId);
      if (errEl) {
        errEl.textContent = message;
        errEl.classList.add("visible");
      }
    }

    function validate() {
      clearErrors();
      let valid = true;

      // Email validation
      const email = emailInput.value.trim();
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!email || !emailRegex.test(email)) {
        showError(emailInput, "email-error", t("auth.email_error", "Please enter a valid email address."));
        valid = false;
      }

      // Password validation
      const password = pwdInput.value;
      if (!password || password.length < 8) {
        showError(pwdInput, "password-error", t("auth.pass_min_error", "Password must be at least 8 characters long."));
        valid = false;
      }

      // Name validation for registration
      if (!isLoginMode) {
        const name = nameInput.value.trim();
        if (!name || name.length < 2) {
          showError(nameInput, "name-error", t("auth.name_error", "Please enter your name."));
          valid = false;
        }
      }

      return valid;
    }

    // Toggle Password Visibility
    if (pwdToggle && pwdInput) {
      pwdToggle.addEventListener("click", () => {
        const isPassword = pwdInput.type === "password";
        pwdInput.type = isPassword ? "text" : "password";
        pwdToggle.textContent = isPassword ? "🙈" : "👁️";
        pwdToggle.setAttribute("aria-label", isPassword ? "Hide password" : "Show password");
      });
    }

    // Tabs & Switchers
    if (tabLogin) tabLogin.addEventListener("click", () => setMode(true));
    if (tabRegister) tabRegister.addEventListener("click", () => setMode(false));
    if (switchLink) switchLink.addEventListener("click", () => setMode(!isLoginMode));

    // Form Submission
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!validate()) {
        card.classList.remove("shake");
        void card.offsetWidth;
        card.classList.add("shake");
        return;
      }

      submitBtn.disabled = true;
      submitSpinner.style.display = "inline-block";

      const endpoint = isLoginMode ? "/api/auth/login" : "/api/auth/register";
      const payload = {
        email: emailInput.value.trim(),
        password: pwdInput.value,
      };
      if (!isLoginMode) {
        payload.name = nameInput.value.trim();
      }

      try {
        const res = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        let data = {};
        const text = await res.text();
        try {
          data = JSON.parse(text);
        } catch {
          // Response body was not JSON (e.g. 500 HTML or raw text)
        }

        if (!res.ok) {
          let errorMsg = (data && data.detail) ? data.detail : null;
          if (!errorMsg) {
            if (res.status === 401) {
              errorMsg = isLoginMode ? "Invalid email or password." : "Authentication failed.";
            } else if (res.status === 400) {
              errorMsg = "Invalid request or account already exists.";
            } else if (res.status === 429) {
              errorMsg = "Too many attempts. Please wait a moment and try again.";
            } else if (res.status >= 500) {
              errorMsg = "Server error occurred. Please try again shortly.";
            } else {
              errorMsg = (text && text.length < 120 && !text.includes("<")) ? text : "Authentication request failed.";
            }
          }
          throw new Error(errorMsg);
        }

        const successMsg = isLoginMode ? t("auth.login_success") : t("auth.register_success");
        showToast(successMsg, "success");

        // Smooth transition & redirect to home
        card.style.opacity = "0.7";
        card.style.transform = "scale(0.98)";
        setTimeout(() => {
          location.replace("/");
        }, 350);

      } catch (err) {
        card.classList.remove("shake");
        void card.offsetWidth;
        card.classList.add("shake");
        showToast(err.message, "error");
        showError(pwdInput, "password-error", err.message);
      } finally {
        submitBtn.disabled = false;
        submitSpinner.style.display = "none";
      }
    });

    // Default mode: Login
    setMode(true);
  }

  // Initialize on DOM Ready
  document.addEventListener("DOMContentLoaded", () => {
    const defaultLogoutBtn = document.getElementById("btn-logout-nav");
    if (defaultLogoutBtn) defaultLogoutBtn.addEventListener("click", doLogout);

    if (location.pathname === "/login") {
      initAuthPage();
    } else {
      checkUserState();
    }
  });

  window.checkUserState = checkUserState;
})();
