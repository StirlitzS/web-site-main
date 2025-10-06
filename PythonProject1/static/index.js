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

    window.openForm = function () {
      if (formBox) formBox.style.display = 'block';
      if (overlay) overlay.style.display = 'block';
      document.getElementById('myFormIn').reset();
    };

    window.closeForm = function () {
      if (formBox) formBox.style.display = 'none';
      if (overlay) overlay.style.display = 'none';
      document.getElementById('myFormIn').reset();
    };

    // Обработка сабмита (если форма есть)

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
  });
})();
