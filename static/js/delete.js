document.addEventListener('click', async (e) => {
  const btn = e.target.closest('.delete-btn');
  if (!btn) return;
  if (!confirm('حذف شود؟')) return;

  const type = btn.dataset.type; // "room" یا "lyric"
  const id = btn.dataset.id;
  const url = type === 'room' ? `/rooms/${id}/delete` : `/lyrics/${id}/delete`;

  try {
    const res = await fetch(url, { method: 'POST', headers: { 'X-Requested-With': 'fetch' } });
    if (!res.ok) throw new Error('delete failed');

    const el = document.getElementById(`${type}-${id}`) || btn.closest('li, .item, .row');
    if (el) el.remove();
  } catch (err) {
    alert('خطا در حذف');
    console.error(err);
  }
});
