/* ============================================
   Sailing Oroboro — Main JavaScript
   ============================================ */

// ─── Sticky Nav ──────────────────────────────
(function () {
  const nav = document.querySelector('.nav');
  if (!nav) return;

  const onScroll = () => {
    if (window.scrollY > 50) nav.classList.add('scrolled');
    else nav.classList.remove('scrolled');
  };

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
})();

// ─── Mobile Menu ─────────────────────────────
(function () {
  const toggle = document.querySelector('.nav-toggle');
  const links  = document.querySelector('.nav-links');
  if (!toggle || !links) return;

  toggle.addEventListener('click', () => {
    const open = links.classList.toggle('open');
    toggle.setAttribute('aria-expanded', open);
    document.body.style.overflow = open ? 'hidden' : '';
  });

  // Close on link click
  links.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => {
      links.classList.remove('open');
      toggle.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    });
  });
})();

// ─── Active Nav Link ──────────────────────────
(function () {
  const path = window.location.pathname;
  document.querySelectorAll('.nav-links a').forEach(a => {
    const href = a.getAttribute('href');
    if (!href) return;
    const aPath = new URL(href, window.location.href).pathname;
    if (path === aPath || (aPath !== '/' && path.startsWith(aPath))) {
      a.classList.add('active');
    }
  });
})();

// ─── Blog Filters ─────────────────────────────
(function () {
  const filterBtns = document.querySelectorAll('.filter-btn');
  const cards      = document.querySelectorAll('.post-card');
  if (!filterBtns.length) return;

  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const region = btn.dataset.filter;

      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      cards.forEach(card => {
        if (region === 'all' || card.dataset.region === region) {
          card.hidden = false;
        } else {
          card.hidden = true;
        }
      });
    });
  });
})();

// ─── Language Selector ───────────────────────
(function () {
  const sel = document.querySelector('.lang-selector');
  if (!sel) return;

  const LANGS = [
    { code: 'en', label: '🇺🇸', mobile: '🇺🇸 English',    prefix: '' },
    { code: 'it', label: '🇮🇹', mobile: '🇮🇹 Italiano',   prefix: '/it' },
    { code: 'ja', label: '🇯🇵', mobile: '🇯🇵 日本語',      prefix: '/ja' },
    { code: 'fr', label: '🇫🇷', mobile: '🇫🇷 Français',   prefix: '/fr' },
    { code: 'pt', label: '🇧🇷', mobile: '🇧🇷 Português',  prefix: '/pt' },
    { code: 'es', label: '🇪🇸', mobile: '🇪🇸 Español',    prefix: '/es' },
    { code: 'ca', label: null,  mobile: 'CA · Català',     prefix: '/ca' },
  ];

  const pathname = window.location.pathname;
  const langMatch = pathname.match(/^\/(it|ja|fr|pt|es|ca)(\/|$)/);
  const currentLang = langMatch ? langMatch[1] : 'en';
  const basePath = langMatch ? pathname.slice(langMatch[1].length + 1) || '/' : pathname;

  function getTarget(lang) {
    if (lang.code === 'en') return basePath === '/' ? '/' : basePath;
    if (basePath === '/' || basePath === '/index.html') return lang.prefix + '/blog.html';
    if (basePath.startsWith('/posts/')) {
      const hreflang = document.querySelector(`link[hreflang="${lang.code}"]`);
      return hreflang ? new URL(hreflang.getAttribute('href')).pathname : lang.prefix + '/blog.html';
    }
    return lang.prefix + basePath;
  }

  // ── Desktop: flag buttons ──
  LANGS.forEach(lang => {
    if (lang.code === currentLang) {
      const span = document.createElement('span');
      span.className = 'lang-option lang-current';
      if (lang.code === 'ca') span.innerHTML = '<span class="flag-ca"></span>';
      else span.textContent = lang.label;
      sel.appendChild(span);
    } else {
      const a = document.createElement('a');
      a.href = getTarget(lang);
      a.className = 'lang-option';
      a.setAttribute('hreflang', lang.code);
      if (lang.code === 'ca') a.innerHTML = '<span class="flag-ca"></span>';
      else a.textContent = lang.label;
      sel.appendChild(a);
    }
  });

  // ── Mobile: compact select dropdown (injected before burger) ──
  const toggle = document.querySelector('.nav-toggle');
  if (toggle) {
    const msel = document.createElement('select');
    msel.className = 'lang-select-mobile';
    LANGS.forEach(lang => {
      const opt = document.createElement('option');
      opt.value = lang.code;
      opt.textContent = lang.mobile;
      if (lang.code === currentLang) opt.selected = true;
      msel.appendChild(opt);
    });
    msel.addEventListener('change', function () {
      const lang = LANGS.find(l => l.code === this.value);
      if (lang && lang.code !== currentLang) window.location.href = getTarget(lang);
    });
    toggle.parentNode.insertBefore(msel, toggle);
  }
})();

// ─── Hero Language Select (mobile homepage) ──
(function () {
  const sel = document.getElementById('hero-lang-sel');
  if (!sel) return;
  const prefixes = { en: '', it: '/it', ja: '/ja', fr: '/fr', pt: '/pt', es: '/es', ca: '/ca' };
  sel.addEventListener('change', function () {
    window.location.href = (prefixes[this.value] || '') + '/';
  });
})();

// ─── Scroll Reveal ───────────────────────────
(function () {
  if (!window.IntersectionObserver) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

  const style = document.createElement('style');
  style.textContent = `
    .reveal { opacity: 0; transform: translateY(24px); transition: opacity 0.6s ease, transform 0.6s ease; }
    .reveal.visible { opacity: 1; transform: none; }
    .reveal-delay-1 { transition-delay: 0.1s; }
    .reveal-delay-2 { transition-delay: 0.2s; }
    .reveal-delay-3 { transition-delay: 0.3s; }
  `;
  document.head.appendChild(style);

  document.querySelectorAll('.post-card, .stat-item, .about-detail').forEach((el, i) => {
    el.classList.add('reveal', `reveal-delay-${(i % 3) + 1}`);
    observer.observe(el);
  });
})();
