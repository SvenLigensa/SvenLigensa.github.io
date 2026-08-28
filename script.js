// ─── Dark mode ───────────────────────────────────────────────────────────────

const root = document.documentElement;
const themeToggle = document.getElementById('theme-toggle');

const saved = localStorage.getItem('theme');
if (saved === 'light') {
  root.setAttribute('data-theme', 'light');
} else {
  root.setAttribute('data-theme', 'dark');
}

themeToggle.addEventListener('click', () => {
  const isDark = root.getAttribute('data-theme') === 'dark';
  root.setAttribute('data-theme', isDark ? 'light' : 'dark');
  localStorage.setItem('theme', isDark ? 'light' : 'dark');
});

// ─── Modal ───────────────────────────────────────────────────────────────────

function openModal(overlay) {
  overlay.classList.add('is-open');
  overlay.setAttribute('aria-hidden', 'false');
  document.body.style.overflow = 'hidden';
  overlay.querySelector('.modal-close').focus();
}

function closeModal(overlay) {
  overlay.classList.remove('is-open');
  overlay.setAttribute('aria-hidden', 'true');
  document.body.style.overflow = '';
}

document.querySelectorAll('.entry--clickable').forEach(entry => {
  const activate = () => {
    const modal = document.getElementById(entry.dataset.modal);
    if (modal) openModal(modal);
  };
  entry.addEventListener('click', activate);
  entry.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') activate(); });
});

document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.querySelector('.modal-close').addEventListener('click', () => closeModal(overlay));
  overlay.addEventListener('click', e => { if (e.target === overlay) closeModal(overlay); });
});

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.is-open').forEach(closeModal);
  }
});

// ─── Show more ───────────────────────────────────────────────────────────────

document.querySelectorAll('.show-more').forEach(button => {
  const extra = document.getElementById(button.getAttribute('aria-controls'));
  const label = button.querySelector('.show-more-label');
  button.addEventListener('click', () => {
    const expanded = button.getAttribute('aria-expanded') === 'true';
    button.setAttribute('aria-expanded', String(!expanded));
    extra.hidden = expanded;
    label.textContent = expanded ? button.dataset.more : button.dataset.less;
  });
});

// ─── Active nav link on scroll ────────────────────────────────────────────────

const sections = document.querySelectorAll('main section[id]');
const navLinks = document.querySelectorAll('nav > ul a');
const mobileSectionLabel = document.getElementById('mobile-section-label');
const mobileDropdownLinks = document.querySelectorAll('.mobile-nav-dropdown a');

const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const href = `#${entry.target.id}`;
        navLinks.forEach((link) => {
          link.classList.toggle('active', link.getAttribute('href') === href);
        });
        mobileDropdownLinks.forEach((link) => {
          link.classList.toggle('active', link.getAttribute('href') === href);
        });
        const activeLink = [...navLinks].find(link => link.getAttribute('href') === href);
        if (activeLink && mobileSectionLabel) {
          mobileSectionLabel.textContent = activeLink.textContent;
        }
      }
    });
  },
  { rootMargin: '-20% 0px -70% 0px' }
);

sections.forEach((section) => observer.observe(section));

// ─── Mobile nav dropdown ──────────────────────────────────────────────────────

const mobileSectionBtn = document.getElementById('mobile-section-btn');
const mobileNavDropdown = document.getElementById('mobile-nav-dropdown');

function openMobileDropdown() {
  mobileNavDropdown.classList.add('is-open');
  mobileNavDropdown.removeAttribute('aria-hidden');
  mobileSectionBtn.setAttribute('aria-expanded', 'true');
}

function closeMobileDropdown() {
  mobileNavDropdown.classList.remove('is-open');
  mobileNavDropdown.setAttribute('aria-hidden', 'true');
  mobileSectionBtn.setAttribute('aria-expanded', 'false');
}

mobileSectionBtn.addEventListener('click', (e) => {
  e.stopPropagation();
  mobileNavDropdown.classList.contains('is-open') ? closeMobileDropdown() : openMobileDropdown();
});

mobileDropdownLinks.forEach(link => {
  link.addEventListener('click', () => closeMobileDropdown());
});

document.addEventListener('click', (e) => {
  if (!mobileSectionBtn.contains(e.target) && !mobileNavDropdown.contains(e.target)) {
    closeMobileDropdown();
  }
});
