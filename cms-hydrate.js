/**
 * Sales Lead Machine: Dynamic Content Hydration Bridge
 * Automatically synchronizes frontend HTML with PostgreSQL database changes
 */
(function () {
  'use strict';

  // HTML Sanitization utility to eliminate XSS
  function safeCmsUrl(raw, kind = 'href') {
    if (typeof raw !== 'string') return null;
    const value = raw.trim();
    if (!value || /[\u0000-\u001f\u007f]/.test(value) || value.startsWith('//')) return null;
    if (kind === 'src' && /^data:image\/(png|jpeg|gif|webp);base64,[a-z0-9+/=]+$/i.test(value)) return value;
    try {
      const parsed = new URL(value, window.location.origin);
      if (kind === 'href' && ['http:', 'https:', 'mailto:', 'tel:'].includes(parsed.protocol)) return value;
      if (kind === 'src' && ['http:', 'https:'].includes(parsed.protocol)) return value;
      if (value.startsWith('#') || (!/^[a-z][a-z0-9+.-]*:/i.test(value) && !value.startsWith('//'))) return value;
    } catch (_) {
      if (value.startsWith('#') || (!/^[a-z][a-z0-9+.-]*:/i.test(value) && !value.startsWith('//'))) return value;
    }
    return null;
  }

function sanitizeHtml(dirty) {
    if (typeof dirty !== 'string' || !dirty) return '';

    // Rebuild markup from an explicit allowlist. Parsing occurs in an inert
    // document and no untrusted element/attribute is copied by default.
    const parsed = new DOMParser().parseFromString(dirty, 'text/html');
    const allowedTags = new Set([
      'A', 'B', 'STRONG', 'I', 'EM', 'U', 'S', 'DEL', 'P', 'BR', 'SPAN',
      'DIV', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'UL', 'OL', 'LI',
      'BLOCKQUOTE', 'PRE', 'CODE', 'TABLE', 'THEAD', 'TBODY', 'TR',
      'TH', 'TD', 'IMG', 'FIGURE', 'FIGCAPTION', 'HR', 'SUB', 'SUP'
    ]);
    const safeUrl = (raw, kind) => {
      const value = String(raw || '').trim();
      if (!value || /[\u0000-\u001f\u007f]/.test(value)) return null;
      if (kind === 'src' && /^data:image\/(png|jpeg|gif|webp);base64,[a-z0-9+/=]+$/i.test(value)) return value;
      try {
        const url = new URL(value, document.baseURI);
        if (kind === 'href' && ['http:', 'https:', 'mailto:', 'tel:'].includes(url.protocol)) return value;
        if (kind === 'src' && ['http:', 'https:'].includes(url.protocol)) return value;
        if (value.startsWith('#') || (!/^[a-z][a-z0-9+.-]*:/i.test(value) && !value.startsWith('//'))) return value;
      } catch (_) {
        if (value.startsWith('#') || (!/^[a-z][a-z0-9+.-]*:/i.test(value) && !value.startsWith('//'))) return value;
      }
      return null;
    };

    const copySafeNode = (node) => {
      if (node.nodeType === Node.TEXT_NODE) return document.createTextNode(node.nodeValue || '');
      if (node.nodeType !== Node.ELEMENT_NODE) return null;

      const tag = node.tagName.toUpperCase();
      if (!allowedTags.has(tag)) {
        const fragment = document.createDocumentFragment();
        Array.from(node.childNodes).forEach(child => {
          const safeChild = copySafeNode(child);
          if (safeChild) fragment.appendChild(safeChild);
        });
        return fragment;
      }

      const clean = document.createElement(tag.toLowerCase());
      const commonAttrs = ['class', 'title'];
      commonAttrs.forEach(name => {
        if (node.hasAttribute(name)) clean.setAttribute(name, node.getAttribute(name));
      });

      if (tag === 'A') {
        const href = safeUrl(node.getAttribute('href'), 'href');
        if (href) clean.setAttribute('href', href);
        if (node.getAttribute('target') === '_blank') {
          clean.setAttribute('target', '_blank');
          clean.setAttribute('rel', 'noopener noreferrer');
        }
      }
      if (tag === 'IMG') {
        const src = safeUrl(node.getAttribute('src'), 'src');
        if (src) clean.setAttribute('src', src);
        ['alt', 'width', 'height'].forEach(name => {
          if (node.hasAttribute(name) && /^[a-z0-9 _.-]{0,300}$/i.test(node.getAttribute(name))) {
            clean.setAttribute(name, node.getAttribute(name));
          }
        });
        clean.setAttribute('loading', 'lazy');
      }
      if (tag === 'TD' || tag === 'TH') {
        ['colspan', 'rowspan'].forEach(name => {
          const value = node.getAttribute(name);
          if (value && /^[1-9][0-9]{0,2}$/.test(value)) clean.setAttribute(name, value);
        });
      }

      if (!['IMG', 'BR', 'HR'].includes(tag)) {
        Array.from(node.childNodes).forEach(child => {
          const safeChild = copySafeNode(child);
          if (safeChild) clean.appendChild(safeChild);
        });
      }
      return clean;
    };

    const output = document.createElement('div');
    Array.from(parsed.body.childNodes).forEach(node => {
      const safeNode = copySafeNode(node);
      if (safeNode) output.appendChild(safeNode);
    });
    return output.innerHTML;
  }

  // Inject live site badge styling specifically for the hero badge
  const badgeStyle = document.createElement('style');
  badgeStyle.id = 'slm-badge-style';
  badgeStyle.innerHTML = `
    .elementor-element-84e417c .elementskit-section-title > span {
      color: #ffffff !important;
      padding: 6px 14px !important;
      background-color: #FF1E57 !important;
      border-radius: 14px !important;
      font-family: "Poppins", Sans-serif !important;
      font-size: 13px !important;
      font-weight: 600 !important;
      text-transform: uppercase !important;
      letter-spacing: 0.5px !important;
      display: inline-block !important;
      margin-bottom: 14px !important;
      transition: all 0.25s ease !important;
    }
    .elementor-element-84e417c .elementskit-section-title:hover > span {
      color: #000000 !important;
      cursor: pointer;
    }
  `;
  document.head.appendChild(badgeStyle);



  // 1. Sync Global Company Details
  async function syncCompanySettings() {
    try {
      const res = await fetch('/api/settings');
      if (!res.ok) return;
      const data = await res.json();
      if (!data.success || !data.settings?.general) return;

      const g = data.settings.general;

      // Update phone across all footer / header links
      if (g.phone) {
        document.querySelectorAll('a[href^="tel:"]').forEach(el => {
          el.href = `tel:${g.phone.replace(/\s+/g, '')}`;
          if (el.textContent.trim().startsWith('+')) {
            el.textContent = g.phone;
          }
        });
      }

      // Update email
      if (g.email) {
        document.querySelectorAll('a[href^="mailto:"]').forEach(el => {
          el.href = `mailto:${g.email}`;
          if (el.textContent.includes('@')) {
            el.textContent = g.email;
          }
        });
      }

      // Update office address text
      if (g.address) {
        document.querySelectorAll('.elementskit-info-box-title, .address-text, .footer-address, .contact-address').forEach(el => {
          if (el.textContent.includes('Leadenhall') || el.textContent.includes('Canary Wharf')) {
            el.textContent = g.address;
          }
        });
      }
    } catch (e) {
      // Graceful fallback to static HTML
    }
  }

  // 2. Sync Team Members on About Us Page
  async function syncTeamMembers() {
    if (!window.location.pathname.includes('about')) return;

    try {
      const res = await fetch('/api/team');
      if (!res.ok) return;
      const data = await res.json();
      if (!data.success || !Array.isArray(data.team) || data.team.length === 0) return;

      const memberCards = document.querySelectorAll('.sassico-team-style-2');
      if (memberCards.length === 0) return;

      data.team.forEach((member, idx) => {
        const memberNameNorm = (member.full_name || '').trim().toLowerCase();
        let card = Array.from(memberCards).find(c => {
          const cardName = (c.querySelector('.profile-title, .ekit-team-modal-title, .tertiary-text-color')?.textContent || '').trim().toLowerCase();
          return cardName && (cardName.includes(memberNameNorm) || memberNameNorm.includes(cardName));
        });
        if (!card) card = memberCards[idx];
        if (!card) return;

        // Update Name
        const titleEl = card.querySelector('.profile-title a, .profile-title');
        if (titleEl && member.full_name) titleEl.textContent = member.full_name;

        const modalTitle = card.querySelector('.ekit-team-modal-title');
        if (modalTitle && member.full_name) modalTitle.textContent = member.full_name;

        // Update Job Title
        const posEl = card.querySelector('.profile-designation');
        if (posEl && member.job_title) posEl.textContent = member.job_title;

        const modalPos = card.querySelector('.ekit-team-modal-position');
        if (modalPos && member.job_title) modalPos.textContent = member.job_title;

        // Update Photo
        if (member.photo_url) {
          card.querySelectorAll('img').forEach(img => {
            img.src = safeCmsUrl(member.photo_url, 'src') || '';
            img.srcset = '';
          });
        }

        // Update Bio
        const bioEl = card.querySelector('.ekit-team-modal-content');
        if (bioEl && member.bio) bioEl.textContent = member.bio;

        // Update LinkedIn Link
        if (member.socials?.linkedin) {
          const linkedinLink = card.querySelector('a[href*="linkedin.com"], a[aria-label*="linkdIn"], a[aria-label*="LinkedIn"]');
          if (linkedinLink) {
            linkedinLink.href = safeCmsUrl(member.socials.linkedin) || '#';
          }
        }
      });
    } catch (e) {
      // Graceful fallback to static HTML
    }
  }

  // 3. CTA & Unlinked Buttons Redirect Bridge
  function syncCtaButtons() {
    const LOGIN_TARGET = 'https://salesleadmachine.uk/login';
    const ctaKeywords = [
      'login', 'log in', 'crm login', 'book ur demo', 'book your demo', 
      'book a demo', 'book demo', 'demo', 
      'free trial', 'start trial', 'try free', 'sign in'
    ];

    // Find all links and buttons
    document.querySelectorAll('a, button, [role="button"]').forEach(el => {
      const text = (el.textContent || '').trim().toLowerCase();
      const href = el.getAttribute('href');

      // Do NOT touch forms, form submits, or contact buttons
      if (el.closest('form') || el.type === 'submit' || text.includes('contact') || text.includes('submit')) {
        return;
      }

      const isDeadHref = !href || href === '#' || href === '#!' || href === 'javascript:void(0)' || href === 'javascript:;' || href.trim() === '';
      const isCtaMatch = ctaKeywords.some(k => text.includes(k));

      if (el.tagName === 'A') {
        // If it's a dead link or matches a demo/login/learn more CTA that has no valid internal page
        if (isCtaMatch || (isDeadHref && (el.classList.contains('elementskit-btn') || el.classList.contains('elementor-button') || el.classList.contains('btn')))) {
          // If href points nowhere or to #, point to login
          if (isDeadHref || (!href.startsWith('/') && !href.startsWith('http') && !href.startsWith('mailto:') && !href.startsWith('tel:'))) {
            el.setAttribute('href', LOGIN_TARGET);
            el.setAttribute('target', '_blank');
            el.setAttribute('rel', 'noopener noreferrer');
          }
        }
      } else {
        // Non-anchor buttons that don't submit forms
        if (isCtaMatch || el.classList.contains('elementskit-btn') || el.classList.contains('elementor-button')) {
          el.addEventListener('click', function(e) {
            e.preventDefault();
            window.open(LOGIN_TARGET, '_blank');
          });
        }
      }
    });
  }

  // Helper: Safely locate the intended section container without corrupting other sections
  function findSectionContainer(sec, idx, topSections, pageRoot, claimedContainers = new Set()) {
    if (sec.anchor_id) {
      const el = document.getElementById(sec.anchor_id) ||
                 pageRoot.querySelector(`[data-id="${sec.anchor_id}"], .elementor-element-${sec.anchor_id}`);
      if (el) return el;
    }

    if (sec.id) {
      const el = pageRoot.querySelector(`[data-slm-sec-id="${sec.id}"]`);
      if (el) return el;
    }

    const unclaimed = topSections.filter(s => !claimedContainers.has(s));

    // 1. Hero Section
    if (sec.section_type === 'hero') {
      const heroCandidate = unclaimed.find(s => s.classList.contains('elementor-element-a26d791') || s.querySelector('.ekit-heading--subtitle, .elementskit-section-subtitle')) || topSections[0];
      return heroCandidate;
    }

    // 2. Team Section
    if (sec.section_type === 'team') {
      return unclaimed.find(s => s.querySelector('.elementskit-team, .sassico-team-style-2'));
    }

    // 3. Partner Logos Wall
    if (sec.section_type === 'logo_wall') {
      return unclaimed.find(s => s.querySelector('.elementskit-client-logo, .simple_logo_carousel, .elementskit-clients-slider'));
    }

    // 4. Card Grid / Products Section
    if (sec.section_type === 'card_grid') {
      return unclaimed.find(s => s.getAttribute('data-id') === '3046460' || s.querySelector('.elementskit-infobox')) || unclaimed.find(s => s.querySelector('.elementskit-icon-box'));
    }

    // 5. CTA Banner
    if (sec.section_type === 'cta_banner') {
      return unclaimed.find(s => {
        if (s.querySelector('.elementskit-infobox, .elementskit-icon-box, .simple_logo_image')) return false;
        const text = (s.textContent || '').toLowerCase();
        return text.includes('review of your needs') || text.includes('ready to transform') || text.includes('get started') || s.classList.contains('banner-bg');
      });
    }

    // 6. Split Section (Must NEVER touch the hero section!)
    if (sec.section_type === 'split') {
      return unclaimed.find(s => {
        if (s.classList.contains('elementor-element-a26d791')) return false;
        const cols = s.querySelectorAll('.elementor-top-column');
        return cols.length === 2 && s.querySelector('img') && s.querySelector('h2, h3');
      });
    }

    // 7. Rich Text Article Section
    if (sec.section_type === 'rich_text') {
      return unclaimed.find(s => s.querySelector('.elementor-widget-text-editor'));
    }

    return unclaimed[0] || null;
  }

  // 4. Sync Page Sections (Safe, Non-Destructive, Supports Draft & Studio)
  async function syncPageSections() {
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const token = localStorage.getItem('slm_auth_token') || localStorage.getItem('admin_token') || '';
      const studioRequested = (
        urlParams.get('admin') === 'true' || urlParams.get('admin') === '1' ||
        urlParams.get('edit') === 'true' || urlParams.get('edit') === '1' ||
        urlParams.get('studio') === 'true' || urlParams.get('studio') === '1' ||
        urlParams.get('mode') === 'draft'
      );
      // URL flags alone must not expose the editor shell to anonymous visitors.
      const isStudio = Boolean(token && token.trim().length > 20 && (studioRequested || token));

      const path = window.location.pathname;
      const headers = {};
      if (token && token.trim().length > 20) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      const res = await fetch(`/api/page-content?path=${encodeURIComponent(path)}&mode=${isStudio ? 'draft' : 'published'}`, { headers });
      if (!res.ok) return;
      const data = await res.json();
      const pageRoot = document.querySelector('[data-elementor-type="wp-page"], .elementor-2911, main') || document.body;
      const topSections = Array.from(pageRoot.querySelectorAll('.elementor-top-section'));

      if (!data.success || !Array.isArray(data.sections) || data.sections.length === 0) {
        if (isStudio) {
          const fallbackData = (data && data.page) ? data : {
            page: { id: '', title: document.title.replace('- Sales Lead Machine', '').trim() },
            sections: [],
            has_draft_changes: false
          };
          initAdminVisualStudio(fallbackData, topSections, pageRoot, token);
        }
        return;
      }

      const claimedContainers = new Set();
      data.sections.forEach((sec, idx) => {
        const d = sec.data || {};
        const container = findSectionContainer(sec, idx, topSections, pageRoot, claimedContainers);
        if (container) claimedContainers.add(container);
        if (!container) return; // Safely skip if no safe match is found

        // Tag section for Canvas Click-to-Select and Accessibility in Studio Mode
        container.setAttribute('data-slm-sec-id', sec.id);
        container.setAttribute('data-slm-sec-idx', idx);
        container.setAttribute('tabindex', '0');
        container.setAttribute('role', 'region');
        container.setAttribute('aria-label', `${sec.label || sec.section_type || 'Section'} (Press Enter to edit in Visual Studio)`);
        if (!container.dataset.slmA11yBound) {
          container.dataset.slmA11yBound = 'true';
          container.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              container.click();
            }
          });
        }

        // 1. Hero Section Hydration (Preserve Red Pill Badge & Verbatim Copy)
        if (sec.section_type === 'hero') {
          const badgeSpan = container.querySelector('.ekit-heading--title > span, .elementskit-section-title > span');
          const subtitleEl = container.querySelector('.elementskit-section-subtitle, .ekit-heading--subtitle');
          const titleEl = container.querySelector('.ekit-heading--title, .elementskit-section-title, .elementor-heading-title, h1');

          if (badgeSpan && subtitleEl) {
            if (d.eyebrow) badgeSpan.textContent = d.eyebrow;
            if (d.title) subtitleEl.innerHTML = sanitizeHtml(d.title);
          } else if (subtitleEl && titleEl && subtitleEl !== titleEl) {
            if (d.eyebrow) subtitleEl.textContent = d.eyebrow;
            if (d.title) titleEl.innerHTML = sanitizeHtml(d.title);
          } else if (titleEl) {
            if (d.title) titleEl.innerHTML = sanitizeHtml(d.title);
          } else if (subtitleEl) {
            if (d.title) subtitleEl.innerHTML = sanitizeHtml(d.title);
          }

          const bodyText = d.body || d.body_html || d.description || d.subtitle;
          if (bodyText) {
            const descWrapper = container.querySelector('.ekit-heading__description, .elementor-widget-text-editor .elementor-widget-container, .elementor-widget-text-editor');
            if (descWrapper) {
              if (bodyText.includes('<p>') || bodyText.includes('<br>') || bodyText.includes('<div>')) {
                descWrapper.innerHTML = sanitizeHtml(bodyText);
              } else {
                const paras = bodyText.split(/\n\n+/).filter(Boolean);
                if (paras.length > 1) {
                  descWrapper.innerHTML = paras.map(p => `<p>${sanitizeHtml(p.trim())}</p>`).join('');
                } else {
                  descWrapper.innerHTML = `<p>${sanitizeHtml(bodyText.trim())}</p>`;
                }
              }
            }
          }

          const allBtns = container.querySelectorAll('.ekit-btn-wraper a, .elementskit-btn');
          const btn1Label = d.btn1_text || (d.buttons && d.buttons[0] && d.buttons[0].label);
          const btn1Url = d.btn1_url || (d.buttons && d.buttons[0] && d.buttons[0].url);
          if (allBtns[0] && btn1Label) {
            const icon = allBtns[0].querySelector('i');
            allBtns[0].textContent = btn1Label + ' ';
            if (icon) allBtns[0].appendChild(icon);
            if (btn1Url) allBtns[0].href = safeCmsUrl(btn1Url) || '#';
          }

          const btn2Label = d.cta_primary_text || d.button_text || (d.buttons && d.buttons[1] && d.buttons[1].label);
          const btn2Url = d.cta_primary_url || (d.buttons && d.buttons[1] && d.buttons[1].url);
          if (allBtns[1] && btn2Label) {
            const icon = allBtns[1].querySelector('i');
            allBtns[1].textContent = btn2Label + ' ';
            if (icon) allBtns[1].appendChild(icon);
            if (btn2Url) allBtns[1].href = safeCmsUrl(btn2Url) || '#';
          }

          const imgUrl = d.dashboard_image || d.image_url;
          if (imgUrl) {
            const macImg = container.querySelector('.elementor-element-16fedd0 img, img[src*="MacBook"], img[src*="b2b-image"]');
            if (macImg) macImg.src = safeCmsUrl(imgUrl, 'src') || '';
          }
        }

        // 2. Team Section Hydration
        if (sec.section_type === 'team') {
          if (d.eyebrow) {
            const eb = container.querySelector('.elementskit-section-subtitle, .ekit-heading--subtitle');
            if (eb) eb.textContent = d.eyebrow;
          }
          if (d.title) {
            const h = container.querySelector('.ekit-heading--title, .elementskit-section-title, .elementor-heading-title');
            if (h) h.textContent = d.title;
          }
          if (Array.isArray(d.members)) {
            const memberCards = container.querySelectorAll('.sassico-team-style-2').length > 0
              ? container.querySelectorAll('.sassico-team-style-2')
              : container.querySelectorAll('.profile-card');

            d.members.forEach((m, idx) => {
              const card = memberCards[idx];
              if (!card) return;
              if (m.name) {
                const titleEl = card.querySelector('.profile-title a, .profile-title');
                if (titleEl) titleEl.textContent = m.name;
                const modalTitle = card.querySelector('.ekit-team-modal-title');
                if (modalTitle) modalTitle.textContent = m.name;
              }
              if (m.role) {
                const posEl = card.querySelector('.profile-designation');
                if (posEl) posEl.textContent = m.role;
                const modalPos = card.querySelector('.ekit-team-modal-position');
                if (modalPos) modalPos.textContent = m.role;
              }
              if (m.photo) {
                card.querySelectorAll('img').forEach(img => {
                  img.src = safeCmsUrl(m.photo, 'src') || '';
                  img.srcset = '';
                });
              }
              if (m.linkedin) {
                const linkEl = card.querySelector('a[href*="linkedin.com"], a[aria-label*="linkdIn"], a[aria-label*="LinkedIn"]');
                if (linkEl) linkEl.href = safeCmsUrl(m.linkedin) || '#';
              }
            });
          }
        }

        // 3. Partner Logos Wall Hydration
        if (sec.section_type === 'logo_wall') {
          if (d.eyebrow) {
            const eb = container.querySelector('.elementskit-section-subtitle, .ekit-heading--subtitle');
            if (eb) eb.textContent = d.eyebrow;
          }
          if (d.title) {
            const h = container.querySelector('.ekit-heading--title, .elementskit-section-title, .elementor-heading-title');
            if (h) h.textContent = d.title;
          }
          if (Array.isArray(d.logos)) {
            const logoItems = container.querySelectorAll('.elementskit-client-slider-item').length > 0
              ? container.querySelectorAll('.elementskit-client-slider-item')
              : container.querySelectorAll('.single-client');

            d.logos.forEach((logo, idx) => {
              const item = logoItems[idx];
              if (!item) return;
              const img = item.querySelector('img');
              if (img && logo.image_url) {
                img.src = safeCmsUrl(logo.image_url, 'src') || '';
                img.srcset = '';
                if (logo.name) img.alt = logo.name;
              }
              let link = item.querySelector('a');
              if (logo.url) {
                if (!link && img) {
                  link = document.createElement('a');
                  link.href = safeCmsUrl(logo.url) || '#';
                  link.target = '_blank';
                  link.rel = 'noopener noreferrer';
                  img.parentNode.insertBefore(link, img);
                  link.appendChild(img);
                } else if (link) {
                  link.href = safeCmsUrl(logo.url) || '#';
                }
              }
            });
          }
        }

        // 4. Split Section Hydration
        if (sec.section_type === 'split') {
          const badgeSpan = container.querySelector('.ekit-heading--title > span, .elementskit-section-title > span');
          const subtitleEl = container.querySelector('.elementskit-section-subtitle, .ekit-heading--subtitle');
          const titleEl = container.querySelector('.ekit-heading--title, .elementskit-section-title, .elementor-heading-title');

          if (badgeSpan && subtitleEl) {
            if (d.eyebrow) badgeSpan.textContent = d.eyebrow;
            if (d.title) subtitleEl.innerHTML = sanitizeHtml(d.title);
          } else if (subtitleEl && titleEl && subtitleEl !== titleEl) {
            if (d.eyebrow) subtitleEl.textContent = d.eyebrow;
            if (d.title) titleEl.innerHTML = sanitizeHtml(d.title);
          } else if (titleEl) {
            if (d.title) titleEl.innerHTML = sanitizeHtml(d.title);
          } else if (subtitleEl) {
            if (d.title) subtitleEl.innerHTML = sanitizeHtml(d.title);
          }

          if (d.description || d.body || d.subtitle || d.body_html) {
            const rawDesc = d.body_html || d.description || d.body || d.subtitle;
            const descWrapper = container.querySelector('.ekit-heading__description, .elementor-widget-text-editor .elementor-widget-container, .elementor-widget-text-editor');
            if (descWrapper) {
              if (rawDesc.includes('<p>') || rawDesc.includes('<br>') || rawDesc.includes('<div>')) {
                descWrapper.innerHTML = sanitizeHtml(rawDesc);
              } else {
                const paras = rawDesc.split(/\n\n+/).filter(Boolean);
                if (paras.length > 1) {
                  descWrapper.innerHTML = paras.map(p => `<p>${sanitizeHtml(p.trim())}</p>`).join('');
                } else {
                  descWrapper.innerHTML = `<p>${sanitizeHtml(rawDesc.trim())}</p>`;
                }
              }
            }
          }

          if (Array.isArray(d.bullets) && d.bullets.length > 0) {
            const bulletEls = container.querySelectorAll('.elementskit-infobox .box-body p, .elementskit-infobox p');
            bulletEls.forEach((el, idx) => {
              if (d.bullets[idx]) {
                const bText = typeof d.bullets[idx] === 'string' ? d.bullets[idx] : d.bullets[idx].text;
                if (bText) el.textContent = bText;
              }
            });
          }

          if (d.btn1_text || d.cta_label || d.cta_text) {
            const btn = container.querySelector('.ekit-btn-wraper a, a.elementor-button, .elementskit-btn');
            if (btn) {
              const icon = btn.querySelector('i');
              btn.textContent = (d.btn1_text || d.cta_label || d.cta_text) + ' ';
              if (icon) btn.appendChild(icon);
              if (d.btn1_url || d.cta_url) btn.href = safeCmsUrl(d.btn1_url || d.cta_url) || '#';
            }
          }

          const splitImg = container.querySelector('.elementor-widget-image img, img[src*="image-3"], img[src*="undraw"]');
          const splitImgUrl = d.dashboard_image || d.image_url;
          if (splitImg && splitImgUrl) {
            splitImg.src = safeCmsUrl(splitImgUrl, 'src') || '';
          }
        }

        // 4. CTA Banner Hydration
        if (sec.section_type === 'cta_banner') {
          if (d.title) {
            const h = container.querySelector('h2, h3, .elementor-heading-title');
            if (h) h.textContent = d.title;
          }
          if (d.subtitle || d.description || d.body || d.body_html) {
            const rawDesc = d.body_html || d.subtitle || d.description || d.body;
            const descWrapper = container.querySelector('.elementor-widget-text-editor .elementor-widget-container, .elementor-widget-text-editor');
            if (descWrapper) {
              if (rawDesc.includes('<p>') || rawDesc.includes('<br>') || rawDesc.includes('<div>')) {
                descWrapper.innerHTML = sanitizeHtml(rawDesc);
              } else {
                descWrapper.innerHTML = `<p>${sanitizeHtml(rawDesc.trim())}</p>`;
              }
            }
          }
          if (d.button_text || d.cta_text || d.cta_label || d.button_url || d.cta_url || d.cta_primary_url) {
            const btn = container.querySelector('.elementor-button, .elementskit-btn, .btn, a');
            if (btn) {
              const icon = btn.querySelector('i');
              if (d.button_text || d.cta_text || d.cta_label) {
                btn.textContent = (d.button_text || d.cta_text || d.cta_label) + ' ';
                if (icon) btn.appendChild(icon);
              }
              if (d.button_url || d.cta_url || d.cta_primary_url) {
                btn.href = safeCmsUrl(d.button_url || d.cta_url || d.cta_primary_url) || '#';
              }
            }
          }
        }

        // 5. Rich Text Hydration
        if (sec.section_type === 'rich_text') {
          if (d.title) {
            const h = container.querySelector('h1, h2, h3, .elementskit-section-title');
            if (h) h.textContent = d.title;
          }
          if (d.body_html || d.content || d.body) {
            const contentBox = container.querySelector('.elementor-widget-text-editor, .elementor-widget-container, .container > div:not(.ekit-wid-con), .rich-content, .privacy-body');
            if (contentBox) contentBox.innerHTML = sanitizeHtml(d.body_html || d.content || d.body);
          }
        }
        // 6. Card Grid / Products / Problems Hydration (Strict Heading Isolation)
        if (sec.section_type === 'card_grid') {
          const headingWraper = container.querySelector('.ekit-heading, .elementskit-section-title-wraper, .elementor-widget-elementskit-heading, .elementor-widget-heading');
          if (headingWraper) {
            if (d.title) {
              const h = headingWraper.querySelector('.ekit-heading--title, .elementskit-section-title, .elementor-heading-title, h1, h2, h3');
              if (h) h.textContent = d.title;
            }
            if (d.subtitle || d.description) {
              const sub = headingWraper.querySelector('.ekit-heading--subtitle, .elementskit-section-subtitle, .ekit-heading__description p');
              if (sub) sub.innerHTML = sanitizeHtml(d.subtitle || d.description);
            }
          }
          if (Array.isArray(d.cards)) {
            let cardContainers = Array.from(container.querySelectorAll('.elementskit-infobox'));
            if (cardContainers.length === 0) {
              cardContainers = Array.from(container.querySelectorAll('.service-card, .elementor-widget-elementskit-icon-box .ekit-wid-con, [data-widget_type*="icon-box"] .ekit-wid-con'));
            }
            d.cards.forEach((c, cIdx) => {
              const cardEl = cardContainers[cIdx];
              if (!cardEl) return;
              if (c.title) {
                const t = cardEl.querySelector('.elementskit-info-box-title, .service-title');
                if (t) t.textContent = c.title;
              }
              if (c.description) {
                const desc = cardEl.querySelector('.box-body p, .elementskit-box-description, .service-desc, p');
                if (desc) desc.innerHTML = sanitizeHtml(c.description);
              }
              if (c.url) {
                const a = cardEl.querySelector('a');
                if (a) a.href = safeCmsUrl(c.url) || '#';
              }
              if (c.image) {
                const img = cardEl.querySelector('img');
                if (img) {
                  img.src = safeCmsUrl(c.image, 'src') || '';
                  img.srcset = '';
                }
              }
            });
          }
        }
      });

      if (isStudio) {
        initAdminVisualStudio(data, topSections, pageRoot, token);
      }
    } catch (e) {
      console.warn('[CMS Hydrate Error]', e);
    }
  }

  // 5. Enterprise Visual Studio (Compact Top Bar + Docked Inspector + Canvas Click-to-Select)
  window.slmActiveEditors = window.slmActiveEditors || {};

  window.switchRichEditorTab = function(fieldId, mode) {
    const nativeWrap = document.getElementById(fieldId + '-wrap-native');
    const quillWrap = document.getElementById(fieldId + '-wrap-quill');
    const inspector = document.getElementById('slm-studio-inspector');
    if (!nativeWrap || !quillWrap || !inspector) return;

    window.slmActiveEditors[fieldId] = window.slmActiveEditors[fieldId] || { mode: 'native' };
    window.slmActiveEditors[fieldId].mode = mode;

    const btnNative = inspector.querySelector(`[onclick*="switchRichEditorTab('${fieldId}', 'native')"]`);
    const btnQuill = inspector.querySelector(`[onclick*="switchRichEditorTab('${fieldId}', 'quill')"]`);

    if (mode === 'native') {
      nativeWrap.style.display = 'block';
      quillWrap.style.display = 'none';
      if (btnNative) { btnNative.style.background = '#6366f1'; btnNative.style.color = '#fff'; }
      if (btnQuill) { btnQuill.style.background = 'transparent'; btnQuill.style.color = '#94a3b8'; }

      if (window.slmActiveEditors[fieldId].quillInstance) {
        const nativeEd = document.getElementById(fieldId + '-native-editor');
        if (nativeEd) nativeEd.innerHTML = window.slmActiveEditors[fieldId].quillInstance.root.innerHTML;
      }
    } else {
      nativeWrap.style.display = 'none';
      quillWrap.style.display = 'block';
      if (btnQuill) { btnQuill.style.background = '#6366f1'; btnQuill.style.color = '#fff'; }
      if (btnNative) { btnNative.style.background = 'transparent'; btnNative.style.color = '#94a3b8'; }

      if (!window.slmActiveEditors[fieldId].quillInstance && window.Quill) {
        const quillContainer = document.getElementById(fieldId + '-quill-editor');
        if (quillContainer) {
          const initialContent = document.getElementById(fieldId + '-native-editor')?.innerHTML || '';
          const q = new window.Quill(quillContainer, {
            theme: 'snow',
            modules: {
              toolbar: [
                ['bold', 'italic', 'underline'],
                [{ header: [2, 3, false] }],
                [{ list: 'ordered' }, { list: 'bullet' }],
                ['link', 'clean']
              ]
            }
          });
          q.root.innerHTML = initialContent;
          window.slmActiveEditors[fieldId].quillInstance = q;
        }
      }
    }
  };

  window.formatRichDoc = function(fieldId, cmd, val = null) {
    const editor = document.getElementById(fieldId + '-native-editor');
    if (editor) editor.focus();
    document.execCommand(cmd, false, val);
  };

  window.addRichLink = function(fieldId) {
    const url = prompt('Enter link URL:', 'https://');
    if (url) {
      window.formatRichDoc(fieldId, 'createLink', url);
    }
  };

  function renderRichTextField(fieldId, label, initialContent = '') {
    window.slmActiveEditors[fieldId] = { mode: 'native' };
    return `
      <div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
          <label style="font-size:11px; text-transform:uppercase; color:#94a3b8; font-weight:700;">${label}</label>
          <div style="display:flex; gap:2px; background:#1e293b; padding:2px; border-radius:6px;">
            <button type="button" onclick="switchRichEditorTab('${fieldId}', 'native')" style="background:#6366f1; color:#fff; border:none; padding:2px 7px; border-radius:4px; font-size:10px; font-weight:700; cursor:pointer;">⚡ Native</button>
            <button type="button" onclick="switchRichEditorTab('${fieldId}', 'quill')" style="background:transparent; color:#94a3b8; border:none; padding:2px 7px; border-radius:4px; font-size:10px; font-weight:700; cursor:pointer;">🖋️ Quill</button>
          </div>
        </div>

        <div id="${fieldId}-wrap-native">
          <div style="display:flex; gap:2px; background:#1e293b; padding:4px 6px; border-radius:6px 6px 0 0; border:1px solid rgba(255,255,255,0.12); border-bottom:none; flex-wrap:wrap;">
            <button type="button" onclick="formatRichDoc('${fieldId}','bold')" title="Bold" style="background:#334155; color:#fff; border:none; border-radius:3px; padding:2px 6px; font-weight:700; cursor:pointer; font-size:11px;">B</button>
            <button type="button" onclick="formatRichDoc('${fieldId}','italic')" title="Italic" style="background:#334155; color:#fff; border:none; border-radius:3px; padding:2px 6px; font-style:italic; cursor:pointer; font-size:11px;">I</button>
            <button type="button" onclick="formatRichDoc('${fieldId}','underline')" title="Underline" style="background:#334155; color:#fff; border:none; border-radius:3px; padding:2px 6px; text-decoration:underline; cursor:pointer; font-size:11px;">U</button>
            <button type="button" onclick="formatRichDoc('${fieldId}','formatBlock','<h3>')" title="Heading 3" style="background:#334155; color:#fff; border:none; border-radius:3px; padding:2px 6px; cursor:pointer; font-size:10px; font-weight:700;">H3</button>
            <button type="button" onclick="formatRichDoc('${fieldId}','insertUnorderedList')" title="Bullet List" style="background:#334155; color:#fff; border:none; border-radius:3px; padding:2px 6px; cursor:pointer; font-size:11px;">• List</button>
            <button type="button" onclick="addRichLink('${fieldId}')" title="Insert Link" style="background:#334155; color:#fff; border:none; border-radius:3px; padding:2px 6px; cursor:pointer; font-size:11px;">🔗</button>
            <button type="button" onclick="formatRichDoc('${fieldId}','removeFormat')" title="Clear Formatting" style="background:#334155; color:#94a3b8; border:none; border-radius:3px; padding:2px 6px; cursor:pointer; font-size:10px;">🧹</button>
          </div>
          <div id="${fieldId}-native-editor" contenteditable="true" style="min-height:75px; max-height:160px; background:#090d16; border:1px solid rgba(255,255,255,0.12); border-radius:0 0 6px 6px; padding:8px 10px; color:#f8fafc; font-size:12px; line-height:1.5; outline:none; overflow-y:auto;">${initialContent}</div>
        </div>

        <div id="${fieldId}-wrap-quill" style="display:none;">
          <div id="${fieldId}-quill-editor" style="min-height:90px; background:#090d16; color:#f8fafc; border-radius:0 0 6px 6px;"></div>
        </div>
      </div>
    `;
  }

  function getRichFieldValue(fieldId) {
    const meta = window.slmActiveEditors[fieldId];
    if (meta && meta.mode === 'quill' && meta.quillInstance) {
      return meta.quillInstance.root.innerHTML;
    }
    const nativeEl = document.getElementById(fieldId + '-native-editor');
    return nativeEl ? nativeEl.innerHTML : '';
  }

  // Toast Notification System
  function showStudioToast(message, type = 'success') {
    let toast = document.getElementById('slm-studio-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'slm-studio-toast';
      toast.style.cssText = `
        position: fixed; top: 54px; right: 400px; z-index: 10000000;
        padding: 10px 18px; border-radius: 8px; font-size: 12px; font-weight: 700;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5); transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        display: flex; align-items: center; gap: 8px; pointer-events: none; opacity: 0; transform: translateY(-10px);
      `;
      document.body.appendChild(toast);
    }

    if (type === 'success') {
      toast.style.background = '#065f46';
      toast.style.color = '#34d399';
      toast.style.border = '1px solid #10b981';
      toast.innerHTML = `<span>✓</span> <span>${message}</span>`;
    } else if (type === 'draft') {
      toast.style.background = '#78350f';
      toast.style.color = '#fbbf24';
      toast.style.border = '1px solid #f59e0b';
      toast.innerHTML = `<span>💾</span> <span>${message}</span>`;
    } else {
      toast.style.background = '#7f1d1d';
      toast.style.color = '#f87171';
      toast.style.border = '1px solid #ef4444';
      toast.innerHTML = `<span>✕</span> <span>${message}</span>`;
    }

    toast.style.opacity = '1';
    toast.style.transform = 'translateY(0)';
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(-10px)';
    }, 3200);
  }

  // Visual Studio Implementation
  function initAdminVisualStudio(data, topSections, pageRoot, token) {
    const page = data.page || {};
    const sections = Array.isArray(data.sections) ? data.sections : [];
    const pageId = page.id || '';
    const hasDraft = !!data.has_draft_changes;

    // Remove legacy clutter
    document.querySelectorAll('.slm-edit-btn, #slm-master-page-modal').forEach(el => el.remove());

    // Inject Studio CSS styles for Canvas Highlights, Scrollbar & Element Isolation
    let studioStyle = document.getElementById('slm-studio-injected-styles');
    if (!studioStyle) {
      studioStyle = document.createElement('style');
      studioStyle.id = 'slm-studio-injected-styles';
      document.head.appendChild(studioStyle);
    }
    studioStyle.innerHTML = `
      /* Studio Mode: Hide all floating widgets that overlap the inspector or trap pointer events */
      #mySidenav, .slm-floating-sidenav, #qVDSFgMnMQ, .mo-optin-form-lightbox, .moModal, #wpfront-scroll-top-container {
        display: none !important;
        pointer-events: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
      }

      [data-slm-sec-id] {
        transition: outline 0.2s ease, box-shadow 0.2s ease !important;
        position: relative !important;
      }
      [data-slm-sec-id]:hover {
        outline: 2px dashed rgba(99, 102, 241, 0.6) !important;
        outline-offset: 2px !important;
        cursor: pointer !important;
      }
      [data-slm-sec-id].slm-sec-selected {
        outline: 3px solid #6366f1 !important;
        outline-offset: 4px !important;
        box-shadow: 0 0 30px rgba(99, 102, 241, 0.35) !important;
        border-radius: 8px !important;
      }
      .slm-accordion-header:hover {
        background: #1e293b !important;
      }
      .slm-vp-btn.active {
        background: #6366f1 !important;
        color: #fff !important;
      }

      #slm-studio-topbar {
        z-index: 2147483647 !important;
      }
      #slm-studio-inspector {
        z-index: 2147483646 !important;
        pointer-events: auto !important;
      }

      #slm-inspector-scroll {
        display: block !important;
        flex: 1 1 auto !important;
        min-height: 0 !important;
        height: calc(100vh - 165px) !important;
        max-height: calc(100vh - 165px) !important;
        overflow-y: scroll !important;
        overflow-x: hidden !important;
        -webkit-overflow-scrolling: touch !important;
        overscroll-behavior: contain !important;
        touch-action: pan-y !important;
        scrollbar-width: thin !important;
        scrollbar-color: #6366f1 #090d16 !important;
        box-sizing: border-box !important;
      }
      #slm-inspector-scroll::-webkit-scrollbar {
        width: 10px !important;
        display: block !important;
      }
      #slm-inspector-scroll::-webkit-scrollbar-track {
        background: #090d16 !important;
        border-left: 1px solid rgba(255,255,255,0.06) !important;
      }
      #slm-inspector-scroll::-webkit-scrollbar-thumb {
        background: #6366f1 !important;
        border-radius: 5px !important;
        border: 2px solid #090d16 !important;
      }
      #slm-inspector-scroll::-webkit-scrollbar-thumb:hover {
        background: #818cf8 !important;
      }

      .slm-section-card {
        margin-bottom: 12px !important;
        box-sizing: border-box !important;
      }
    `;

    // Also explicitly hide floating sidenav via JS
    const mySidenav = document.getElementById('mySidenav');
    if (mySidenav) {
      mySidenav.style.setProperty('display', 'none', 'important');
      mySidenav.style.setProperty('pointer-events', 'none', 'important');
    }

    // 1. Build Top Bar (Fixed 42px)
    let topBar = document.getElementById('slm-studio-topbar');
    if (!topBar) {
      topBar = document.createElement('div');
      topBar.id = 'slm-studio-topbar';
      topBar.style.cssText = `
        position: fixed; top: 0; left: 0; right: 0; height: 42px; z-index: 2147483647;
        background: #090d16; border-bottom: 1px solid rgba(255,255,255,0.12); color: #f8fafc;
        display: flex; align-items: center; justify-content: space-between;
        padding: 0 14px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 11px; font-weight: 600;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
      `;
      document.body.prepend(topBar);
      document.body.style.paddingTop = '42px';
    }

    topBar.innerHTML = `
      <!-- Left: Brand & Page Selector -->
      <div style="display:flex; align-items:center; gap:10px;">
        <div style="display:flex; align-items:center; gap:6px;">
          <span id="slm-status-dot" style="width:8px; height:8px; border-radius:50%; background:${hasDraft ? '#f59e0b' : '#10b981'}; box-shadow:0 0 8px ${hasDraft ? '#f59e0b' : '#10b981'};"></span>
          <span style="font-weight:800; letter-spacing:0.5px; color:#fff; font-size:12px;">SLM STUDIO</span>
        </div>

        <select id="slm-page-select" style="background:#1e293b; color:#cbd5e1; border:1px solid rgba(255,255,255,0.15); border-radius:6px; padding:3px 8px; font-size:11px; font-weight:600; outline:none; cursor:pointer;">
          <option value="${window.location.pathname}" selected>📄 Current Page (${sections.length} Sections)</option>
        </select>

        <span id="slm-status-pill" style="padding:2px 8px; border-radius:12px; font-size:10px; font-weight:700; ${hasDraft ? 'background:rgba(245,158,11,0.2); color:#fbbf24; border:1px solid rgba(245,158,11,0.4);' : 'background:rgba(16,185,129,0.2); color:#34d399; border:1px solid rgba(16,185,129,0.4);'}">
          ${hasDraft ? '● Draft Changes Pending' : '● Live In Sync'}
        </span>
      </div>

      <!-- Center: Responsive Viewport Switcher -->
      <div style="display:flex; align-items:center; background:#1e293b; border:1px solid rgba(255,255,255,0.1); border-radius:6px; padding:2px;">
        <button id="slm-vp-desktop" class="slm-vp-btn active" style="background:#6366f1; color:#fff; border:none; padding:3px 9px; border-radius:4px; font-size:11px; font-weight:600; cursor:pointer; display:flex; align-items:center; gap:4px;">💻 <span>Desktop</span></button>
        <button id="slm-vp-tablet" class="slm-vp-btn" style="background:transparent; color:#94a3b8; border:none; padding:3px 9px; border-radius:4px; font-size:11px; font-weight:600; cursor:pointer; display:flex; align-items:center; gap:4px;">📱 <span>Tablet (768px)</span></button>
        <button id="slm-vp-mobile" class="slm-vp-btn" style="background:transparent; color:#94a3b8; border:none; padding:3px 9px; border-radius:4px; font-size:11px; font-weight:600; cursor:pointer; display:flex; align-items:center; gap:4px;">📱 <span>Mobile (375px)</span></button>
      </div>

      <!-- Right: Action Buttons -->
      <div style="display:flex; align-items:center; gap:8px;">
        <button id="slm-btn-discard" style="background:#1e293b; color:#ef4444; border:1px solid rgba(239,68,68,0.3); padding:4px 10px; border-radius:6px; font-weight:700; cursor:pointer; font-size:11px; display:${hasDraft ? 'inline-block' : 'none'};">
          ↩ Discard Draft
        </button>
        <button id="slm-btn-save-draft" style="background:#1e293b; color:#f8fafc; border:1px solid rgba(255,255,255,0.2); padding:4px 12px; border-radius:6px; font-weight:700; cursor:pointer; font-size:11px; display:flex; align-items:center; gap:5px;">
          <span>💾</span> <span>Save Draft</span>
        </button>
        <button id="slm-btn-publish" style="background:linear-gradient(135deg, #10b981 0%, #059669 100%); color:#fff; border:1px solid rgba(255,255,255,0.3); padding:4px 14px; border-radius:6px; font-weight:700; cursor:pointer; font-size:11px; display:flex; align-items:center; gap:5px; box-shadow:0 2px 10px rgba(16,185,129,0.3);">
          <span>🚀</span> <span>Publish Live</span>
        </button>
        <button id="slm-btn-toggle-inspector" style="background:#312e81; color:#c7d2fe; border:1px solid #6366f1; padding:4px 10px; border-radius:6px; font-weight:700; cursor:pointer; font-size:11px; display:flex; align-items:center; gap:4px;">
          <span>🎨</span> <span>Inspector</span>
        </button>
        <a href="/admin/" target="_blank" style="color:#94a3b8; background:#1e293b; border:1px solid rgba(255,255,255,0.1); padding:4px 10px; border-radius:6px; text-decoration:none; font-size:11px;">Admin</a>
        <button id="slm-btn-exit" style="background:#ef4444; color:#fff; border:none; padding:4px 9px; border-radius:6px; font-weight:700; cursor:pointer; font-size:11px;">✕</button>
      </div>
    `;

    // Populate Page Dropdown from `/api/admin/pages`
    fetch('/api/admin/pages', { headers: { 'Authorization': `Bearer ${token}` } })
      .then(r => r.json())
      .then(res => {
        if (res && res.success && Array.isArray(res.pages)) {
          const select = document.getElementById('slm-page-select');
          if (select) {
            select.innerHTML = '';
            const curPath = window.location.pathname.replace(/\/$/, '') || '/';
            const curSlug = curPath.split('/').filter(Boolean).pop() || '';
            let matched = false;

            res.pages.forEach(p => {
              const opt = document.createElement('option');
              opt.value = p.full_path;
              const hasPageDraft = (p.draft_changes_count > 0) || (p.status === 'draft');
              opt.textContent = `${p.title} ${hasPageDraft ? '● (Draft)' : ''}`;
              
              const pPath = (p.full_path || '').replace(/\/$/, '') || '/';
              const pSlug = (p.slug || pPath.split('/').filter(Boolean).pop() || '').toLowerCase();
              
              const isDirectMatch = p.full_path === window.location.pathname || curPath === pPath;
              const isSlugMatch = curSlug && (curSlug === pSlug || (curSlug === 'for-marketing' && pSlug === 'for-marketer') || (curSlug === 'crome-extension' && pSlug === 'chrome-extension'));
              const isRootMatch = curPath === '/' && pPath === '/';

              if (!matched && (isDirectMatch || isSlugMatch || isRootMatch)) {
                opt.selected = true;
                matched = true;
              }
              select.appendChild(opt);
            });
            select.onchange = () => {
              window.location.href = `${select.value}?admin=true&studio=true`;
            };
          }
        }
      })
      .catch(() => {});

    // 2. Viewport Simulator Setup
    const pageContainer = document.querySelector('[data-elementor-type="wp-page"], .elementor-2911, main, #page') || document.body;
    pageContainer.style.transition = 'max-width 0.3s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.3s ease, border 0.3s ease';

    function setViewport(mode) {
      document.querySelectorAll('.slm-vp-btn').forEach(b => {
        b.classList.remove('active');
        b.style.background = 'transparent';
        b.style.color = '#94a3b8';
      });

      const activeBtn = document.getElementById(`slm-vp-${mode}`);
      if (activeBtn) {
        activeBtn.classList.add('active');
        activeBtn.style.background = '#6366f1';
        activeBtn.style.color = '#fff';
      }

      if (mode === 'desktop') {
        pageContainer.style.maxWidth = '100%';
        pageContainer.style.margin = '0 auto';
        pageContainer.style.border = 'none';
        pageContainer.style.boxShadow = 'none';
      } else if (mode === 'tablet') {
        pageContainer.style.maxWidth = '768px';
        pageContainer.style.margin = '20px auto';
        pageContainer.style.border = '2px solid rgba(255,255,255,0.15)';
        pageContainer.style.borderRadius = '16px';
        pageContainer.style.boxShadow = '0 25px 60px rgba(0,0,0,0.6)';
      } else if (mode === 'mobile') {
        pageContainer.style.maxWidth = '375px';
        pageContainer.style.margin = '20px auto';
        pageContainer.style.border = '2px solid rgba(255,255,255,0.15)';
        pageContainer.style.borderRadius = '24px';
        pageContainer.style.boxShadow = '0 25px 60px rgba(0,0,0,0.6)';
      }
    }

    document.getElementById('slm-vp-desktop').onclick = () => setViewport('desktop');
    document.getElementById('slm-vp-tablet').onclick = () => setViewport('tablet');
    document.getElementById('slm-vp-mobile').onclick = () => setViewport('mobile');

    // 3. Build Docked Visual Side Inspector (380px)
    let inspector = document.getElementById('slm-studio-inspector');
    if (!inspector) {
      inspector = document.createElement('div');
      inspector.id = 'slm-studio-inspector';
      document.body.appendChild(inspector);
    }
    inspector.style.cssText = `
      position: fixed; top: 42px; right: 0; bottom: 0; width: 380px; z-index: 2147483646;
      height: calc(100vh - 42px); max-height: calc(100vh - 42px); pointer-events: auto;
      background: #0b1120; border-left: 1px solid rgba(255,255,255,0.12); color: #f8fafc;
      display: flex; flex-direction: column; box-shadow: -8px 0 30px rgba(0,0,0,0.5);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      transform: translateX(0); transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      overflow: hidden; box-sizing: border-box;
    `;
    document.body.style.marginRight = '380px';
    document.body.style.transition = 'margin-right 0.25s cubic-bezier(0.16, 1, 0.3, 1)';

    let isInspectorOpen = true;
    const setInspectorOpen = (open) => {
      isInspectorOpen = open;
      inspector.style.transform = isInspectorOpen ? 'translateX(0)' : 'translateX(100%)';
      document.body.style.marginRight = isInspectorOpen ? '380px' : '0px';
      const btn = document.getElementById('slm-btn-toggle-inspector');
      if (btn) {
        btn.style.background = isInspectorOpen ? '#312e81' : '#1e293b';
        btn.style.color = isInspectorOpen ? '#c7d2fe' : '#94a3b8';
      }
    };
    const toggleInspector = () => setInspectorOpen(!isInspectorOpen);
    document.getElementById('slm-btn-toggle-inspector').onclick = toggleInspector;

    // Build Inspector HTML
    let sectionOptions = '';
    sections.forEach((sec, idx) => {
      sectionOptions += `<option value="${sec.id}">Section ${idx + 1}: ${sec.label || sec.section_type}</option>`;
    });

    let sectionCardsHtml = '';
    sections.forEach((sec, sIdx) => {
      const d = sec.data || {};
      const type = sec.section_type || 'generic';
      const fPrefix = `sec_${sec.id}`;

      let sectionFields = '';

      // Eyebrow field
      if (type === 'hero' || type === 'split' || d.eyebrow !== undefined) {
        sectionFields += `
          <div>
            <label style="font-size:11px; text-transform:uppercase; color:#94a3b8; font-weight:700; display:block; margin-bottom:4px;">Eyebrow / Badge</label>
            <input type="text" id="${fPrefix}-eyebrow" value="${d.eyebrow || ''}" style="width:100%; box-sizing:border-box; background:#090d16; border:1px solid rgba(255,255,255,0.12); color:#f8fafc; padding:7px 10px; border-radius:6px; font-size:12px;">
          </div>
        `;
      }

      // Main Title / Headline field
      sectionFields += `
        <div>
          <label style="font-size:11px; text-transform:uppercase; color:#94a3b8; font-weight:700; display:block; margin-bottom:4px;">Main Title / Headline</label>
          <input type="text" id="${fPrefix}-title" value="${(d.title || '').replace(/"/g, '&quot;')}" style="width:100%; box-sizing:border-box; background:#090d16; border:1px solid rgba(255,255,255,0.12); color:#f8fafc; padding:7px 10px; border-radius:6px; font-size:12px; font-weight:600;">
        </div>
      `;

      // Subtitle / Body Rich Text
      const initialRichText = d.body_html || d.subtitle || d.description || d.body || d.content || '';
      sectionFields += renderRichTextField(`${fPrefix}-desc`, 'Subtitle & Body Description', initialRichText);

      // Buttons
      if (type === 'hero' || type === 'cta_banner' || type === 'split') {
        const b1Text = d.btn1_text || (d.buttons && d.buttons[0] && d.buttons[0].label) || '';
        const b1Url = d.btn1_url || (d.buttons && d.buttons[0] && d.buttons[0].url) || '';
        const ctaText = d.cta_primary_text || d.button_text || d.cta_text || (d.buttons && d.buttons[1] && d.buttons[1].label) || '';
        const ctaUrl = d.cta_primary_url || d.button_url || d.cta_url || (d.buttons && d.buttons[1] && d.buttons[1].url) || '';

        sectionFields += `
          <div style="background:#090d16; padding:8px 10px; border-radius:6px; border:1px solid rgba(255,255,255,0.08); display:flex; flex-direction:column; gap:8px;">
            <div style="font-size:11px; text-transform:uppercase; color:#818cf8; font-weight:700;">Action Buttons</div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px;">
              <div>
                <label style="font-size:10px; color:#94a3b8;">Button 1 Label</label>
                <input type="text" id="${fPrefix}-btn1-text" value="${b1Text}" style="width:100%; box-sizing:border-box; background:#1e293b; border:1px solid rgba(255,255,255,0.1); color:#fff; padding:5px 8px; border-radius:4px; font-size:11px;">
              </div>
              <div>
                <label style="font-size:10px; color:#94a3b8;">Button 1 URL</label>
                <input type="text" id="${fPrefix}-btn1-url" value="${b1Url}" style="width:100%; box-sizing:border-box; background:#1e293b; border:1px solid rgba(255,255,255,0.1); color:#fff; padding:5px 8px; border-radius:4px; font-size:11px;">
              </div>
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px;">
              <div>
                <label style="font-size:10px; color:#94a3b8;">CTA Button 2 Label</label>
                <input type="text" id="${fPrefix}-cta-text" value="${ctaText}" style="width:100%; box-sizing:border-box; background:#1e293b; border:1px solid rgba(255,255,255,0.1); color:#fff; padding:5px 8px; border-radius:4px; font-size:11px;">
              </div>
              <div>
                <label style="font-size:10px; color:#94a3b8;">CTA Button 2 URL</label>
                <input type="text" id="${fPrefix}-cta-url" value="${ctaUrl}" style="width:100%; box-sizing:border-box; background:#1e293b; border:1px solid rgba(255,255,255,0.1); color:#fff; padding:5px 8px; border-radius:4px; font-size:11px;">
              </div>
            </div>
          </div>
        `;
      }

      // Media / Image URL
      if (d.dashboard_image || d.image_url || type === 'hero' || type === 'split') {
        const curImg = d.dashboard_image || d.image_url || '';
        sectionFields += `
          <div>
            <label style="font-size:11px; text-transform:uppercase; color:#94a3b8; font-weight:700; display:block; margin-bottom:4px;">Mockup / Illustration Image</label>
            <input type="text" id="${fPrefix}-image" value="${curImg}" style="width:100%; box-sizing:border-box; background:#090d16; border:1px solid rgba(255,255,255,0.12); color:#f8fafc; padding:7px 10px; border-radius:6px; font-size:11px;">
          </div>
        `;
      }

      // Cards if Card Grid
      if (type === 'card_grid' && Array.isArray(d.cards)) {
        sectionFields += `
          <div style="background:#090d16; padding:10px; border-radius:6px; border:1px solid rgba(255,255,255,0.08); display:flex; flex-direction:column; gap:8px;">
            <div style="font-size:11px; text-transform:uppercase; color:#818cf8; font-weight:700;">Cards in Grid (${d.cards.length})</div>
            ${d.cards.map((c, cIdx) => `
              <div style="background:#1e293b; padding:8px; border-radius:6px; display:flex; flex-direction:column; gap:4px;">
                <input type="text" id="${fPrefix}-card-${cIdx}-title" value="${(c.title || '').replace(/"/g, '&quot;')}" placeholder="Card Title" style="width:100%; box-sizing:border-box; background:#090d16; border:1px solid rgba(255,255,255,0.1); color:#fff; padding:4px 8px; border-radius:4px; font-size:11px; font-weight:600;">
                <textarea id="${fPrefix}-card-${cIdx}-desc" rows="2" placeholder="Card Description" style="width:100%; box-sizing:border-box; background:#090d16; border:1px solid rgba(255,255,255,0.1); color:#cbd5e1; padding:4px 8px; border-radius:4px; font-size:11px;">${c.description || ''}</textarea>
                <input type="text" id="${fPrefix}-card-${cIdx}-url" value="${c.url || ''}" placeholder="Card URL (e.g. /features/)" style="width:100%; box-sizing:border-box; background:#090d16; border:1px solid rgba(255,255,255,0.1); color:#cbd5e1; padding:4px 8px; border-radius:4px; font-size:10px;">
              </div>
            `).join('')}
          </div>
        `;
      }

      // Team Members Editor
      if (type === 'team' && Array.isArray(d.members)) {
        sectionFields += `
          <div style="background:#090d16; padding:10px; border-radius:6px; border:1px solid rgba(255,255,255,0.08); display:flex; flex-direction:column; gap:10px;">
            <div style="font-size:11px; text-transform:uppercase; color:#818cf8; font-weight:700;">Team Leaders & Members (${d.members.length})</div>
            ${d.members.map((m, mIdx) => `
              <div style="background:#1e293b; padding:10px; border-radius:6px; display:flex; flex-direction:column; gap:6px; border:1px solid rgba(255,255,255,0.08);">
                <div style="display:flex; align-items:center; gap:8px;">
                  <img src="${m.photo || '/wp-content/uploads/2023/03/s.png'}" style="width:28px; height:28px; border-radius:50%; object-fit:cover; border:1px solid rgba(255,255,255,0.2); background:#0b1120;" onerror="this.src='/wp-content/uploads/2023/03/s.png'">
                  <span style="font-size:11px; font-weight:700; color:#f8fafc;">#${mIdx + 1}: ${m.name || 'Member'}</span>
                </div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px;">
                  <div>
                    <label style="font-size:10px; color:#94a3b8; display:block; margin-bottom:2px;">Full Name</label>
                    <input type="text" id="${fPrefix}-member-${mIdx}-name" value="${(m.name || '').replace(/"/g, '&quot;')}" placeholder="Full Name" style="width:100%; box-sizing:border-box; background:#090d16; border:1px solid rgba(255,255,255,0.12); color:#fff; padding:4px 8px; border-radius:4px; font-size:11px; font-weight:600;">
                  </div>
                  <div>
                    <label style="font-size:10px; color:#94a3b8; display:block; margin-bottom:2px;">Role / Designation</label>
                    <input type="text" id="${fPrefix}-member-${mIdx}-role" value="${(m.role || '').replace(/"/g, '&quot;')}" placeholder="e.g. CEO" style="width:100%; box-sizing:border-box; background:#090d16; border:1px solid rgba(255,255,255,0.12); color:#fff; padding:4px 8px; border-radius:4px; font-size:11px;">
                  </div>
                </div>
                <div>
                  <label style="font-size:10px; color:#94a3b8; display:block; margin-bottom:2px;">Photo URL</label>
                  <input type="text" id="${fPrefix}-member-${mIdx}-photo" value="${m.photo || ''}" placeholder="/wp-content/uploads/..." style="width:100%; box-sizing:border-box; background:#090d16; border:1px solid rgba(255,255,255,0.12); color:#cbd5e1; padding:4px 8px; border-radius:4px; font-size:10px;">
                </div>
                <div>
                  <label style="font-size:10px; color:#94a3b8; display:block; margin-bottom:2px;">LinkedIn Profile URL</label>
                  <input type="text" id="${fPrefix}-member-${mIdx}-linkedin" value="${m.linkedin || ''}" placeholder="https://linkedin.com/in/..." style="width:100%; box-sizing:border-box; background:#090d16; border:1px solid rgba(255,255,255,0.12); color:#cbd5e1; padding:4px 8px; border-radius:4px; font-size:10px;">
                </div>
              </div>
            `).join('')}
          </div>
        `;
      }

      // Partner Logos Wall Editor
      if (type === 'logo_wall' && Array.isArray(d.logos)) {
        sectionFields += `
          <div style="background:#090d16; padding:10px; border-radius:6px; border:1px solid rgba(255,255,255,0.08); display:flex; flex-direction:column; gap:8px;">
            <div style="font-size:11px; text-transform:uppercase; color:#818cf8; font-weight:700;">Partner Logos (${d.logos.length})</div>
            ${d.logos.map((l, lIdx) => `
              <div style="background:#1e293b; padding:8px 10px; border-radius:6px; display:flex; flex-direction:column; gap:6px; border:1px solid rgba(255,255,255,0.06);">
                <div style="display:flex; align-items:center; gap:8px;">
                  <img src="${l.image_url || ''}" style="width:40px; height:20px; object-fit:contain; background:#ffffff; padding:2px; border-radius:3px;">
                  <span style="font-size:11px; font-weight:700; color:#f8fafc;">Logo #${lIdx + 1}: ${l.name || 'Partner'}</span>
                </div>
                <div>
                  <label style="font-size:10px; color:#94a3b8; display:block; margin-bottom:2px;">Logo Image URL</label>
                  <input type="text" id="${fPrefix}-logo-${lIdx}-img" value="${l.image_url || ''}" placeholder="Image URL" style="width:100%; box-sizing:border-box; background:#090d16; border:1px solid rgba(255,255,255,0.12); color:#cbd5e1; padding:4px 8px; border-radius:4px; font-size:10px;">
                </div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px;">
                  <div>
                    <label style="font-size:10px; color:#94a3b8; display:block; margin-bottom:2px;">Partner Name</label>
                    <input type="text" id="${fPrefix}-logo-${lIdx}-name" value="${(l.name || '').replace(/"/g, '&quot;')}" placeholder="e.g. Partner Name" style="width:100%; box-sizing:border-box; background:#090d16; border:1px solid rgba(255,255,255,0.12); color:#fff; padding:4px 8px; border-radius:4px; font-size:11px;">
                  </div>
                  <div>
                    <label style="font-size:10px; color:#94a3b8; display:block; margin-bottom:2px;">Partner Link (optional)</label>
                    <input type="text" id="${fPrefix}-logo-${lIdx}-url" value="${l.url || ''}" placeholder="https://..." style="width:100%; box-sizing:border-box; background:#090d16; border:1px solid rgba(255,255,255,0.12); color:#cbd5e1; padding:4px 8px; border-radius:4px; font-size:10px;">
                  </div>
                </div>
              </div>
            `).join('')}
          </div>
        `;
      }

      sectionCardsHtml += `
        <div id="slm-card-${sec.id}" class="slm-section-card" style="background:#131c31; border:1px solid rgba(255,255,255,0.08); border-radius:8px; overflow:hidden; transition:border 0.2s ease;">
          <div class="slm-accordion-header" onclick="toggleSectionAccordion('${sec.id}')" style="padding:10px 14px; background:#182238; border-bottom:1px solid rgba(255,255,255,0.06); display:flex; align-items:center; justify-content:space-between; cursor:pointer;">
            <div style="display:flex; align-items:center; gap:8px;">
              <span style="font-size:10px; font-weight:800; background:#334155; color:#cbd5e1; padding:2px 6px; border-radius:4px;">${sIdx + 1}</span>
              <span style="font-size:12px; font-weight:700; color:#f8fafc;">${sec.label || type}</span>
              <span style="font-size:9px; text-transform:uppercase; padding:1px 5px; border-radius:3px; background:rgba(99,102,241,0.2); color:#a5b4fc; border:1px solid rgba(99,102,241,0.4);">${type}</span>
            </div>
            <div style="display:flex; align-items:center; gap:6px;">
              <span id="slm-chevron-${sec.id}" style="color:#94a3b8; font-size:11px; transition:transform 0.2s;">▼</span>
            </div>
          </div>

          <div id="slm-body-${sec.id}" class="slm-accordion-body" style="padding:14px; display:flex; flex-direction:column; gap:12px;">
            ${sectionFields}
          </div>
        </div>
      `;
    });

    if (!sectionCardsHtml) {
      sectionCardsHtml = `
        <div style="background:#131c31; border:1px dashed rgba(255,255,255,0.18); border-radius:8px; padding:24px 16px; text-align:center; color:#94a3b8;">
          <div style="font-size:28px; margin-bottom:8px;">📄</div>
          <div style="font-size:13px; font-weight:700; color:#f8fafc; margin-bottom:6px;">No Sections Configured in Database</div>
          <p style="font-size:11px; margin:0; line-height:1.5; color:#94a3b8;">This page is active, but its section schema has not been populated in PostgreSQL yet.</p>
        </div>
      `;
    }

    inspector.innerHTML = `
      <!-- Inspector Header -->
      <div style="flex-shrink:0; padding:12px 16px; background:#0f172a; border-bottom:1px solid rgba(255,255,255,0.1); display:flex; align-items:center; justify-content:space-between;">
        <div>
          <h3 style="margin:0; font-size:13px; font-weight:800; color:#fff; display:flex; align-items:center; gap:6px;">
            <span>🎨</span> <span>VISUAL INSPECTOR</span>
          </h3>
          <p style="margin:2px 0 0; font-size:10px; color:#94a3b8;">Click any page element or pick from list</p>
        </div>
        <button id="slm-inspector-close-btn" style="background:none; border:none; color:#94a3b8; font-size:16px; cursor:pointer;" title="Close Inspector">✕</button>
      </div>

      <!-- Quick Section Jump -->
      <div style="flex-shrink:0; padding:8px 14px; background:#131d33; border-bottom:1px solid rgba(255,255,255,0.06);">
        <select id="slm-jump-section" onchange="jumpToSection(this.value)" style="width:100%; box-sizing:border-box; background:#090d16; color:#cbd5e1; border:1px solid rgba(255,255,255,0.15); border-radius:6px; padding:5px 8px; font-size:11px; outline:none; cursor:pointer;">
          <option value="">⚡ Jump to Section...</option>
          ${sectionOptions}
        </select>
      </div>

      <!-- Inspector Cards Scroll Area -->
      <div id="slm-inspector-scroll" style="display:block !important; flex:1 1 auto !important; min-height:0 !important; height:calc(100vh - 165px) !important; max-height:calc(100vh - 165px) !important; overflow-y:scroll !important; overflow-x:hidden !important; padding:12px !important; box-sizing:border-box !important; -webkit-overflow-scrolling:touch !important; overscroll-behavior:contain !important; touch-action:pan-y !important;">
        ${sectionCardsHtml}
      </div>

      <!-- Inspector Sticky Footer -->
      <div style="flex-shrink:0; padding:12px 14px; background:#0f172a; border-top:1px solid rgba(255,255,255,0.1); display:flex; gap:8px;">
        <button id="slm-insp-save-draft" style="flex:1; background:#1e293b; color:#fff; border:1px solid rgba(255,255,255,0.2); padding:8px 0; border-radius:6px; font-weight:700; cursor:pointer; font-size:11px;">
          💾 Save Draft
        </button>
        <button id="slm-insp-publish" style="flex:1; background:linear-gradient(135deg, #10b981 0%, #059669 100%); color:#fff; border:none; padding:8px 0; border-radius:6px; font-weight:700; cursor:pointer; font-size:11px; box-shadow:0 2px 10px rgba(16,185,129,0.3);">
          🚀 Publish Live
        </button>
      </div>
    `;

    const closeInspectorBtn = document.getElementById('slm-inspector-close-btn');
    if (closeInspectorBtn) {
      closeInspectorBtn.onclick = () => setInspectorOpen(false);
    }

    // Active Wheel & Scroll Isolation to prevent theme/page event suppression
    const scrollContainer = document.getElementById('slm-inspector-scroll');
    if (scrollContainer) {
      scrollContainer.addEventListener('wheel', function(e) {
        e.stopPropagation();
        const prev = scrollContainer.scrollTop;
        scrollContainer.scrollTop += e.deltaY;
        if (scrollContainer.scrollTop !== prev) {
          e.preventDefault();
        }
      }, { passive: false });

      inspector.addEventListener('wheel', function(e) {
        if (!e.target.closest('#slm-inspector-scroll')) {
          e.stopPropagation();
          scrollContainer.scrollTop += e.deltaY;
          e.preventDefault();
        }
      }, { passive: false });
    }

    // Global Accordion Helpers
    window.toggleSectionAccordion = function(secId) {
      const body = document.getElementById(`slm-body-${secId}`);
      const chevron = document.getElementById(`slm-chevron-${secId}`);
      if (body) {
        const isHidden = body.style.display === 'none';
        body.style.display = isHidden ? 'flex' : 'none';
        if (chevron) chevron.style.transform = isHidden ? 'rotate(0deg)' : 'rotate(-90deg)';
      }
    };

    window.jumpToSection = function(secId) {
      if (!secId) return;
      // Scroll canvas
      const targetCanvasEl = document.querySelector(`[data-slm-sec-id="${secId}"]`);
      if (targetCanvasEl) {
        document.querySelectorAll('[data-slm-sec-id]').forEach(el => el.classList.remove('slm-sec-selected'));
        targetCanvasEl.classList.add('slm-sec-selected');
        targetCanvasEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }

      // Open inspector card
      const card = document.getElementById(`slm-card-${secId}`);
      if (card) {
        const body = document.getElementById(`slm-body-${secId}`);
        const chevron = document.getElementById(`slm-chevron-${secId}`);
        if (body) body.style.display = 'flex';
        if (chevron) chevron.style.transform = 'rotate(0deg)';
        card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        card.style.borderColor = '#6366f1';
        setTimeout(() => { card.style.borderColor = 'rgba(255,255,255,0.08)'; }, 1500);
      }
    };

    // 4. Canvas Click-to-Select Listener
    document.querySelectorAll('[data-slm-sec-id]').forEach(el => {
      el.addEventListener('click', function(e) {
        // Allow clicking inputs inside the inspector without trigger
        if (e.target.closest('#slm-studio-inspector') || e.target.closest('#slm-studio-topbar')) return;

        // If in studio mode, prevent normal anchor link redirects to allow selecting
        if (e.target.closest('a')) {
          e.preventDefault();
        }

        const secId = el.getAttribute('data-slm-sec-id');
        if (secId) {
          // Open inspector if closed
          if (!isInspectorOpen) setInspectorOpen(true);
          jumpToSection(secId);
          showStudioToast(`Focused: ${el.getAttribute('data-slm-sec-idx')} on canvas`, 'success');
        }
      });
    });

    // 5. Save & Publish Actions
    const executeSaveOrPublish = async (isPublish) => {
      const updatedPayload = [];

      sections.forEach((sec) => {
        const d = { ...sec.data };
        const type = sec.section_type || 'generic';
        const fPrefix = `sec_${sec.id}`;

        if (document.getElementById(`${fPrefix}-eyebrow`)) {
          d.eyebrow = document.getElementById(`${fPrefix}-eyebrow`).value;
        }
        if (document.getElementById(`${fPrefix}-title`)) {
          d.title = document.getElementById(`${fPrefix}-title`).value;
        }

        const richDesc = getRichFieldValue(`${fPrefix}-desc`);
        if (richDesc) {
          d.subtitle = richDesc;
          d.description = richDesc;
          d.body = richDesc;
          d.body_html = richDesc;
        }

        if (document.getElementById(`${fPrefix}-btn1-text`)) {
          const b1Text = document.getElementById(`${fPrefix}-btn1-text`).value;
          const b1Url = document.getElementById(`${fPrefix}-btn1-url`).value;
          d.btn1_text = b1Text;
          d.btn1_url = b1Url;
          if (!d.buttons) d.buttons = [{}, {}];
          d.buttons[0] = { label: b1Text, url: b1Url, style: 'primary' };
        }
        if (document.getElementById(`${fPrefix}-cta-text`)) {
          const ctaText = document.getElementById(`${fPrefix}-cta-text`).value;
          const ctaUrl = document.getElementById(`${fPrefix}-cta-url`)?.value || 'https://salesleadmachine.uk/login';
          d.cta_primary_text = ctaText;
          d.button_text = ctaText;
          d.cta_text = ctaText;
          d.cta_label = ctaText;
          d.cta_primary_url = ctaUrl;
          d.button_url = ctaUrl;
          d.cta_url = ctaUrl;
          if (d.buttons && d.buttons.length >= 2) {
            d.buttons[1] = { label: ctaText, url: ctaUrl, style: 'outline' };
          }
        }
        if (document.getElementById(`${fPrefix}-image`)) {
          const img = document.getElementById(`${fPrefix}-image`).value;
          d.dashboard_image = img;
          d.image_url = img;
        }

        if (type === 'card_grid' && Array.isArray(d.cards)) {
          d.cards.forEach((c, cIdx) => {
            const cardTitleEl = document.getElementById(`${fPrefix}-card-${cIdx}-title`);
            const cardUrlEl = document.getElementById(`${fPrefix}-card-${cIdx}-url`);
            const cardDescEl = document.getElementById(`${fPrefix}-card-${cIdx}-desc`);
            if (cardTitleEl) c.title = cardTitleEl.value;
            if (cardUrlEl) c.url = cardUrlEl.value;
            if (cardDescEl) c.description = cardDescEl.value;
          });
        }

        if (type === 'team' && Array.isArray(d.members)) {
          d.members.forEach((m, mIdx) => {
            const nameEl = document.getElementById(`${fPrefix}-member-${mIdx}-name`);
            const roleEl = document.getElementById(`${fPrefix}-member-${mIdx}-role`);
            const photoEl = document.getElementById(`${fPrefix}-member-${mIdx}-photo`);
            const linkEl = document.getElementById(`${fPrefix}-member-${mIdx}-linkedin`);
            if (nameEl) m.name = nameEl.value;
            if (roleEl) m.role = roleEl.value;
            if (photoEl) m.photo = photoEl.value;
            if (linkEl) m.linkedin = linkEl.value;
          });
        }

        if (type === 'logo_wall' && Array.isArray(d.logos)) {
          d.logos.forEach((l, lIdx) => {
            const imgEl = document.getElementById(`${fPrefix}-logo-${lIdx}-img`);
            const nameEl = document.getElementById(`${fPrefix}-logo-${lIdx}-name`);
            const urlEl = document.getElementById(`${fPrefix}-logo-${lIdx}-url`);
            if (imgEl) l.image_url = imgEl.value;
            if (nameEl) l.name = nameEl.value;
            if (urlEl) l.url = urlEl.value;
          });
        }

        updatedPayload.push({
          id: sec.id,
          label: sec.label,
          is_visible: sec.is_visible,
          data: d
        });
      });

      try {
        if (!pageId) throw new Error('No page ID');

        const res = await fetch(`/api/admin/pages/${pageId}/bulk-sections`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            sections: updatedPayload,
            publish: isPublish
          })
        });

        const resJson = await res.json();
        if (resJson.success) {
          const pill = document.getElementById('slm-status-pill');
          const dot = document.getElementById('slm-status-dot');
          const discardBtn = document.getElementById('slm-btn-discard');

          if (isPublish) {
            showStudioToast('🚀 All changes published live to website!', 'success');
            if (pill) {
              pill.textContent = '● Live In Sync';
              pill.style.background = 'rgba(16,185,129,0.2)';
              pill.style.color = '#34d399';
              pill.style.border = '1px solid rgba(16,185,129,0.4)';
            }
            if (dot) {
              dot.style.background = '#10b981';
              dot.style.boxShadow = '0 0 8px #10b981';
            }
            if (discardBtn) discardBtn.style.display = 'none';
          } else {
            showStudioToast('💾 Draft saved successfully!', 'draft');
            if (pill) {
              pill.textContent = '● Draft Changes Pending';
              pill.style.background = 'rgba(245,158,11,0.2)';
              pill.style.color = '#fbbf24';
              pill.style.border = '1px solid rgba(245,158,11,0.4)';
            }
            if (dot) {
              dot.style.background = '#f59e0b';
              dot.style.boxShadow = '0 0 8px #f59e0b';
            }
            if (discardBtn) discardBtn.style.display = 'inline-block';
          }

          // Live update canvas without full reload
          setTimeout(() => syncPageSections(), 300);
        } else {
          showStudioToast('Failed to save to database', 'error');
        }
      } catch (err) {
        showStudioToast('Connection error while saving', 'error');
      }
    };

    document.getElementById('slm-btn-save-draft').onclick = () => executeSaveOrPublish(false);
    document.getElementById('slm-insp-save-draft').onclick = () => executeSaveOrPublish(false);
    document.getElementById('slm-btn-publish').onclick = () => executeSaveOrPublish(true);
    document.getElementById('slm-insp-publish').onclick = () => executeSaveOrPublish(true);

    // Discard Draft Handler
    const discardBtn = document.getElementById('slm-btn-discard');
    if (discardBtn) {
      discardBtn.onclick = async () => {
        if (!confirm('Discard all pending draft edits and restore live content?')) return;
        try {
          const res = await fetch(`/api/admin/pages/${pageId}/discard-draft`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
          });
          const resJson = await res.json();
          if (resJson.success) {
            showStudioToast('Draft discarded. Restored live content.', 'success');
            setTimeout(() => window.location.reload(), 500);
          }
        } catch (e) {
          showStudioToast('Failed to discard draft', 'error');
        }
      };
    }

    // Exit Button Handler
    document.getElementById('slm-btn-exit').onclick = () => {
      localStorage.removeItem('slm_auth_token');
      window.location.href = window.location.pathname;
    };
  }



  // 7. Bootstrap when DOM is ready
  function initHydration() {
    syncCompanySettings();
    syncTeamMembers();
    syncCtaButtons();
    syncPageSections();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initHydration);
  } else {
    initHydration();
  }
})();
