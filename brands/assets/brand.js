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
const carouselLayout = window.matchMedia('(max-width: 900px), (hover: none) and (pointer: coarse)');
if (track && cards.length) {
  const section = track.closest('.brands');
  const dots = [...section.querySelectorAll('.carousel-dot')];
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let index = 0;
  let looping = false;
  let timer;
  let settling;
  let swipeFeedbackTimer;
  let swipeStartLeft = null;
  let layoutFrame;
  let arranging = false;
  let targetLeft = null;
  let pointerOrigin = null;
  let dragged = false;
  let touching = false;
  let foreground = true;
  let paused = reducedMotion.matches;
  const wrap = (value) => ((value % cards.length) + cards.length) % cards.length;
  const stop = () => clearTimeout(timer);
  const canPlay = () => looping && !paused && !document.hidden && foreground && !pointerOrigin && !touching
    && !nav?.classList.contains('open') && !track.contains(document.activeElement);
  const schedule = () => {
    stop();
    if (canPlay()) timer = setTimeout(() => move(1), 3000);
  };
  const update = () => {
    dots.forEach((dot, i) => dot.setAttribute('aria-current', String(i === index)));
    section.querySelectorAll('.brand-card.is-revealed').forEach((card) => {
      if (card.href !== cards[index].href) card.classList.remove('is-revealed');
    });
  };
  const clearSwipeFeedback = () => {
    clearTimeout(swipeFeedbackTimer);
    track.classList.remove('is-swipe-feedback');
    track.querySelectorAll('.is-swipe-feedback').forEach((card) => card.classList.remove('is-swipe-feedback'));
  };
  const showSwipeFeedback = (destination = null) => {
    if (!looping) return;
    const items = [...track.querySelectorAll('.brand-card')];
    if (destination === null) {
      const origin = swipeStartLeft ?? (index + 1) * track.clientWidth;
      const delta = track.scrollLeft - origin;
      if (Math.abs(delta) < 2) return;
      const fraction = track.scrollLeft / track.clientWidth;
      destination = delta > 0 ? Math.ceil(fraction - .001) : Math.floor(fraction + .001);
    }
    destination = Math.max(0, Math.min(items.length - 1, destination));
    track.classList.add('is-swipe-feedback');
    items.forEach((card, physical) => {
      card.classList.toggle('is-swipe-feedback', physical === destination);
      if (physical !== destination) card.classList.remove('is-pressed', 'is-revealed');
    });
    clearTimeout(swipeFeedbackTimer);
    swipeFeedbackTimer = setTimeout(clearSwipeFeedback, 650);
  };
  const physicalIndex = () => Math.round(track.scrollLeft / track.clientWidth);
  const position = (physical, animate = false) => {
    targetLeft = physical * track.clientWidth;
    track.scrollTo({ left: targetLeft, behavior: animate && !reducedMotion.matches ? 'smooth' : 'auto' });
  };
  const normalize = () => {
    const physical = physicalIndex();
    const destination = physical === 0 ? cards.length : physical === cards.length + 1 ? 1 : null;
    if (destination !== null) {
      position(destination);
      swipeStartLeft = destination * track.clientWidth;
      if (track.classList.contains('is-swipe-feedback')) showSwipeFeedback(destination);
    }
  };
  const settle = () => {
    if (!looping) return;
    if (targetLeft !== null && Math.abs(track.scrollLeft - targetLeft) > 1) return;
    const manual = targetLeft === null;
    targetLeft = null;
    index = wrap(physicalIndex() - 1);
    normalize();
    update();
    swipeStartLeft = track.scrollLeft;
    const active = track.querySelector('.brand-card.is-swipe-feedback');
    if (active && active.href !== cards[index].href) clearSwipeFeedback();
    if (manual) schedule();
  };
  const select = (requested, focus = false) => {
    stop();
    index = wrap(requested);
    if (looping) position(index + 1, true);
    if (focus) cards[index].focus({ preventScroll: true });
    update();
    schedule();
  };
  function move(direction) {
    if (!looping) return;
    stop();
    normalize();
    const physical = physicalIndex();
    index = wrap(physical - 1 + direction);
    position(physical + direction, true);
    update();
    schedule();
  }
  const clone = (card) => {
    const copy = card.cloneNode(true);
    copy.classList.add('carousel-clone');
    copy.setAttribute('aria-hidden', 'true');
    copy.tabIndex = -1;
    return copy;
  };
  const layout = () => {
    stop();
    clearTimeout(settling);
    cancelAnimationFrame(layoutFrame);
    clearSwipeFeedback();
    arranging = true;
    track.querySelectorAll('.carousel-clone').forEach((card) => card.remove());
    looping = carouselLayout.matches;
    if (looping) {
      track.prepend(clone(cards[cards.length - 1]));
      track.append(clone(cards[0]));
    } else track.scrollLeft = 0;
    layoutFrame = requestAnimationFrame(() => {
      if (looping) position(index + 1);
      arranging = false;
      update();
      schedule();
    });
  };
  section.querySelector('.previous-card')?.addEventListener('click', () => move(-1));
  section.querySelector('.next-card')?.addEventListener('click', () => move(1));
  dots.forEach((dot, i) => dot.addEventListener('click', () => select(i)));
  track.addEventListener('scroll', () => {
    if (!looping || arranging) return;
    if (targetLeft === null) stop();
    if (targetLeft === null || track.classList.contains('is-swipe-feedback')) showSwipeFeedback();
    index = wrap(physicalIndex() - 1);
    update();
    clearTimeout(settling);
    settling = setTimeout(settle, 160);
  }, { passive: true });
  track.addEventListener('keydown', (event) => {
    if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
    event.preventDefault();
    if (looping) { move(event.key === 'ArrowRight' ? 1 : -1); cards[index].focus({ preventScroll: true }); }
    else {
      const current = cards.indexOf(document.activeElement);
      select((current >= 0 ? current : index) + (event.key === 'ArrowRight' ? 1 : -1), true);
    }
  });
  section.addEventListener('pointerdown', (event) => {
    stop();
    if (track.contains(event.target)) { targetLeft = null; swipeStartLeft = track.scrollLeft; pointerOrigin = { x: event.clientX, y: event.clientY }; dragged = false; }
  });
  track.addEventListener('pointermove', (event) => {
    if (pointerOrigin && Math.hypot(event.clientX - pointerOrigin.x, event.clientY - pointerOrigin.y) > 10) { dragged = true; showSwipeFeedback(); }
  }, { passive: true });
  track.addEventListener('click', (event) => {
    if (dragged && event.detail !== 0) { event.preventDefault(); dragged = false; }
  });
  const release = () => { pointerOrigin = null; schedule(); };
  document.addEventListener('pointerup', release);
  document.addEventListener('pointercancel', release);
  track.addEventListener('touchstart', () => { targetLeft = null; swipeStartLeft = track.scrollLeft; touching = true; stop(); }, { passive: true });
  const endTouch = () => { touching = false; schedule(); };
  document.addEventListener('touchend', endTouch, { passive: true });
  document.addEventListener('touchcancel', endTouch, { passive: true });
  track.addEventListener('focusin', stop);
  track.addEventListener('focusout', () => setTimeout(schedule, 0));
  toggle?.addEventListener('click', schedule);
  nav?.addEventListener('click', schedule);
  document.addEventListener('click', schedule);
  document.addEventListener('keydown', (event) => { if (event.key === 'Escape') schedule(); });
  document.addEventListener('visibilitychange', () => { if (document.hidden) clearSwipeFeedback(); schedule(); });
  window.addEventListener('blur', () => { foreground = false; stop(); clearSwipeFeedback(); });
  window.addEventListener('focus', () => { foreground = true; schedule(); });
  window.addEventListener('resize', layout);
  reducedMotion.addEventListener('change', () => { paused = reducedMotion.matches; update(); schedule(); });
  layout();
}

