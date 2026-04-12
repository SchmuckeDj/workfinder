/**
 * WorkFinder — main.js v5
 * Carrusel vertical sidebar, carrusel horizontal afiliados (drag + flechas),
 * filtros, stagger de cards, navbar shadow.
 */
document.addEventListener('DOMContentLoaded', () => {

  /* ── Flash messages auto-dismiss ── */
  document.querySelectorAll('.alert').forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity .4s, transform .4s';
      el.style.opacity = '0';
      el.style.transform = 'translateX(12px)';
      setTimeout(() => el.remove(), 400);
    }, 5000);
  });

  /* ── Stagger job cards ── */
  const jobCards = document.querySelectorAll('.job-card.card-hidden');
  if ('IntersectionObserver' in window && jobCards.length) {
    const io = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (!e.isIntersecting) return;
        setTimeout(() => e.target.classList.replace('card-hidden', 'card-visible'),
          parseInt(e.target.dataset.index || 0) * 70);
        io.unobserve(e.target);
      });
    }, { threshold: 0.08 });
    jobCards.forEach((c, i) => { c.dataset.index = i; io.observe(c); });
  } else {
    jobCards.forEach(c => c.classList.replace('card-hidden', 'card-visible'));
  }

  /* ── Filtros de modalidad ── */
  const pills = document.querySelectorAll('.filter-pill');
  const grid  = document.getElementById('jobs-grid');
  if (pills.length && grid) {
    pills.forEach(pill => pill.addEventListener('click', () => {
      const f = pill.dataset.filter;
      pills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      let n = 0;
      grid.querySelectorAll('.job-card').forEach(card => {
        const show = f === 'all' || card.dataset.modality === f;
        if (show) {
          card.style.display = 'flex';
          requestAnimationFrame(() => { card.style.opacity = '1'; card.style.transform = ''; });
          n++;
        } else {
          card.style.opacity = '0'; card.style.transform = 'translateY(8px)';
          setTimeout(() => { card.style.display = 'none'; }, 200);
        }
      });
      const counter = document.querySelector('.filter-count');
      if (counter) counter.textContent = `${n} resultado${n !== 1 ? 's' : ''}`;
    }));
  }

  /* ────────────────────────────────────────
     CARRUSEL VERTICAL — sidebar izquierdo
  ──────────────────────────────────────── */
  const vCarousel  = document.getElementById('vcarousel');
  const vTrack     = document.getElementById('vcarousel-track');
  const vBtnUp     = document.getElementById('vcarousel-up');
  const vBtnDown   = document.getElementById('vcarousel-down');
  const vIndicator = document.getElementById('vcarousel-indicator');

  if (vCarousel && vTrack && vBtnUp && vBtnDown) {
    const vCards = Array.from(vTrack.querySelectorAll('.vcard'));
    const vTotal = vCards.length;
    let vIdx = 0, vTimer = null;

    const vH = () => vCarousel.getBoundingClientRect().height || 260;

    const vGo = idx => {
      vIdx = ((idx % vTotal) + vTotal) % vTotal;
      vTrack.style.transform = `translateY(-${vIdx * vH()}px)`;
      if (vIndicator) vIndicator.textContent = `${vIdx + 1} / ${vTotal}`;
    };

    const vReset = () => { clearInterval(vTimer); vTimer = setInterval(() => vGo(vIdx + 1), 4500); };

    vBtnDown.addEventListener('click', () => { vGo(vIdx + 1); vReset(); });
    vBtnUp.addEventListener('click',   () => { vGo(vIdx - 1); vReset(); });
    vGo(0); vReset();

    window.addEventListener('resize', () => {
      vTrack.style.transition = 'none';
      vTrack.style.transform  = `translateY(-${vIdx * vH()}px)`;
      requestAnimationFrame(() => { vTrack.style.transition = ''; });
    }, { passive: true });
  }

  /* ────────────────────────────────────────
     CARRUSEL HORIZONTAL — afiliados
     Soporta: flechas, dots, touch swipe y drag con mouse.
     FIX clave: calcular offset DESPUÉS del primer paint
     usando requestAnimationFrame para que getBoundingClientRect
     devuelva el ancho real y no 0.
  ──────────────────────────────────────── */
  const hTrack  = document.getElementById('hcarousel-track');
  const hPrev   = document.getElementById('hcarousel-prev');
  const hNext   = document.getElementById('hcarousel-next');
  const hDotsEl = document.getElementById('hcarousel-dots');

  if (hTrack && hPrev && hNext) {
    const hCards = Array.from(hTrack.querySelectorAll('.acard'));
    const hTotal = hCards.length;
    let hIdx = 0;

    /* Calcula cuántos px hay que desplazar por "página" */
    const hStep = () => {
      const first = hCards[0];
      if (!first) return 260;
      const gap = parseFloat(getComputedStyle(hTrack).gap) || 20;
      return Math.round(first.getBoundingClientRect().width + gap);
    };

    /* Cuántas cards caben en el viewport del wrapper */
    const hVisible = () => {
      const wrapper = hTrack.parentElement;
      const ww = wrapper ? wrapper.getBoundingClientRect().width : window.innerWidth;
      const step = hStep();
      return Math.max(1, Math.floor(ww / step));
    };

    const hMax = () => Math.max(0, hTotal - hVisible());

    /* Mueve el track */
    const hApply = (idx, instant = false) => {
      if (instant) hTrack.style.transition = 'none';
      hTrack.style.transform = `translateX(-${idx * hStep()}px)`;
      if (instant) requestAnimationFrame(() => { hTrack.style.transition = ''; });
      hPrev.disabled = idx <= 0;
      hNext.disabled = idx >= hMax();
      hDotsEl && hDotsEl.querySelectorAll('.hcarousel-dot').forEach((d, i) => {
        d.classList.toggle('active', i === idx);
      });
    };

    const hGo = idx => {
      hIdx = Math.max(0, Math.min(idx, hMax()));
      hApply(hIdx);
    };

    /* Dots */
    const buildDots = () => {
      if (!hDotsEl) return;
      hDotsEl.innerHTML = '';
      const pages = hMax() + 1;
      for (let i = 0; i < pages; i++) {
        const btn = document.createElement('button');
        btn.className = 'hcarousel-dot' + (i === hIdx ? ' active' : '');
        btn.addEventListener('click', () => hGo(i));
        hDotsEl.appendChild(btn);
      }
    };

    hNext.addEventListener('click', () => hGo(hIdx + 1));
    hPrev.addEventListener('click', () => hGo(hIdx - 1));

    /* ── Touch swipe ── */
    let tStartX = 0;
    hTrack.addEventListener('touchstart', e => { tStartX = e.touches[0].clientX; }, { passive: true });
    hTrack.addEventListener('touchend', e => {
      const diff = tStartX - e.changedTouches[0].clientX;
      if (diff >  40) hGo(hIdx + 1);
      if (diff < -40) hGo(hIdx - 1);
    });

    /* ── Mouse drag ── */
    let mDown = false, mStartX = 0, mScrollX = 0;

    hTrack.addEventListener('mousedown', e => {
      mDown   = true;
      mStartX = e.pageX;
      mScrollX = hIdx * hStep();
      hTrack.classList.add('dragging');
    });

    document.addEventListener('mousemove', e => {
      if (!mDown) return;
      const dx = e.pageX - mStartX;
      /* Mueve en tiempo real sin transition */
      hTrack.style.transition = 'none';
      hTrack.style.transform  = `translateX(-${mScrollX - dx}px)`;
    });

    document.addEventListener('mouseup', e => {
      if (!mDown) return;
      mDown = false;
      hTrack.classList.remove('dragging');
      hTrack.style.transition = '';
      const dx = e.pageX - mStartX;
      if (dx < -40) hGo(hIdx + 1);
      else if (dx > 40) hGo(hIdx - 1);
      else hApply(hIdx); /* snap de vuelta si no llegó al umbral */
    });

    /* Init — esperar que el browser pinte para medir anchos reales */
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {       /* doble rAF asegura layout completo */
        buildDots();
        hApply(0, true);
      });
    });

    window.addEventListener('resize', () => {
      buildDots();
      hGo(Math.min(hIdx, hMax()));
    }, { passive: true });
  }

  /* ── Navbar shadow on scroll ── */
  const navbar = document.querySelector('.navbar');
  if (navbar) {
    window.addEventListener('scroll', () => {
      navbar.style.boxShadow = window.scrollY > 20 ? '0 2px 16px rgba(0,0,0,0.08)' : '';
    }, { passive: true });
  }

});
