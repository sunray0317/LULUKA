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
const carouselLayout = window.matchMedia('(max-width: 900px)');
if (track && cards.length) {
  let pointerOrigin = null;
  let dragged = false;
  const clearPressed = () => cards.forEach((card) => card.classList.remove('is-pressed'));
  cards.forEach((card) => {
    card.addEventListener('pointerdown', () => card.classList.add('is-pressed'));
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
  const previous = document.querySelector('.previous-card');
  const next = document.querySelector('.next-card');
  const nearestIndex = () => {
    const center = track.getBoundingClientRect().x + track.clientWidth / 2;
    return cards.reduce((best, card, index) => {
      const bounds = card.getBoundingClientRect();
      const distance = Math.abs(bounds.x + bounds.width / 2 - center);
      return distance < best.distance ? { index, distance } : best;
    }, { index: 0, distance: Infinity }).index;
  };
  const updateControls = () => {
    const index = nearestIndex();
    if (previous) previous.disabled = index === 0;
    if (next) next.disabled = index === cards.length - 1;
  };
  const selectCard = (requestedIndex, focus = false) => {
    const index = Math.max(0, Math.min(cards.length - 1, requestedIndex));
    const card = cards[index];
    if (focus) card.focus({ preventScroll: true });
    if (carouselLayout.matches) {
      const center = track.getBoundingClientRect().x + track.clientWidth / 2;
      const bounds = card.getBoundingClientRect();
      track.scrollBy({ left: bounds.x + bounds.width / 2 - center, behavior: 'instant' });
    }
    updateControls();
  };
  previous?.addEventListener('click', () => selectCard(nearestIndex() - 1));
  next?.addEventListener('click', () => selectCard(nearestIndex() + 1));
  track.addEventListener('keydown', (event) => {
    if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
    event.preventDefault();
    const focused = cards.indexOf(document.activeElement);
    const current = focused >= 0 ? focused : nearestIndex();
    selectCard(current + (event.key === 'ArrowRight' ? 1 : -1), true);
  });
  track.addEventListener('scroll', updateControls, { passive: true });
  window.addEventListener('resize', updateControls, { passive: true });
  updateControls();
  document.addEventListener('pointerup', () => { pointerOrigin = null; clearPressed(); });
  document.addEventListener('pointercancel', () => { pointerOrigin = null; dragged = false; clearPressed(); });
  window.addEventListener('blur', () => { pointerOrigin = null; clearPressed(); });
}
