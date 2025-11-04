(function () {
  function arrivalAtLeast3Days(arrivalValue) {
  if (!arrivalValue) return false;
  const arrival = new Date(arrivalValue);
  const today = new Date();
  today.setHours(0,0,0,0);
  const min = new Date(today);
  min.setDate(min.getDate() + 3);
  return arrival >= min;
}
  let prevScroll = window.pageYOffset || 0;
  window.addEventListener('scroll', () => {
    const cur = window.pageYOffset || 0;
    const hat = document.getElementById('hat');
    if (!hat) { prevScroll = cur; return; }
    hat.style.top = (prevScroll > cur) ? '0' : '-80px';
    prevScroll = cur;
  });

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

  document.addEventListener('DOMContentLoaded', () => {
    createSlider({ wrapperId: 'slides-main', prevId: 'prev', nextId: 'next', gap: 120 });
    createSlider({ wrapperId: 'slides-room', prevId: 'prev-room', nextId: 'next-room', gap: 120 });
    createSlider({ wrapperId: 'slides-feedbacks', prevId: 'prev-feedbacks', nextId: 'next-feedbacks', gap: 180 });

    const hat = document.getElementById('hat');

    const overlay = document.getElementById('overlay');
    const overlay2 = document.getElementById('overlay-2'); 
    const bookingBox = document.getElementById('myForm');   
    const bookingForm = document.getElementById('myFormIn'); 
    const reviewModal = document.getElementById('review-1') || document.getElementById('review'); 
    const reviewForm = document.getElementById('my-review-1') || document.getElementById('my-review'); 
    const reviewBtn = document.getElementById('review-button');

    function showElement(el) { if (el) el.style.display = 'block'; }
    function hideElement(el) { if (el) el.style.display = 'none'; }

    window.openForm = function () {
      showElement(bookingBox);
      showElement(overlay);
      if (hat) hat.style.display = 'none';
      if (bookingForm) bookingForm.reset();
    };

    window.closeForm = function () {
      hideElement(bookingBox);
      hideElement(overlay);
      if (hat) hat.style.display = 'flex';
      if (bookingForm) bookingForm.reset();
    };

    (function setupReview() {
      const reviewOverlay = overlay2 || overlay;
      if (!reviewBtn || !reviewModal) return;

      const show = (el) => { if (el) el.style.display = 'block'; };
      const hide = (el) => { if (el) el.style.display = 'none'; };

      function openReview() {
        show(reviewModal);
        if (reviewOverlay) show(reviewOverlay);
        if (hat) hat.style.display = 'none';
        document.body.style.overflow = 'hidden';
        if (reviewForm) reviewForm.reset();
        const first = reviewModal.querySelector('input, textarea, button, select');
        if (first) first.focus();
      }

      function closeReview() {
        hide(reviewModal);
        if (reviewOverlay) hide(reviewOverlay);
        if (hat) hat.style.display = 'flex';
        document.body.style.overflow = '';
        if (reviewForm) reviewForm.reset();
      }

      reviewBtn.addEventListener('click', (e) => {
        e.preventDefault();
        openReview();
      });

      reviewModal.querySelectorAll('.cancel').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          closeReview();
        });
      });

      if (reviewOverlay) {
        reviewOverlay.addEventListener('click', closeReview);
      }

      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && getComputedStyle(reviewModal).display !== 'none') {
          closeReview();
        }
      });


      if (reviewForm) {
        reviewForm.addEventListener('submit', (e) => {

        });
      }

      if (getComputedStyle(reviewModal).display === 'block') reviewModal.style.display = 'none';
      if (reviewOverlay && getComputedStyle(reviewOverlay).display === 'block') reviewOverlay.style.display = 'none';
    })();

    if (overlay) {
      overlay.addEventListener('click', () => {
        closeForm();

      });
    }
    if (overlay2) {
      overlay2.addEventListener('click', () => {

      });
    }

    if (bookingForm) {
      bookingForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (!bookingForm.checkValidity()) {
          bookingForm.reportValidity();
          return;
        }

        const raw = Object.fromEntries(new FormData(bookingForm).entries());
        if (raw.room_number !== undefined) raw.room_number = parseInt(raw.room_number, 10);
        if (!raw.date_arrival || !raw.date_departure) {
          alert('Введите даты заезда и выезда.');
          return;
        }

        if (raw.date_departure < raw.date_arrival) {
          alert('Дата выезда должна быть не раньше даты заезда.');
          return;
        }
        if (raw.name.length < 3 || raw.name.length > 20) {
          alert("Имя должно иметь от 3-ёх до 20 символов");
          return;
        }
        if(!arrivalAtLeast3Days(raw.date_arrival)){
          alert("Дата заезда должна быть минимум через 3 дня от нынешней даты")
          return;
        }
        if (raw.phone_number.length < 7 || raw.name.length >= 17) {
          alert("Номер телефона может быть длинной от 7 до 16 символов");
          return;
        }

        try {
          const res = await fetch('/add-booking', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(raw),
            credentials: 'same-origin'
          });

          const text = await res.text();
          console.log('Booking response:', res.status, text);

          if (res.status === 422) {
            try {
              const payload = JSON.parse(text);
              alert('Ошибка валидации: ' + JSON.stringify(payload.detail || payload));
            } catch {
              alert('Ошибка валидации: ' + text);
            }
            return;
          }

          if (!res.ok) {
            let msg = `Ошибка сервера: ${res.status}`;
            try {
              const j = JSON.parse(text);
              msg = j.detail || JSON.stringify(j);
            } catch {}
            alert(msg);
            return;
          }

          alert('Заявка принята');
          bookingForm.reset();
          hideElement(bookingBox);
          hideElement(overlay);
          if (hat) hat.style.display = 'flex';
        } catch (err) {
          console.error(err);
          alert('Сетевая ошибка: ' + (err && err.message ? err.message : 'unknown'));
        }
      });
    }


    if (overlay && getComputedStyle(overlay).display === 'block') overlay.style.display = 'none';
    if (overlay2 && getComputedStyle(overlay2).display === 'block') overlay2.style.display = 'none';
    if (bookingBox && getComputedStyle(bookingBox).display === 'block') bookingBox.style.display = 'none';
    (function setupAdminToggle() {
  const wrapper = document.getElementById('admin-button'); 
  const btn = wrapper ? wrapper.querySelector('button') : null;
  const panel = document.getElementById('admin-btn-container'); 

  if (!btn || !panel) return; 

  if (getComputedStyle(panel).display !== 'block') panel.style.display = 'none';

  btn.addEventListener('click', (e) => {
    e.preventDefault();
    const isHidden = getComputedStyle(panel).display === 'none';
    panel.style.display = isHidden ? 'block' : 'none';
    if (isHidden) {
      panel.scrollIntoView({ behavior: 'smooth', block: 'center' });
      const first = panel.querySelector('input, button, textarea, select');
      if (first) first.focus();
    }
  });
})();

  }); 
})(); 
document.addEventListener('DOMContentLoaded', function () {
  const wrapper = document.getElementById('admin-button');
  const btn = wrapper ? wrapper.querySelector('button') : null;
  const panel = document.getElementById('admin-btn-container');

  if (!btn || !panel) return;

  btn.addEventListener('click', function () {
    panel.classList.toggle('visible');

    if (panel.classList.contains('visible')) {
      panel.scrollIntoView({ behavior: 'smooth', block: 'center' });
      const firstInput = panel.querySelector('input, button, textarea, select');
      if (firstInput) firstInput.focus();
    }
  });
});
