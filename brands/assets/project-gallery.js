(() => {
  const grid = document.querySelector('.project-grid');
  const viewer = document.querySelector('.artwork-viewer');
  if (!grid || !viewer) return;
  let opener;
  grid.addEventListener('click', event => {
    const button = event.target.closest('.artwork-button');
    if (!button) return;
    opener = button;
    viewer.querySelector('.viewer-content').replaceChildren(button.querySelector('figure').cloneNode(true));
    viewer.showModal();
    document.documentElement.classList.add('is-viewing');
  });
  viewer.querySelector('.viewer-close').addEventListener('click', () => viewer.close());
  viewer.addEventListener('click', event => {
    if (event.target !== viewer) return;
    const r = viewer.getBoundingClientRect();
    if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) viewer.close();
  });
  viewer.addEventListener('close', () => {
    document.documentElement.classList.remove('is-viewing');
    if (opener) opener.focus({preventScroll:true});
  });
})();
