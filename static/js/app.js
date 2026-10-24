/**
 * FocusFlow — app.js
 * Vanilla JS + HTMX event wiring + Toast system + Custom confirm dialog
 */

window.FocusFlow = window.FocusFlow || {};

// ============================================================================
// HTMX: CSRF Token Setup
// ============================================================================
(function setupHtmxCsrf() {
  const metaTag = document.querySelector('meta[name="csrf-token"]');
  if (!metaTag) return;
  const csrfToken = metaTag.getAttribute('content');
  document.addEventListener('htmx:configRequest', function (event) {
    event.detail.headers['X-CSRFToken'] = csrfToken;
  });
})();

// ============================================================================
// Custom Confirm Dialog (replaces browser alert/confirm)
// ============================================================================
(function setupConfirmDialog() {
  // Inject dialog HTML once into the DOM
  const markup = `
    <div id="ff-confirm-backdrop" style="display:none;position:fixed;inset:0;z-index:500;background:rgba(15,23,42,0.45);backdrop-filter:blur(4px);-webkit-backdrop-filter:blur(4px);align-items:center;justify-content:center;padding:1rem;">
      <div id="ff-confirm-box" style="background:#fff;border:1px solid #E2E8F0;border-radius:16px;box-shadow:0 20px 25px -5px rgba(0,0,0,0.12),0 10px 10px -5px rgba(0,0,0,0.05);width:100%;max-width:400px;overflow:hidden;transform:scale(0.96);opacity:0;transition:transform 200ms ease,opacity 200ms ease;">
        <div style="padding:1.5rem 1.5rem 1rem;">
          <div style="display:flex;align-items:flex-start;gap:1rem;">
            <div style="width:36px;height:36px;border-radius:8px;background:#FEF2F2;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
              <svg viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:18px;height:18px;"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            </div>
            <div style="flex:1;min-width:0;">
              <p id="ff-confirm-title" style="font-family:Inter,sans-serif;font-size:0.9375rem;font-weight:600;color:#0F172A;letter-spacing:-0.01em;margin:0 0 0.375rem;"></p>
              <p id="ff-confirm-message" style="font-family:Inter,sans-serif;font-size:0.8125rem;color:#64748B;line-height:1.5;margin:0;"></p>
            </div>
          </div>
        </div>
        <div style="display:flex;align-items:center;justify-content:flex-end;gap:0.625rem;padding:1rem 1.5rem;border-top:1px solid #F1F5F9;background:#FAFAFA;">
          <button id="ff-confirm-cancel" style="font-family:Inter,sans-serif;font-size:0.8125rem;font-weight:500;padding:0.4375rem 0.875rem;border:1px solid #E2E8F0;border-radius:8px;background:#fff;color:#334155;cursor:pointer;transition:all 120ms ease;">Cancel</button>
          <button id="ff-confirm-ok" style="font-family:Inter,sans-serif;font-size:0.8125rem;font-weight:500;padding:0.4375rem 0.875rem;border:1px solid #EF4444;border-radius:8px;background:#EF4444;color:#fff;cursor:pointer;transition:all 120ms ease;">Delete</button>
        </div>
      </div>
    </div>`;

  document.body.insertAdjacentHTML('beforeend', markup);

  const backdrop = document.getElementById('ff-confirm-backdrop');
  const box      = document.getElementById('ff-confirm-box');
  const titleEl  = document.getElementById('ff-confirm-title');
  const msgEl    = document.getElementById('ff-confirm-message');
  const btnOk    = document.getElementById('ff-confirm-ok');
  const btnCancel = document.getElementById('ff-confirm-cancel');

  let resolveFn = null;

  function showConfirm(title, message, okLabel = 'Confirm') {
    titleEl.textContent  = title;
    msgEl.textContent    = message;
    btnOk.textContent    = okLabel;

    backdrop.style.display = 'flex';
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        box.style.transform = 'scale(1)';
        box.style.opacity   = '1';
      });
    });

    return new Promise((resolve) => { resolveFn = resolve; });
  }

  function hideConfirm(result) {
    box.style.transform = 'scale(0.96)';
    box.style.opacity   = '0';
    setTimeout(() => { backdrop.style.display = 'none'; }, 200);
    if (resolveFn) { resolveFn(result); resolveFn = null; }
  }

  btnOk.addEventListener('click',     () => hideConfirm(true));
  btnCancel.addEventListener('click', () => hideConfirm(false));
  backdrop.addEventListener('click',  (e) => { if (e.target === backdrop) hideConfirm(false); });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && backdrop.style.display === 'flex') hideConfirm(false);
  });

  // Hover styles
  btnCancel.addEventListener('mouseenter', () => { btnCancel.style.background = '#F8FAFC'; });
  btnCancel.addEventListener('mouseleave', () => { btnCancel.style.background = '#fff'; });
  btnOk.addEventListener('mouseenter',    () => { btnOk.style.background = '#DC2626'; btnOk.style.borderColor = '#DC2626'; });
  btnOk.addEventListener('mouseleave',    () => { btnOk.style.background = '#EF4444'; btnOk.style.borderColor = '#EF4444'; });

  // Override HTMX's built-in confirm handler
  document.addEventListener('htmx:confirm', function (e) {
    const message = e.detail.question;
    if (!message) return;

    e.preventDefault();

    showConfirm('Are you sure?', message, 'Delete').then((confirmed) => {
      if (confirmed) e.detail.issueRequest(true);
    });
  });

  window.FocusFlow.showConfirm = showConfirm;
})();

// ============================================================================
// Toast Notification System
// ============================================================================
(function setupToasts() {
  const container = document.getElementById('toast-container');

  function showToast(message, type = 'info', duration = 3500) {
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');

    const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };
    toast.innerHTML = `
      <span style="font-size:1rem;line-height:1;">${icons[type] || icons.info}</span>
      <span>${message}</span>
    `;

    container.appendChild(toast);

    const timer = setTimeout(() => dismissToast(toast), duration);
    toast.addEventListener('click', () => { clearTimeout(timer); dismissToast(toast); });
  }

  function dismissToast(toast) {
    toast.classList.add('toast--removing');
    toast.addEventListener('animationend', () => toast.remove(), { once: true });
    setTimeout(() => toast.remove(), 400);
  }

  window.FocusFlow.showToast = showToast;
})();

// ============================================================================
// HTMX Global Event Listeners
// ============================================================================
(function setupHtmxEvents() {
  document.body.addEventListener('htmx:afterRequest', function (event) {
    const trigger = event.detail.xhr.getResponseHeader('HX-Trigger');
    if (!trigger) return;

    if (trigger.includes('sessionCreated')) {
      window.FocusFlow.showToast('Session created.', 'success');
    } else if (trigger.includes('sessionStarted')) {
      window.FocusFlow.showToast('Session started — stay focused!', 'success');
    } else if (trigger.includes('sessionStopped')) {
      window.FocusFlow.showToast('Session stopped. Great work!', 'info');
    } else if (trigger.includes('sessionDeleted')) {
      window.FocusFlow.showToast('Session deleted.', 'warning');
    }
  });

  document.body.addEventListener('htmx:responseError', function (event) {
    const status = event.detail.xhr.status;
    if (status === 422) return;
    window.FocusFlow.showToast(`Request failed (${status}). Please try again.`, 'error');
  });
})();

// ============================================================================
// Keyboard Shortcuts
// ============================================================================
(function setupKeyboardShortcuts() {
  document.addEventListener('keydown', function (e) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      document.dispatchEvent(new CustomEvent('open-create-modal'));
    }
  });
})();

