/* PWA Service Worker & Offline Sync */
function initPWA() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').then((reg) => {
      console.log('[Kandezhuthu PWA] Service Worker registered:', reg.scope);
    }).catch((err) => {
      console.warn('[Kandezhuthu PWA] Service Worker registration failed:', err);
    });
  }

  function updateOnlineStatus() {
    const badge = document.getElementById("pwa-status-badge");
    const dot = document.getElementById("pwa-dot");
    const text = document.getElementById("pwa-status-text");
    if (badge) badge.hidden = navigator.onLine;
    if (text) text.textContent = currentLanguage === "ml" ? "ഓഫ്‌ലൈൻ" : "Offline";
  }

  window.addEventListener('online', updateOnlineStatus);
  window.addEventListener('offline', updateOnlineStatus);
  updateOnlineStatus();
}

window.addEventListener("DOMContentLoaded", async () => {
  try {
    await loadTranslations();
  } catch (e) {
    console.warn("[Kandezhuthu UI] Could not load translations:", e);
  }
  initMap();
  initHud();
  initPWA();
  setLanguage(currentLanguage);
  setWorkflowStep(1);
  initTouchDragScroll("step-nav-bar");
  initTouchDragScroll("workflow-bar");

  // Auto-refresh dev watcher: detects code edits, static changes & server restarts
  (function initDevAutoRefresh() {
    let lastState = null;
    let serverWasDown = false;

    async function checkVersion() {
      try {
        const res = await fetch('/api/dev/version?t=' + Date.now(), { cache: 'no-store' });
        if (res.ok) {
          const data = await res.json();
          const currentState = `${data.server_start}_${data.static_mtime}`;
          if (serverWasDown) {
            console.log("[Auto-Refresh] Server is back online. Refreshing page...");
            window.location.reload();
            return;
          }
          if (lastState !== null && lastState !== currentState) {
            console.log("[Auto-Refresh] Change detected on server. Refreshing page...");
            window.location.reload();
            return;
          }
          lastState = currentState;
          serverWasDown = false;
        } else {
          serverWasDown = true;
        }
      } catch (e) {
        serverWasDown = true;
      }
    }

    setInterval(checkVersion, 1000);
  })();
});
