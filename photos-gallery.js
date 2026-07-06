const d = document, lb = d.getElementById('lightbox');
const lbJpg = d.getElementById('lb-jpg');
const items = [...d.querySelectorAll('main.gallery a.thumb')];
let i = -1;

function openAt(idx){
  i = (idx + items.length) % items.length;
  const a = items[i];
  lbJpg.src = a.getAttribute('href');
  lb.showModal();
}
items.forEach((a, idx) => a.addEventListener('click', e => { e.preventDefault(); openAt(idx); }));
lb.addEventListener('click', e => { if (e.target === lb) lb.close(); });
addEventListener('keydown', e => {
  if (!lb.open) return;
  if (e.key === 'Escape') lb.close();
  if (e.key === 'ArrowRight') openAt(i+1);
  if (e.key === 'ArrowLeft') openAt(i-1);
});
