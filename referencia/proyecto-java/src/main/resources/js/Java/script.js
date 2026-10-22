const obs = new IntersectionObserver((entries) => {
    entries.forEach((e, i) => {
        if (e.isIntersecting) {
            setTimeout(() =>  e.target.classList.add('visible'), i * 80);
            obs.unobserve(e.target);

        }
    });
}, { threshold: 0.1 });
document.querySelectorAll('.fade-in').forEach((e) => obs.observe(e));


window.addEventListener('scroll', () => {
 document.querySelector('nav').style.borderBottomColor =
   window.scrollY > 50 ? 'rgba(255, 255, 255, 0.2)' : 'var(--border)';

});

