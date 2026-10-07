const toggle = document.querySelector('.menu-toggle');
const nav = document.querySelector('#brand-nav');
if (toggle && nav) {
  const setOpen = (open) => {
    toggle.setAttribute('aria-expanded', String(open));
    nav.classList.toggle('open', open);
  };
  toggle.addEventListener('click', () => setOpen(toggle.getAttribute('aria-expanded') !== 'true'));
  nav.addEventListener('click', (event) => {
    if (event.target.closest('a')) setOpen(false);
  });
  document.addEventListener('click', (event) => {
    if (!nav.contains(event.target) && !toggle.contains(event.target)) setOpen(false);
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
      setOpen(false);
      toggle.focus();
    }
  });
}

const cards = [...document.querySelectorAll('.brand-card')];
const track = document.querySelector('.brand-cards');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const carouselLayout = window.matchMedia('(max-width: 900px)');
if (track && cards.length) {
  let frame = 0;
  let pointerOrigin = null;
  let dragged = false;
  const pointerOffsets = new Map();
  const clamp = (value, limit) => Math.max(-limit, Math.min(limit, value));
  const updateLayers = () => {
    frame = 0;
    if (reducedMotion.matches) return;
    const trackBounds = track.getBoundingClientRect();
    cards.forEach((card) => {
      const bounds = card.getBoundingClientRect();
      const pointer = pointerOffsets.get(card) || { x: 0, y: 0 };
      const scrollX = carouselLayout.matches ? clamp((bounds.x + bounds.width / 2 - trackBounds.x - trackBounds.width / 2) / bounds.width, 1) * 9 : 0;
      const scrollY = clamp((bounds.y + bounds.height / 2 - innerHeight / 2) / innerHeight, 1) * 8;
      card.style.setProperty('--motion-x', `${(scrollX + pointer.x).toFixed(2)}px`);
      card.style.setProperty('--motion-y', `${(scrollY + pointer.y).toFixed(2)}px`);
    });
  };
  const scheduleLayers = () => {
    if (!frame && !reducedMotion.matches) frame = requestAnimationFrame(updateLayers);
  };
  const clearPressed = () => cards.forEach((card) => card.classList.remove('is-pressed'));
  cards.forEach((card) => {
    card.addEventListener('pointerdown', () => card.classList.add('is-pressed'));
    card.addEventListener('pointermove', (event) => {
      if (event.pointerType !== 'mouse' || reducedMotion.matches) return;
      const bounds = card.getBoundingClientRect();
      pointerOffsets.set(card, {
        x: clamp((event.clientX - bounds.x) / bounds.width - .5, .5) * 14,
        y: clamp((event.clientY - bounds.y) / bounds.height - .5, .5) * 14,
      });
      scheduleLayers();
    });
    card.addEventListener('pointerleave', () => {
      pointerOffsets.delete(card);
      scheduleLayers();
    });
  });
  track.addEventListener('pointerdown', (event) => {
    pointerOrigin = { x: event.clientX, y: event.clientY };
    dragged = false;
  });
  track.addEventListener('pointermove', (event) => {
    if (pointerOrigin && Math.hypot(event.clientX - pointerOrigin.x, event.clientY - pointerOrigin.y) > 10) {
      dragged = true;
      clearPressed();
    }
  }, { passive: true });
  track.addEventListener('click', (event) => {
    if (dragged && event.detail !== 0) {
      event.preventDefault();
      dragged = false;
    }
  });
  track.addEventListener('keydown', (event) => {
    if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
    event.preventDefault();
    const focused = cards.indexOf(document.activeElement);
    const center = track.getBoundingClientRect().x + track.clientWidth / 2;
    const nearest = cards.reduce((best, card, index) => {
      const bounds = card.getBoundingClientRect();
      const distance = Math.abs(bounds.x + bounds.width / 2 - center);
      return distance < best.distance ? { index, distance } : best;
    }, { index: 0, distance: Infinity }).index;
    const current = focused >= 0 ? focused : nearest;
    const index = Math.max(0, Math.min(cards.length - 1, current + (event.key === 'ArrowRight' ? 1 : -1)));
    const card = cards[index];
    card.focus({ preventScroll: true });
    if (carouselLayout.matches) {
      const bounds = card.getBoundingClientRect();
      track.scrollBy({ left: bounds.x + bounds.width / 2 - center, behavior: reducedMotion.matches ? 'instant' : 'smooth' });
    }
  });
  track.addEventListener('scroll', scheduleLayers, { passive: true });
  window.addEventListener('scroll', scheduleLayers, { passive: true });
  window.addEventListener('resize', scheduleLayers, { passive: true });
  document.addEventListener('pointerup', () => { pointerOrigin = null; clearPressed(); });
  document.addEventListener('pointercancel', () => { pointerOrigin = null; dragged = false; clearPressed(); });
  window.addEventListener('blur', () => { pointerOrigin = null; clearPressed(); });
  reducedMotion.addEventListener('change', () => {
    if (reducedMotion.matches) {
      cards.forEach((card) => {
        card.style.removeProperty('--motion-x');
        card.style.removeProperty('--motion-y');
      });
    } else scheduleLayers();
  });
  scheduleLayers();
}
