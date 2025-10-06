(function () {
  // Хедер при скролле
  let prevScroll = window.pageYOffset || 0;
  window.addEventListener('scroll', () => {
    const cur = window.pageYOffset || 0;
    const hat = document.getElementById('hat');
    if (!hat) { prevScroll = cur; return; }
    hat.style.top = (prevScroll > cur) ? '0' : '-80px';
    prevScroll = cur;
  });

  // Универсальный слайдер-конструктор
  function createSlider(options) {
    const wrapper = document.getElementById(options.wrapperId);
    if (!wrapper) return;
    const slides = Array.from(wrapper.querySelectorAll('.slide'));
    if (!slides.length) return;

    const prevBtn = document.getElementById(options.prevId);
    const nextBtn = document.getElementById(options.nextId);
    let idx = 0;
    const gap = typeof options.gap === 'number' ? options.gap : 120;

    function update() {
      const w = slides[0].getBoundingClientRect().width;
      const offset = (w + gap) * idx;
      wrapper.style.transform = `translateX(-${offset}px)`;
      wrapper.style.transition = 'transform 500ms ease';
    }

    if (nextBtn) nextBtn.addEventListener('click', () => {
      idx = (idx + 1) % slides.length;
      update();
    });

    if (prevBtn) prevBtn.addEventListener('click', () => {
      idx = (idx - 1 + slides.length) % slides.length;
      update();
    });

    window.addEventListener('resize', update);
    update();
  }

  // Создаём три слайдера (аналогично вашему коду)
  document.addEventListener('DOMContentLoaded', () => {
    createSlider({ wrapperId: 'slides-main', prevId: 'prev', nextId: 'next', gap: 120 });
    createSlider({ wrapperId: 'slides-room', prevId: 'prev-room', nextId: 'next-room', gap: 120 });
    createSlider({ wrapperId: 'slides-feedbacks', prevId: 'prev-feedbacks', nextId: 'next-feedbacks', gap: 180 });

    // Открытие/закрытие формы
    const overlay = document.getElementById('overlay');
    const formBox = document.getElementById('myForm');
    const form = document.querySelector('form'); // ожидается одна основная форма; если несколько — используйте id в HTML
    const hat = document.getElementById('hat')

    window.openForm = function () {
      if (formBox) formBox.style.display = 'block';
      if (overlay) overlay.style.display = 'block';
      if (hat) hat.style.display = 'none';
      document.getElementById('myFormIn').reset();
    };

    window.closeForm = function () {
      if (formBox) formBox.style.display = 'none';
      if (overlay) overlay.style.display = 'none';
      if (hat) hat.style.display = 'flex';
      document.getElementById('myFormIn').reset();
    };
    // Обработка сабмита (если форма есть)
    overlay?.addEventListener('click', closeForm);
form.addEventListener('submit', async (e) => {
  e.preventDefault();

  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }

  const fd = new FormData(form);
  // FormData автоматически содержит выбранный radio (по name="options")
  const data = Object.fromEntries(fd.entries());
  // Если нужно, преобразовать пустые строки в null или прочее — добавьте здесь

  try {
    const res = await fetch('/add-booking', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(res.status);
    // очистить/закрыть
    form.reset();
    if (formBox) formBox.style.display = 'none';
    if (overlay) overlay.style.display = 'none';
    const json = await res.json().catch(() => null);
    console.log('Server response', json);
  } catch (err) {
    console.error('Send error', err);
  }

});
  const openBtn = document.getElementById('review-button');
  const overlay_2 = document.getElementById('overlay-2');
  const modal = document.getElementById('review');
  const form_2 = document.getElementById('my-review');
  const closeBtns = modal ? modal.querySelectorAll('.cancel') : [];


  function showModal(){
    if (overlay_2) overlay.style.display = 'block';
    if (modal) modal.style.display = 'block';
    if (hat) hat.style.display = 'none';
  }
  function hideModal(){
    if (overlay_2) overlay.style.display = 'none';
    if (modal) modal.style.display = 'none';
    if (hat) hat.style.display = 'flex';
    form?.reset();
  }

  openBtn?.addEventListener('click', (e) => {
    e.preventDefault();
    showModal();
  });

  overlay?.addEventListener('click', hideModal);
  closeBtns.forEach(btn => btn.addEventListener('click', hideModal));

  form?.addEventListener('submit', (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(form_2).entries());
    console.log('Form data:', data);
    hideModal();
  });

  // Ensure hidden by default
  if (overlay && getComputedStyle(overlay).display === 'block') overlay.style.display = 'none';
  if (modal && getComputedStyle(modal).display === 'block') modal.style.display = 'none';
  });
})();
