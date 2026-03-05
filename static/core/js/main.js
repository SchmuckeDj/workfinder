/**
 * WorkFinder — main.js
 * Interacciones ligeras sin dependencias externas.
 */

// Auto-dismiss flash messages después de 5 segundos
document.addEventListener('DOMContentLoaded', () => {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      alert.style.opacity = '0';
      alert.style.transform = 'translateX(20px)';
      setTimeout(() => alert.remove(), 400);
    }, 5000);
  });

  // Animación de entrada para las job cards (Intersection Observer)
  const cards = document.querySelectorAll('.job-card');
  if ('IntersectionObserver' in window && cards.length) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry, i) => {
        if (entry.isIntersecting) {
          // Stagger: cada carta aparece 80ms después de la anterior
          setTimeout(() => {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
          }, i * 80);
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });

    cards.forEach(card => {
      card.style.opacity = '0';
      card.style.transform = 'translateY(24px)';
      card.style.transition = 'opacity 0.5s ease, transform 0.5s ease, box-shadow 0.25s ease, border-color 0.25s ease';
      observer.observe(card);
    });
  }
});