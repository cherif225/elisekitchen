/**
 * ELISE KITCHEN — Site Public JS
 * Panier AJAX, animations, interactions
 */

(function () {
  'use strict';

  /* ── TOAST NOTIFICATION ───────────────────────────────────── */
  window.showToast = function (msg, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) return;

    const icons = { success: 'check-circle', error: 'exclamation-circle', warning: 'triangle-exclamation' };
    const toast = document.createElement('div');
    toast.className = `toast-msg ${type}`;
    toast.innerHTML = `<i class="fas fa-${icons[type] || icons.success}"></i>${msg}`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.animation = 'slideIn 0.3s ease reverse';
      setTimeout(() => toast.remove(), 280);
    }, 3500);
  };

  /* ── PANIER : MISE À JOUR COMPTEUR NAVBAR ─────────────────── */
  function updateNavBadge(count) {
    let badge = document.getElementById('nav-badge');
    const txt = document.getElementById('nav-panier-txt');
    if (count > 0) {
      if (!badge) {
        badge = document.createElement('span');
        badge.id = 'nav-badge';
        badge.className = 'panier-badge';
        document.getElementById('nav-panier')?.appendChild(badge);
      }
      badge.textContent = count;
      badge.style.transform = 'scale(1.3)';
      setTimeout(() => { if (badge) badge.style.transform = ''; }, 300);
    } else {
      badge?.remove();
    }
    if (txt) txt.textContent = `Panier${count > 0 ? ` (${count})` : ''}`;
  }

  /* ── AJOUT AU PANIER (AJAX) ───────────────────────────────── */
  window.addToCart = function (prodId, qty = 1) {
    return fetch('/panier/ajouter', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({ produit_id: prodId, quantite: qty })
    })
      .then(r => r.json())
      .then(d => {
        if (d.success) {
          updateNavBadge(d.nb_panier);
          showToast(d.message, 'success');
        } else {
          showToast(d.message || 'Erreur lors de l\'ajout', 'error');
        }
        return d;
      })
      .catch(() => showToast('Erreur réseau', 'error'));
  };

  /* ── ANIMATION BOUTON AJOUTER ─────────────────────────────── */
  window.addAndAnimate = function (btn, id, qty = 1) {
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    addToCart(id, qty).then(d => {
      if (d && d.success) {
        btn.classList.add('added');
        btn.innerHTML = '<i class="fas fa-check"></i>';
        setTimeout(() => {
          btn.classList.remove('added');
          btn.innerHTML = '<i class="fas fa-plus"></i>';
          btn.disabled = false;
        }, 1800);
      } else {
        btn.innerHTML = '<i class="fas fa-plus"></i>';
        btn.disabled = false;
      }
    });
  };

  /* ── ANIMATION D'ENTRÉE AU SCROLL ────────────────────────── */
  function initScrollAnimations() {
    if (!window.IntersectionObserver) return;
    const observer = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.style.opacity = '1';
          e.target.style.transform = 'translateY(0) scale(1)';
          observer.unobserve(e.target);
        }
      });
    }, { threshold: 0.08 });

    document.querySelectorAll('.produit-card, .cat-card, .stat-pill').forEach((el, i) => {
      el.style.cssText += `
        opacity: 0;
        transform: translateY(24px) scale(0.97);
        transition: opacity 0.5s ease ${i * 0.06}s, transform 0.5s ease ${i * 0.06}s;
      `;
      observer.observe(el);
    });
  }

  /* ── QUANTITÉ PANIER LIVE ─────────────────────────────────── */
  window.changeQty = function (id, delta, newVal = null) {
    const inp = document.getElementById(`qty-${id}`);
    if (!inp) return;
    let qty = newVal !== null ? parseInt(newVal) : Math.max(0, parseInt(inp.value) + delta);
    if (isNaN(qty)) qty = 0;
    inp.value = qty;

    fetch('/panier/modifier', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({ produit_id: id, quantite: qty })
    })
      .then(r => r.json())
      .then(d => {
        if (!d.success) return;

        // Supprimer la ligne si qty = 0
        if (qty === 0) {
          const row = document.getElementById(`item-${id}`);
          if (row) {
            row.style.transition = 'opacity 0.3s, transform 0.3s';
            row.style.opacity = '0';
            row.style.transform = 'translateX(20px)';
            setTimeout(() => {
              row.remove();
              if (d.nb_panier === 0) location.reload();
            }, 300);
          }
        } else {
          const priceEl = document.getElementById(`prix-${id}`);
          if (priceEl) {
            priceEl.textContent = parseFloat(d.total).toLocaleString('fr-FR') + ' F';
          }
        }

        // Total global
        const totalEl = document.getElementById('recap-total');
        if (totalEl) totalEl.textContent = parseFloat(d.total).toLocaleString('fr-FR') + ' FCFA';

        updateNavBadge(d.nb_panier);
      })
      .catch(() => showToast('Erreur réseau', 'error'));
  };

  /* ── SUIVI COMMANDE : FORMULAIRE AUTO-UPPERCASE ───────────── */
  const suiviInput = document.querySelector('input[name="numero"]');
  if (suiviInput) {
    suiviInput.addEventListener('input', function () {
      const pos = this.selectionStart;
      this.value = this.value.toUpperCase();
      this.setSelectionRange(pos, pos);
    });
  }

  /* ── LAZY LOAD IMAGES ─────────────────────────────────────── */
  if ('loading' in HTMLImageElement.prototype) {
    document.querySelectorAll('img[data-src]').forEach(img => {
      img.src = img.dataset.src;
    });
  }

  /* ── NAVBAR : OMBRE AU SCROLL ─────────────────────────────── */
  const navbar = document.querySelector('.navbar-pub');
  if (navbar) {
    window.addEventListener('scroll', () => {
      navbar.style.boxShadow = window.scrollY > 20
        ? '0 4px 20px rgba(61,31,10,0.12)'
        : 'none';
    }, { passive: true });
  }

  /* ── TOGGLE MODE LIVRAISON CHECKOUT ─────────────────────────*/
  const livraisonRadios = document.querySelectorAll('input[name="type_livraison"]');
  const adresseBlock = document.getElementById('adresse-block');
  if (livraisonRadios.length && adresseBlock) {
    livraisonRadios.forEach(r => {
      r.addEventListener('change', () => {
        const show = r.value === 'livraison' && r.checked;
        adresseBlock.style.display = show ? 'block' : 'none';
        const adresseInput = adresseBlock.querySelector('input');
        if (adresseInput) adresseInput.required = show;
      });
    });
  }

  /* ── INIT ─────────────────────────────────────────────────── */
  document.addEventListener('DOMContentLoaded', () => {
    initScrollAnimations();
  });

  // Exécuter aussi si DOM déjà prêt
  if (document.readyState !== 'loading') {
    initScrollAnimations();
  }

})();
