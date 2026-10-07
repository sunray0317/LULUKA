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

const cards = document.querySelectorAll('.brand-card');
if (cards.length) {
  const clearPressed = () => cards.forEach((card) => card.classList.remove('is-pressed'));
  cards.forEach((card) => {
    card.addEventListener('pointerdown', () => card.classList.add('is-pressed'));
  });
  document.addEventListener('pointerup', clearPressed);
  document.addEventListener('pointercancel', clearPressed);
  window.addEventListener('blur', clearPressed);
}
