/**
 * ELISE KITCHEN Admin — Temps réel & interactions
 * Polling nouvelles commandes, horloge live, notifications
 */

(function () {
  'use strict';

  /* ── HORLOGE TEMPS RÉEL ───────────────────────────────────── */
  function updateClock() {
    const el = document.getElementById('topbarDate');
    if (!el) return;
    const now = new Date();
    el.textContent = now.toLocaleDateString('fr-FR', {
      weekday: 'short', day: 'numeric', month: 'short', year: 'numeric'
    }) + ' · ' + now.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  }
  updateClock();
  setInterval(updateClock, 30000);

  /* ── POLLING NOUVELLES COMMANDES (toutes les 30s) ─────────── */
  let lastNouvellesCount = parseInt(
    document.querySelector('.sb-badge')?.textContent || '0'
  );

  function pollNouvellesCommandes() {
    fetch('/admin/api/stats', { credentials: 'same-origin' })
      .then(r => r.json())
      .then(data => {
        if (!data || data.error) return;

        // Nouvelles commandes depuis les statuts
        const statuts = data.statuts || [];
        const nouvelles = statuts.find(s => s.statut === 'nouvelle');
        const count = nouvelles ? parseInt(nouvelles.nb) : 0;

        // Mettre à jour le badge sidebar
        const badge = document.querySelector('.admin-sidebar .sb-badge');
        const bellDot = document.querySelector('.bell-dot');

        if (count > 0) {
          if (badge) {
            badge.textContent = count;
            badge.style.display = '';
          }
          if (bellDot) bellDot.style.display = '';
        } else {
          if (badge) badge.style.display = 'none';
          if (bellDot) bellDot.style.display = 'none';
        }

        // Notification si nouvelle commande arrivée
        if (count > lastNouvellesCount && lastNouvellesCount >= 0) {
          const diff = count - lastNouvellesCount;
          showAdminToast(
            `🛒 ${diff} nouvelle${diff > 1 ? 's' : ''} commande${diff > 1 ? 's' : ''} reçue${diff > 1 ? 's' : ''} !`,
            'new-order',
            8000
          );
          // Son de notification (bip léger)
          playNotifSound();
        }
        lastNouvellesCount = count;
      })
      .catch(() => {}); // Silencieux si pas connecté
  }

  // Démarrer le polling après 5 secondes (laisser la page charger)
  setTimeout(() => {
    pollNouvellesCommandes();
    setInterval(pollNouvellesCommandes, 30000);
  }, 5000);

  /* ── SON DE NOTIFICATION ──────────────────────────────────── */
  function playNotifSound() {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.frequency.setValueAtTime(880, ctx.currentTime);
      osc.frequency.setValueAtTime(1100, ctx.currentTime + 0.1);
      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.5);
    } catch (e) {}
  }

  /* ── TOAST ADMIN ──────────────────────────────────────────── */
  function showAdminToast(msg, type = 'info', duration = 4000) {
    let container = document.getElementById('adminToastContainer');
    if (!container) {
      container = document.createElement('div');
      container.id = 'adminToastContainer';
      container.style.cssText = `
        position: fixed; bottom: 24px; right: 24px; z-index: 9999;
        display: flex; flex-direction: column; gap: 10px;
        pointer-events: none;
      `;
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const colors = {
      'new-order': '#D97706',
      'success':   '#059669',
      'error':     '#E03131',
      'info':      '#2563EB'
    };
    toast.style.cssText = `
      background: white;
      border-left: 4px solid ${colors[type] || colors.info};
      border-radius: 10px;
      padding: 14px 18px;
      font-size: 0.85rem;
      font-family: Inter, sans-serif;
      font-weight: 500;
      color: #111827;
      box-shadow: 0 8px 28px rgba(0,0,0,0.15);
      min-width: 280px;
      max-width: 360px;
      display: flex; align-items: center; gap: 10px;
      animation: slideInRight 0.3s ease;
      pointer-events: all;
      cursor: pointer;
    `;
    toast.innerHTML = msg;
    toast.addEventListener('click', () => dismissToast(toast));

    container.appendChild(toast);

    const t = setTimeout(() => dismissToast(toast), duration);
    toast._timer = t;
    return toast;
  }

  function dismissToast(toast) {
    clearTimeout(toast._timer);
    toast.style.animation = 'slideOutRight 0.3s ease';
    setTimeout(() => toast.remove(), 280);
  }

  // Expose globally
  window.showAdminToast = showAdminToast;

  /* ── STYLES ANIMATIONS TOAST ──────────────────────────────── */
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideInRight {
      from { transform: translateX(120%); opacity: 0; }
      to   { transform: translateX(0);    opacity: 1; }
    }
    @keyframes slideOutRight {
      from { transform: translateX(0);    opacity: 1; }
      to   { transform: translateX(120%); opacity: 0; }
    }
  `;
  document.head.appendChild(style);

  /* ── CONFIRMATION SUPPRESSION ─────────────────────────────── */
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', e => {
      if (!confirm(el.dataset.confirm)) e.preventDefault();
    });
  });

  /* ── RECHERCHE INSTANTANÉE TABLES ─────────────────────────── */
  document.querySelectorAll('[data-search-table]').forEach(input => {
    const tableId = input.dataset.searchTable;
    const table = document.getElementById(tableId);
    if (!table) return;
    input.addEventListener('input', function () {
      const q = this.value.toLowerCase();
      table.querySelectorAll('tbody tr').forEach(row => {
        row.style.display = (!q || row.textContent.toLowerCase().includes(q)) ? '' : 'none';
      });
    });
  });

  /* ── MISE À JOUR SIDEBAR ACTIVE AU CLIC ───────────────────── */
  document.querySelectorAll('.admin-sidebar .sb-item').forEach(item => {
    item.addEventListener('click', function () {
      document.querySelectorAll('.admin-sidebar .sb-item').forEach(i => i.classList.remove('active'));
      this.classList.add('active');
    });
  });

  /* ── TOGGLE SIDEBAR MOBILE ────────────────────────────────── */
  const sidebar = document.getElementById('adminSidebar');
  const topbar  = document.getElementById('adminTopbar');
  const main    = document.getElementById('adminMain');

  window.toggleSidebar = function () {
    const collapsed = sidebar.classList.toggle('collapsed');
    topbar?.classList.toggle('expanded', collapsed);
    main?.classList.toggle('expanded', collapsed);
    localStorage.setItem('sidebarCollapsed', collapsed ? '1' : '0');
  };

  // Restaurer état sidebar depuis localStorage
  if (localStorage.getItem('sidebarCollapsed') === '1') {
    sidebar?.classList.add('collapsed');
    topbar?.classList.add('expanded');
    main?.classList.add('expanded');
  }

  /* ── AUTO-DISMISS FLASH MESSAGES ─────────────────────────── */
  setTimeout(() => {
    document.querySelectorAll('.flash-item').forEach(el => {
      el.style.transition = 'opacity 0.5s, transform 0.5s';
      el.style.opacity = '0';
      el.style.transform = 'translateY(-8px)';
      setTimeout(() => el.remove(), 500);
    });
  }, 5000);

  /* ── CONFIRM AVANT ACTIONS DESTRUCTIVES ───────────────────── */
  document.querySelectorAll('a[href*="supprimer"], a[href*="annulee"]').forEach(a => {
    if (!a.getAttribute('onclick')) {
      a.addEventListener('click', e => {
        if (!confirm('Confirmer cette action ?')) e.preventDefault();
      });
    }
  });

})();
