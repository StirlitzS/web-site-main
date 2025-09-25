document.addEventListener('DOMContentLoaded', () => {
  const slidesWrapper = document.getElementById('slides');
  const slides = Array.from(slidesWrapper.querySelectorAll('.slide'));
  const prevBtn = document.getElementById('prev');
  const nextBtn = document.getElementById('next');

  let currentIndex = 0;
  const visibleWidth = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--slider-width')) || 900;
  const gap = 24; // должен совпадать с gap в CSS для #slides

  function update() {
    const slideWidth = slides[0].getBoundingClientRect().width;
    const offset = (slideWidth + 120) * currentIndex;
    slidesWrapper.style.transform = `translateX(-${offset}px)`;
  }

  nextBtn.addEventListener('click', () => {
    currentIndex = Math.min((currentIndex + 1)%3, slides.length - 1);
    update();
  });

  prevBtn.addEventListener('click', () => {
    currentIndex = (currentIndex - 1) % 3;
    update();
  });


  // Подстройка при ресайзе
  window.addEventListener('resize', update);

  update();

});