// Mobile taps show the active image for half a second before entering the theme.
let pendingThemeNavigation = null;
let themeTapOrigin = null;
const cancelThemeNavigation = () => {
  if (pendingThemeNavigation) clearTimeout(pendingThemeNavigation.timer);
  pendingThemeNavigation = null;
  track?.classList.remove('is-tap-feedback');
  track?.querySelectorAll('.is-revealed').forEach((card) => card.classList.remove('is-revealed'));
};
track?.addEventListener('click', (event) => {
  const card = event.target.closest('.brand-card');
  if (!card || !carouselLayout.matches || event.detail === 0) return;
  if (event.defaultPrevented) { cancelThemeNavigation(); return; }
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  event.preventDefault();
  if (pendingThemeNavigation?.href === card.href) return;
  cancelThemeNavigation();
  track.classList.add('is-tap-feedback');
  track.querySelectorAll('.brand-card').forEach((other) => {
    other.classList.toggle('is-revealed', other.href === card.href);
  });
  const href = card.href;
  const timer = setTimeout(() => {
    pendingThemeNavigation = null;
    window.location.assign(href);
  }, 500);
  pendingThemeNavigation = { href, timer };
});
track?.addEventListener('pointerdown', (event) => {
  themeTapOrigin = { x: event.clientX, y: event.clientY };
}, { passive: true });
track?.addEventListener('pointermove', (event) => {
  if (themeTapOrigin && Math.hypot(event.clientX - themeTapOrigin.x, event.clientY - themeTapOrigin.y) > 10) cancelThemeNavigation();
}, { passive: true });
document.addEventListener('pointerup', () => { themeTapOrigin = null; }, { passive: true });
document.addEventListener('pointercancel', () => { themeTapOrigin = null; cancelThemeNavigation(); }, { passive: true });
track?.closest('.brands')?.addEventListener('click', (event) => {
  if (event.target.closest('.carousel-arrow, .carousel-dot')) cancelThemeNavigation();
});
carouselLayout.addEventListener('change', cancelThemeNavigation);
window.addEventListener('blur', cancelThemeNavigation);
document.addEventListener('visibilitychange', () => { if (document.hidden) cancelThemeNavigation(); });

// Delegation also handles the mobile carousel's cloned cards.
let pressedFashionCard = null;
let fashionPressOrigin = null;
const releaseFashionCard = () => {
  pressedFashionCard?.classList.remove('is-pressed');
  pressedFashionCard = null;
  fashionPressOrigin = null;
};
document.addEventListener('pointerdown', (event) => {
  releaseFashionCard();
  const card = event.target.closest('.fashion-lifestyle-card');
  if (!card || event.button !== 0 || carouselLayout.matches) return;
  pressedFashionCard = card;
  fashionPressOrigin = { x: event.clientX, y: event.clientY };
  card.classList.add('is-pressed');
}, { passive: true });
document.addEventListener('pointermove', (event) => {
  if (fashionPressOrigin && Math.hypot(event.clientX - fashionPressOrigin.x, event.clientY - fashionPressOrigin.y) > 10) releaseFashionCard();
}, { passive: true });
document.addEventListener('pointerup', releaseFashionCard, { passive: true });
document.addEventListener('pointercancel', releaseFashionCard, { passive: true });
window.addEventListener('blur', releaseFashionCard);
document.addEventListener('visibilitychange', () => { if (document.hidden) releaseFashionCard(); });
