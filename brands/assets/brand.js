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
  };
  const physicalIndex = () => Math.round(track.scrollLeft / track.clientWidth);
  const position = (physical, animate = false) => {
    targetLeft = physical * track.clientWidth;
    track.scrollTo({ left: targetLeft, behavior: animate && !reducedMotion.matches ? 'smooth' : 'auto' });
  };
  const normalize = () => {
    const physical = physicalIndex();
    if (physical === 0) position(cards.length);
    else if (physical === cards.length + 1) position(1);
  };
  const settle = () => {
    if (!looping) return;
    if (targetLeft !== null && Math.abs(track.scrollLeft - targetLeft) > 1) return;
    const manual = targetLeft === null;
    targetLeft = null;
    index = wrap(physicalIndex() - 1);
    normalize();
    update();
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
    if (track.contains(event.target)) { targetLeft = null; pointerOrigin = { x: event.clientX, y: event.clientY }; dragged = false; }
  });
  track.addEventListener('pointermove', (event) => {
    if (pointerOrigin && Math.hypot(event.clientX - pointerOrigin.x, event.clientY - pointerOrigin.y) > 10) dragged = true;
  }, { passive: true });
  track.addEventListener('click', (event) => {
    if (dragged && event.detail !== 0) { event.preventDefault(); dragged = false; }
  });
  const release = () => { pointerOrigin = null; schedule(); };
  document.addEventListener('pointerup', release);
  document.addEventListener('pointercancel', release);
  track.addEventListener('touchstart', () => { targetLeft = null; touching = true; stop(); }, { passive: true });
  const endTouch = () => { touching = false; schedule(); };
  document.addEventListener('touchend', endTouch, { passive: true });
  document.addEventListener('touchcancel', endTouch, { passive: true });
  track.addEventListener('focusin', stop);
  track.addEventListener('focusout', () => setTimeout(schedule, 0));
  toggle?.addEventListener('click', schedule);
  nav?.addEventListener('click', schedule);
  document.addEventListener('click', schedule);
  document.addEventListener('keydown', (event) => { if (event.key === 'Escape') schedule(); });
  document.addEventListener('visibilitychange', schedule);
  window.addEventListener('blur', () => { foreground = false; stop(); });
  window.addEventListener('focus', () => { foreground = true; schedule(); });
  window.addEventListener('resize', layout);
  reducedMotion.addEventListener('change', () => { paused = reducedMotion.matches; update(); schedule(); });
  layout();
}
