(() => {
  const video = document.querySelector('.project-motion video');
  const button = document.querySelector('.motion-toggle');
  if (!video || !button) return;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let manuallyPaused = false;
  let visible = false;
  const updateButton = () => {
    button.classList.toggle('is-paused', video.paused);
    button.setAttribute('aria-label', video.paused ? '播放動態作品' : '暫停動態作品');
  };
  const synchronize = () => {
    if (!visible || document.hidden || manuallyPaused || reduced.matches) video.pause();
    else video.play().catch(updateButton);
    updateButton();
  };
  video.addEventListener('play', updateButton);
  video.addEventListener('pause', updateButton);
  button.addEventListener('click', () => {
    if (video.paused) {
      manuallyPaused = false;
      video.play().catch(updateButton);
    } else {
      manuallyPaused = true;
      video.pause();
    }
  });
  new IntersectionObserver(entries => {
    visible = entries[0].isIntersecting;
    synchronize();
  }, {threshold: .15}).observe(video);
  document.addEventListener('visibilitychange', synchronize);
  reduced.addEventListener('change', synchronize);
  if (reduced.matches) video.pause();
  updateButton();
})();
