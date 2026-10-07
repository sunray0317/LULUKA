(() => {
  const grid = document.querySelector('.project-grid');
  const dialog = document.querySelector('.project-lightbox');
  if (!grid || !dialog) return;
  const preview = dialog.querySelector('.preview-image');
  const title = dialog.querySelector('#preview-title');
  let opener;
  grid.addEventListener('pointerover', event => {
    if (event.target.closest('.project-view')) grid.classList.add('is-engaged');
  });
  grid.addEventListener('pointerleave', () => grid.classList.remove('is-engaged'));
  grid.addEventListener('pointerdown', event => {
    if (event.target.closest('.project-view')) grid.classList.add('is-engaged');
  });
  grid.addEventListener('click', event => {
    const button = event.target.closest('.project-view');
    if (!button) return;
    opener = button;
    preview.className = 'visual-window preview-image quadrant-' + button.dataset.view;
    preview.replaceChildren(button.querySelector('img').cloneNode());
    title.textContent = button.querySelector('.view-caption').textContent;
    dialog.showModal();
    document.documentElement.classList.add('is-previewing');
  });
  dialog.querySelector('.preview-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const bounds = dialog.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
  });
  dialog.addEventListener('close', () => {
    document.documentElement.classList.remove('is-previewing');
    grid.classList.remove('is-engaged');
    if (opener) opener.focus({preventScroll:true});
  });
})();
