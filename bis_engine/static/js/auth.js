/* =====================================================================
   Authentication Client Module (auth.js)
   Handles Login, Supabase Registration, OTP Verification, Input Validation & Auth State
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

  // Login / Register / OTP Page Logic
  function initAuthPage() {
    const card = document.getElementById("auth-card");
    const form = document.getElementById("auth-form");
    const otpForm = document.getElementById("otp-form");
    if (!form || !card) return;

    const tabLogin = document.getElementById("tab-login");
    const tabRegister = document.getElementById("tab-register");
    const authTabs = document.querySelector(".auth-tabs");
    const authFooter = document.getElementById("auth-footer");
    const nameGroup = document.getElementById("name-group");
    const submitBtn = document.getElementById("submit-btn");
    const submitText = document.getElementById("submit-text");
    const submitSpinner = document.getElementById("submit-spinner");
    const switchLink = document.getElementById("switch-auth-link");
    const pwdToggle = document.getElementById("toggle-password");
    const pwdInput = document.getElementById("password");
    const emailInput = document.getElementById("email");
    const nameInput = document.getElementById("name");

    const otpInput = document.getElementById("otp-code");
    const otpError = document.getElementById("otp-error");
    const otpEmailLabel = document.getElementById("otp-email-label");
    const verifyOtpBtn = document.getElementById("verify-otp-btn");
    const verifySpinner = document.getElementById("verify-spinner");
    const resendOtpBtn = document.getElementById("resend-otp-btn");
    const cancelOtpBtn = document.getElementById("cancel-otp-btn");

    let isLoginMode = true;
    let pendingEmail = "";

    function setMode(login) {
      isLoginMode = login;
      if (otpForm) otpForm.style.display = "none";
      if (form) form.style.display = "block";
      if (authTabs) authTabs.style.display = "flex";
      if (authFooter) authFooter.style.display = "block";

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
        titleEl.textContent = isLoginMode ? t("auth.login_title", "Sign In") : t("auth.register_title", "Create an Account");
      }
      if (subEl) {
        subEl.textContent = isLoginMode ? t("auth.login_sub", "Sign in to access procurement standards and tools") : t("auth.register_sub", "Sign up to access procurement standards and tools");
      }
      if (submitText) {
        submitText.textContent = isLoginMode ? t("auth.signin_btn", "Sign In") : t("auth.signup_btn", "Create Account");
      }
      if (switchLink) {
        switchLink.textContent = isLoginMode ? t("auth.need_account", "Don't have an account? Create one") : t("auth.have_account", "Already have an account? Sign in");
      }

      clearErrors();
    }

    function showOtpView(email) {
      pendingEmail = email;
      if (form) form.style.display = "none";
      if (authTabs) authTabs.style.display = "none";
      if (authFooter) authFooter.style.display = "none";
      if (otpForm) otpForm.style.display = "block";

      const titleEl = document.getElementById("auth-card-title");
      const subEl = document.getElementById("auth-card-sub");
      if (titleEl) titleEl.textContent = "Verify Your Email";
      if (subEl) subEl.textContent = "Enter the 6-digit confirmation code sent by Supabase.";
      if (otpEmailLabel) otpEmailLabel.textContent = email;
      if (otpInput) {
        otpInput.value = "";
        setTimeout(() => otpInput.focus(), 150);
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

    // Form Submission (Login & Register)
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
          // Non-JSON response
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

        // If Supabase requires OTP / email confirmation
        if (data.requires_otp || data.status === "pending_verification") {
          showToast(data.message || "Verification code sent to your email.", "info", 5000);
          showOtpView(payload.email);
          return;
        }

        const successMsg = isLoginMode ? t("auth.login_success", "Signed in successfully.") : t("auth.register_success", "Account created successfully.");
        showToast(successMsg, "success");

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

    // OTP Form Submission
    if (otpForm) {
      otpForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const otpCode = otpInput.value.trim();
        if (!otpCode || otpCode.length < 4) {
          showError(otpInput, "otp-error", "Please enter the verification code sent to your email.");
          return;
        }

        verifyOtpBtn.disabled = true;
        verifySpinner.style.display = "inline-block";

        try {
          const res = await fetch("/api/auth/verify-otp", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email: pendingEmail,
              token: otpCode,
              type: "signup",
            }),
          });

          let data = {};
          const text = await res.text();
          try {
            data = JSON.parse(text);
          } catch {}

          if (!res.ok) {
            throw new Error((data && data.detail) || "Invalid or expired verification code.");
          }

          showToast("Account verified successfully! Logging in...", "success");
          card.style.opacity = "0.7";
          card.style.transform = "scale(0.98)";
          setTimeout(() => {
            location.replace("/");
          }, 400);

        } catch (err) {
          card.classList.remove("shake");
          void card.offsetWidth;
          card.classList.add("shake");
          showToast(err.message, "error");
          showError(otpInput, "otp-error", err.message);
        } finally {
          verifyOtpBtn.disabled = false;
          verifySpinner.style.display = "none";
        }
      });
    }

    // Resend OTP Button
    if (resendOtpBtn) {
      resendOtpBtn.addEventListener("click", async () => {
        if (!pendingEmail) return;
        resendOtpBtn.disabled = true;
        resendOtpBtn.textContent = "Sending...";
        try {
          const res = await fetch("/api/auth/resend-otp", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: pendingEmail }),
          });
          const data = await res.json().catch(() => ({}));
          if (res.ok) {
            showToast("A new verification code has been sent to your email.", "success");
          } else {
            showToast(data.detail || "Could not resend code. Please try again in a moment.", "error");
          }
        } catch {
          showToast("Could not resend code. Please try again later.", "error");
        } finally {
          setTimeout(() => {
            resendOtpBtn.disabled = false;
            resendOtpBtn.textContent = "Resend Code";
          }, 3000);
        }
      });
    }

    // Cancel OTP Button
    if (cancelOtpBtn) {
      cancelOtpBtn.addEventListener("click", () => setMode(true));
    }

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
