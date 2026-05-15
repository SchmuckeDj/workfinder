/**
 * WorkFinder — main.js v8
 * Hamburger, carruseles, filtros, stagger cards, navbar shadow, scrollspy.
 */
document.addEventListener('DOMContentLoaded', () => {

  /* ── Hamburger menu ── */
  const navToggle = document.getElementById('nav-toggle');
  const navDrawer = document.getElementById('nav-drawer');

  if (navToggle && navDrawer) {
    const openMenu = () => {
      navToggle.classList.add('open');
      navToggle.setAttribute('aria-expanded', 'true');
      navDrawer.classList.add('open');
      navDrawer.setAttribute('aria-hidden', 'false');
      document.body.classList.add('nav-open');
    };
    const closeMenu = () => {
      navToggle.classList.remove('open');
      navToggle.setAttribute('aria-expanded', 'false');
      navDrawer.classList.remove('open');
      navDrawer.setAttribute('aria-hidden', 'true');
      document.body.classList.remove('nav-open');
    };
    navToggle.addEventListener('click', () => {
      navToggle.classList.contains('open') ? closeMenu() : openMenu();
    });
    navDrawer.querySelectorAll('a').forEach(a => a.addEventListener('click', closeMenu));
    document.addEventListener('click', e => {
      if (!navToggle.contains(e.target) && !navDrawer.contains(e.target)) closeMenu();
    });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeMenu(); });
    window.addEventListener('resize', () => {
      if (window.innerWidth >= 640) closeMenu();
    }, { passive: true });
  }

  /* ── Flash auto-dismiss ── */
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

  /* ── Carrusel vertical sidebar ── */
  const vCarousel  = document.getElementById('vcarousel');
  const vTrack     = document.getElementById('vcarousel-track');
  const vBtnUp     = document.getElementById('vcarousel-up');
  const vBtnDown   = document.getElementById('vcarousel-down');
  const vIndicator = document.getElementById('vcarousel-indicator');

  if (vCarousel && vTrack && vBtnUp && vBtnDown) {
    const vSlides = Array.from(vTrack.querySelectorAll('.vslide'));
    const vTotal  = vSlides.length;
    let vIdx = 0, vTimer = null;
    const isDesktop = () => window.innerWidth >= 1024;
    const vH = () => vCarousel.getBoundingClientRect().height || 268;

    const vGo = idx => {
      if (!isDesktop()) return;
      vIdx = ((idx % vTotal) + vTotal) % vTotal;
      vTrack.style.transform = `translateY(-${vIdx * vH()}px)`;
      if (vIndicator) vIndicator.textContent = `${vIdx + 1} / ${vTotal}`;
    };
    const vReset = () => {
      clearInterval(vTimer);
      if (isDesktop()) vTimer = setInterval(() => vGo(vIdx + 1), 4500);
    };
    vBtnDown.addEventListener('click', () => { vGo(vIdx + 1); vReset(); });
    vBtnUp.addEventListener('click',   () => { vGo(vIdx - 1); vReset(); });
    window.addEventListener('resize', () => {
      if (!isDesktop()) {
        vTrack.style.transform = '';
        clearInterval(vTimer);
      } else {
        vTrack.style.transition = 'none';
        vTrack.style.transform  = `translateY(-${vIdx * vH()}px)`;
        requestAnimationFrame(() => { vTrack.style.transition = ''; });
        vReset();
      }
    }, { passive: true });
    if (isDesktop()) { vGo(0); vReset(); }
  }

  /* ── Carrusel horizontal afiliados ── */
  const hTrack  = document.getElementById('hcarousel-track');
  const hPrev   = document.getElementById('hcarousel-prev');
  const hNext   = document.getElementById('hcarousel-next');
  const hDotsEl = document.getElementById('hcarousel-dots');

  if (hTrack && hPrev && hNext) {
    const hCards = Array.from(hTrack.querySelectorAll('.acard'));
    const hTotal = hCards.length;
    let hIdx = 0;

    const hStep = () => {
      const first = hCards[0];
      if (!first) return 260;
      return Math.round(first.getBoundingClientRect().width + (parseFloat(getComputedStyle(hTrack).gap) || 20));
    };
    const hVisible = () => {
      const ww = (hTrack.parentElement || document.body).getBoundingClientRect().width;
      return Math.max(1, Math.floor(ww / hStep()));
    };
    const hMax = () => Math.max(0, hTotal - hVisible());

    const hApply = (idx, instant = false) => {
      if (instant) hTrack.style.transition = 'none';
      hTrack.style.transform = `translateX(-${idx * hStep()}px)`;
      if (instant) requestAnimationFrame(() => { hTrack.style.transition = ''; });
      hPrev.disabled = idx <= 0;
      hNext.disabled = idx >= hMax();
      if (hDotsEl) hDotsEl.querySelectorAll('.hcarousel-dot').forEach((d, i) => {
        d.classList.toggle('active', i === idx);
      });
    };
    const hGo = idx => { hIdx = Math.max(0, Math.min(idx, hMax())); hApply(hIdx); };

    const buildDots = () => {
      if (!hDotsEl) return;
      hDotsEl.innerHTML = '';
      for (let i = 0; i <= hMax(); i++) {
        const btn = document.createElement('button');
        btn.className = 'hcarousel-dot' + (i === hIdx ? ' active' : '');
        btn.addEventListener('click', () => hGo(i));
        hDotsEl.appendChild(btn);
      }
    };

    hNext.addEventListener('click', () => hGo(hIdx + 1));
    hPrev.addEventListener('click', () => hGo(hIdx - 1));

    let tX = 0;
    hTrack.addEventListener('touchstart', e => { tX = e.touches[0].clientX; }, { passive: true });
    hTrack.addEventListener('touchend', e => {
      const d = tX - e.changedTouches[0].clientX;
      if (d >  40) hGo(hIdx + 1);
      if (d < -40) hGo(hIdx - 1);
    });

    let mDown = false, mStartX = 0, mScrollX = 0;
    hTrack.addEventListener('mousedown', e => {
      mDown = true; mStartX = e.pageX; mScrollX = hIdx * hStep();
      hTrack.classList.add('dragging');
      e.preventDefault();
    });
    document.addEventListener('mousemove', e => {
      if (!mDown) return;
      hTrack.style.transition = 'none';
      hTrack.style.transform  = `translateX(-${mScrollX - (e.pageX - mStartX)}px)`;
    });
    document.addEventListener('mouseup', e => {
      if (!mDown) return;
      mDown = false; hTrack.classList.remove('dragging'); hTrack.style.transition = '';
      const d = e.pageX - mStartX;
      if (d < -40) hGo(hIdx + 1);
      else if (d > 40) hGo(hIdx - 1);
      else hApply(hIdx);
    });

    requestAnimationFrame(() => requestAnimationFrame(() => {
      buildDots();
      hApply(0, true);
    }));

    window.addEventListener('resize', () => {
      buildDots();
      hGo(Math.min(hIdx, hMax()));
    }, { passive: true });
  }

  /* ── Navbar shadow on scroll ── */
  const navbar = document.querySelector('.navbar');
  if (navbar) {
    window.addEventListener('scroll', () => {
      navbar.style.boxShadow = window.scrollY > 20 ? '0 2px 16px rgba(0,0,0,.08)' : '';
    }, { passive: true });
  }

  /* ────────────────────────────────────────
     Fix #7 — SCROLLSPY: marca el nav-link activo
     según la sección visible en el viewport.
     Mapea href="#anchor" → section id="anchor".
  ──────────────────────────────────────── */
  const spyLinks = document.querySelectorAll('.navbar-links .nav-link[href*="#"], .nav-drawer .nav-link[href*="#"]');
  const sectionMap = new Map(); // section element → array of matching links

  spyLinks.forEach(link => {
    const href = link.getAttribute('href') || '';
    const hashIdx = href.indexOf('#');
    if (hashIdx === -1) return;
    const id = href.slice(hashIdx + 1);
    if (!id) return;
    const sec = document.getElementById(id);
    if (!sec) return;
    if (!sectionMap.has(sec)) sectionMap.set(sec, []);
    sectionMap.get(sec).push(link);
  });

  if (sectionMap.size && 'IntersectionObserver' in window) {
    const spyIO = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        // quitar active de todos los spy-links
        spyLinks.forEach(l => l.classList.remove('active'));
        // agregar active a los que apuntan a esta sección
        const links = sectionMap.get(entry.target) || [];
        links.forEach(l => l.classList.add('active'));
      });
    }, {
      // la sección se considera "activa" cuando entra en el tercio superior
      rootMargin: '-20% 0px -70% 0px',
      threshold: 0
    });

    sectionMap.forEach((_, sec) => spyIO.observe(sec));
  }

});
