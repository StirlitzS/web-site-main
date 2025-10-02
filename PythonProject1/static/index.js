var prevScrollpos = window.pageYOffset;
window.onscroll = function() {
  var currentScrollPos = window.pageYOffset;
  if (prevScrollpos > currentScrollPos) {
    document.getElementById("hat").style.top = "0";
  } else {
    document.getElementById("hat").style.top = "-80px";
  }
  prevScrollpos = currentScrollPos;
}
document.addEventListener('DOMContentLoaded', () => {
  const slidesWrapper = document.getElementById('slides-main');
  const slides = Array.from(slidesWrapper.querySelectorAll('.slide'));
  const prevBtn = document.getElementById('prev');
  const nextBtn = document.getElementById('next');

  let currentIndex = 0;


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
    if(currentIndex - 1 < 0) {
      currentIndex = 2;
    } else {
      currentIndex = currentIndex - 1
    }
    update();
  });


  // Подстройка при ресайзе
  window.addEventListener('resize', update);

  update();

});
document.addEventListener('DOMContentLoaded', () => {
  const slidesWrapper = document.getElementById('slides-room');
  const slides = Array.from(slidesWrapper.querySelectorAll('.slide'));
  const prevBtn = document.getElementById('prev-room');
  const nextBtn = document.getElementById('next-room');

  let currentIndex = 0;


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
    if(currentIndex - 1 < 0) {
      currentIndex = 2;
    } else {
      currentIndex = currentIndex - 1
    }
    update();
  });


  window.addEventListener('resize', update);

  update();

});