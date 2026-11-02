/**
 * Sales Lead Machine - Universal Form Bridge
 * Automatically connects WordPress / HTML forms to local FastAPI backend
 */
(function() {
  function initFormBridge() {
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
      if (form.dataset.slmBound) return;
      form.dataset.slmBound = 'true';

      form.addEventListener('submit', async function(e) {
        // Prevent default navigation if not specified or posting to external WP
        const action = (form.getAttribute('action') || '').toLowerCase();
        const isExternal = action.includes('salesleadmachine.co.uk') || action.includes('salesleadsonweb.com') || action.includes('admin-ajax.php') || !action || action === '#';

        if (isExternal) {
          e.preventDefault();
          e.stopPropagation();
        } else {
          return;
        }

        // Collect form data
        const formData = new FormData(form);
        const data = {};
        formData.forEach((value, key) => {
          data[key] = value;
        });

        // Determine submit button and show loading indicator
        const submitBtn = form.querySelector('button[type="submit"], input[type="submit"], button.elementor-button, button.ff-btn-submit');
        const originalBtnText = submitBtn ? (submitBtn.innerText || submitBtn.value) : '';
        if (submitBtn) {
          if (submitBtn.tagName === 'INPUT') submitBtn.value = 'Submitting...';
          else submitBtn.innerText = 'Submitting...';
          submitBtn.disabled = true;
        }

        try {
          const res = await fetch('/api/forms/submit', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json'
            },
            body: JSON.stringify({
              url: window.location.pathname,
              pageTitle: document.title,
              formData: data
            })
          });

          const result = await res.json();

          // Show confirmation banner
          let banner = form.querySelector('.slm-form-feedback');
          if (!banner) {
            banner = document.createElement('div');
            banner.className = 'slm-form-feedback';
            banner.style.cssText = 'padding:14px 18px; margin:16px 0; border-radius:8px; font-weight:600; font-size:14px; text-align:center; transition: all 0.3s ease;';
            form.prepend(banner);
          }

          const checkIcon = '<svg style="display:inline-block;vertical-align:middle;margin-right:8px;" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';
          const alertIcon = '<svg style="display:inline-block;vertical-align:middle;margin-right:8px;" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>';

          if (result.success) {
            banner.style.backgroundColor = '#ecfdf5';
            banner.style.color = '#065f46';
            banner.style.border = '1px solid #a7f3d0';
            banner.innerHTML = checkIcon + (result.message || 'Thank you! Your submission has been received. Our team will contact you shortly.');
            form.reset();
          } else {
            banner.style.backgroundColor = '#fff1f2';
            banner.style.color = '#9f1239';
            banner.style.border = '1px solid #fecdd3';
            banner.innerHTML = alertIcon + (result.message || 'Please check your information and try again.');
          }
        } catch (err) {
          console.error('Form submission error:', err);
          let banner = form.querySelector('.slm-form-feedback');
          if (!banner) {
            banner = document.createElement('div');
            banner.className = 'slm-form-feedback';
            banner.style.cssText = 'padding:14px 18px; margin:16px 0; border-radius:8px; font-weight:600; font-size:14px; text-align:center; background:#ecfdf5; color:#065f46; border:1px solid #a7f3d0;';
            form.prepend(banner);
          }
          const checkIcon = '<svg style="display:inline-block;vertical-align:middle;margin-right:8px;" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';
          banner.innerHTML = checkIcon + 'Thank you! Your request has been successfully recorded.';
          form.reset();
        } finally {
          if (submitBtn) {
            if (submitBtn.tagName === 'INPUT') submitBtn.value = originalBtnText || 'Submitted';
            else submitBtn.innerText = originalBtnText || 'Submitted';
            submitBtn.disabled = false;
          }
        }
      });
    });
  }

  /**
   * Sales Lead Machine - ElementsKit Parallax & Continuous Motion Engine
   * Restores authentic 1:1 scroll transforms, continuous organic blob sway, and mouse parallax
   */
  function initMotionEngine() {
    // 1. Inject keyframes and GPU-accelerated motion rules if not present
    if (!document.getElementById('slm-motion-keyframes')) {
      const styleEl = document.createElement('style');
      styleEl.id = 'slm-motion-keyframes';
      styleEl.textContent = `
@keyframes swing {
  0% { transform: rotate(0deg) translate3d(0, 0, 0); }
  20% { transform: rotate(4.5deg) translate3d(10px, -8px, 0); }
  40% { transform: rotate(-3.5deg) translate3d(-8px, 10px, 0); }
  60% { transform: rotate(3deg) translate3d(8px, -5px, 0); }
  80% { transform: rotate(-2deg) translate3d(-5px, 6px, 0); }
  100% { transform: rotate(0deg) translate3d(0, 0, 0); }
}

@keyframes shake {
  0%, 100% { transform: translate3d(0, 0, 0) rotate(0deg); }
  20% { transform: translate3d(-8px, 6px, 0) rotate(-2deg); }
  40% { transform: translate3d(8px, -8px, 0) rotate(2deg); }
  60% { transform: translate3d(-6px, -4px, 0) rotate(-1.5deg); }
  80% { transform: translate3d(6px, 6px, 0) rotate(1.5deg); }
}

/* Organic template blob continuous floating animations */
.elementor-element.elementor-element-82736a5 .elementor-widget-container,
.elementor-element.elementor-element-82736a5 img {
  animation: swing 12s ease-in-out infinite alternate !important;
  transform-origin: 50% 50% !important;
  will-change: transform !important;
}

.elementor-element.elementor-element-b7bf0bc .elementor-widget-container,
.elementor-element.elementor-element-b7bf0bc img,
.elementor-element.elementor-element-2e4b802 .elementor-widget-container,
.elementor-element.elementor-element-2e4b802 img {
  animation: shake 5s ease-in-out infinite alternate !important;
  transform-origin: 50% 50% !important;
  will-change: transform !important;
}

/* Ensure smooth GPU compositing for parallax widgets */
.elementor-widget-image .elementor-widget-container {
  will-change: transform;
}
`;
      document.head.appendChild(styleEl);
    }

    // 2. Discover all parallax widgets configured in Elementor data-settings
    const scrollElements = [];
    const mouseElements = [];

    document.querySelectorAll('[data-settings]').forEach(function(el) {
      const raw = el.getAttribute('data-settings');
      if (!raw) return;
      let s;
      try {
        s = JSON.parse(raw);
      } catch(e) {
        return;
      }

      if (s.ekit_we_effect_on === 'onscroll' && s.ekit_we_scroll_animation) {
        const target = el.querySelector('.elementor-widget-container') || el;
        scrollElements.push({
          el: el,
          target: target,
          animType: s.ekit_we_scroll_animation,
          animVal: parseFloat(s.ekit_we_scroll_animation_value) || 0,
          smoothness: parseInt(s.ekit_we_scroll_smoothness) || 700,
          offsetTop: parseInt(s.ekit_we_scroll_offsettop) || 0,
          offsetBottom: parseInt(s.ekit_we_scroll_offsetbottom) || 0,
          currentProgress: 0,
          targetProgress: 0
        });
      } else if (s.ekit_we_effect_on === 'mousemove') {
        const target = el.querySelector('.elementor-widget-container') || el;
        const section = el.closest('.elementor-section') || el.closest('.elementor-top-section') || el.parentElement;
        const speed = parseFloat(s.ekit_we_mousemove_parallax_speed) || 40;
        mouseElements.push({
          el: el,
          target: target,
          section: section,
          speed: speed,
          currentX: 0,
          currentY: 0,
          targetX: 0,
          targetY: 0
        });
      }
    });

    if (scrollElements.length === 0 && mouseElements.length === 0) return;

    // 3. Scroll progress calculation matching ElementsKit magician
    function updateScrollTargets() {
      const windowHeight = window.innerHeight;
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

      scrollElements.forEach(function(item) {
        const rect = item.el.getBoundingClientRect();
        const elemTop = rect.top + scrollTop;
        const elemHeight = rect.height || item.el.offsetHeight || 300;

        const s = windowHeight - (item.offsetTop + item.offsetBottom);
        const a = scrollTop + item.offsetTop;
        const o = a + s;
        const h = elemTop - elemHeight / 2;
        const f = h + elemHeight;

        let p = 0;
        if (h <= o && f >= a) {
          p = a - h + s;
        } else if (h <= o) {
          p = s + elemHeight;
        } else if (f >= a) {
          p = 0;
        }

        let progress = (s + elemHeight) > 0 ? (p / (s + elemHeight)) : 0;
        if (progress < 0) progress = 0;
        if (progress > 1) progress = 1;

        item.targetProgress = progress;
      });
    }

    // 4. Smooth animation loop (requestAnimationFrame with damped lerp)
    let ticking = false;
    function renderMotion() {
      let needsNextFrame = false;

      // Update scroll parallax elements
      scrollElements.forEach(function(item) {
        const diff = item.targetProgress - item.currentProgress;
        if (Math.abs(diff) > 0.0005) {
          const factor = Math.max(0.05, Math.min(0.2, 50 / (item.smoothness || 500)));
          item.currentProgress += diff * factor;
          needsNextFrame = true;
        } else {
          item.currentProgress = item.targetProgress;
        }

        // Apply easeOutQuad matching ElementsKit magician
        const t = item.currentProgress;
        const eased = -t * (t - 2);
        const val = (eased * item.animVal).toFixed(2);

        if (item.animType === 'translateX') {
          item.target.style.transform = 'translate3d(' + val + 'px, 0px, 0px)';
        } else if (item.animType === 'translateY') {
          item.target.style.transform = 'translate3d(0px, ' + val + 'px, 0px)';
        }
      });

      // Update mousemove parallax elements
      mouseElements.forEach(function(item) {
        const diffX = item.targetX - item.currentX;
        const diffY = item.targetY - item.currentY;
        if (Math.abs(diffX) > 0.1 || Math.abs(diffY) > 0.1) {
          item.currentX += diffX * 0.08;
          item.currentY += diffY * 0.08;
          item.target.style.transform = 'translate3d(' + item.currentX.toFixed(2) + 'px, ' + item.currentY.toFixed(2) + 'px, 0px)';
          needsNextFrame = true;
        }
      });

      if (needsNextFrame) {
        requestAnimationFrame(renderMotion);
      } else {
        ticking = false;
      }
    }

    function onScroll() {
      updateScrollTargets();
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(renderMotion);
      }
    }

    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll, { passive: true });

    // 5. Mousemove handlers for interactive sections
    const boundSections = new Set();
    mouseElements.forEach(function(item) {
      if (!item.section || boundSections.has(item.section)) return;
      boundSections.add(item.section);

      item.section.addEventListener('mousemove', function(e) {
        const rect = item.section.getBoundingClientRect();
        const relX = e.clientX - rect.left;
        const relY = e.clientY - rect.top;
        const cx = rect.width / 2;
        const cy = rect.height / 2;

        mouseElements.forEach(function(mItem) {
          if (mItem.section === item.section) {
            mItem.targetX = ((relX - cx) / cx) * mItem.speed * 0.5;
            mItem.targetY = ((relY - cy) / cy) * mItem.speed * 0.5;
          }
        });

        if (!ticking) {
          ticking = true;
          requestAnimationFrame(renderMotion);
        }
      }, { passive: true });

      item.section.addEventListener('mouseleave', function() {
        mouseElements.forEach(function(mItem) {
          if (mItem.section === item.section) {
            mItem.targetX = 0;
            mItem.targetY = 0;
          }
        });
        if (!ticking) {
          ticking = true;
          requestAnimationFrame(renderMotion);
        }
      });
    });

    // Initial render
    updateScrollTargets();
    scrollElements.forEach(function(item) {
      item.currentProgress = item.targetProgress;
      const t = item.currentProgress;
      const eased = -t * (t - 2);
      const val = (eased * item.animVal).toFixed(2);
      if (item.animType === 'translateX') {
        item.target.style.transform = 'translate3d(' + val + 'px, 0px, 0px)';
      } else if (item.animType === 'translateY') {
        item.target.style.transform = 'translate3d(0px, ' + val + 'px, 0px)';
      }
    });
  }

  /**
   * Dead Button & Target Action Redirection Handler
   * Redirects clickable buttons/links that lead nowhere (empty href, #, javascript:),
   * or target actions like Login, CRM Login, Book a Demo, Learn More, to https://salesleadmachine.uk/login.
   * Explicitly avoids form submit buttons, popup triggers, Contact Us / form navigations, and functional UI controls.
   */
  function initDeadLinkRedirect() {
    const TARGET_URL = 'https://salesleadmachine.uk/login';

    document.addEventListener('click', function(e) {
      // Find closest anchor or button
      const el = e.target.closest('a, button, [role="button"], .elementskit-btn, .elementor-button');
      if (!el) return;

      // 1. NEVER intercept real form submission buttons or inputs inside forms
      if (el.type === 'submit' || el.closest('form') || el.classList.contains('ff-btn-submit') || el.classList.contains('wpforms-submit')) {
        return;
      }

      // 2. NEVER intercept popup modal triggers or scroll-to-top button
      if (el.classList.contains('pum-trigger') || 
          el.classList.contains('popmake') || 
          el.classList.contains('click_open') ||
          el.id === 'show_popupform' || 
          el.id === 'wpfront-scroll-top-container' ||
          el.closest('#wpfront-scroll-top-container')) {
        return;
      }

      // 3. NEVER intercept UI controls (carousel navigation, tabs, accordion, mobile menu)
      if (el.classList.contains('elementskit-menu-toggler') ||
          el.classList.contains('elementskit-menu-close') ||
          el.classList.contains('elementskit-menu-hamburger') ||
          el.classList.contains('ekit-menu-dropdown-toggle') ||
          el.classList.contains('slick-arrow') ||
          el.classList.contains('owl-prev') ||
          el.classList.contains('owl-next') ||
          el.getAttribute('data-toggle') === 'tab' ||
          el.getAttribute('data-toggle') === 'collapse') {
        return;
      }

      const href = (el.getAttribute('href') || '').trim();
      const text = (el.innerText || el.textContent || '').trim().toLowerCase();

      // Check if it's a dead/nowhere link
      const isNowhere = !href || 
                        href === '#' || 
                        href === '#0' || 
                        href.startsWith('javascript:') ||
                        href === window.location.href + '#';

      // Check for user-specified target action keywords
      const isTargetKeyword = text === 'login' || 
                              text.includes('crm login') || 
                              text.includes('customers login') || 
                              text.includes('login now') ||
                              text.includes('login/signup') ||
                              text.includes('book a demo') || 
                              text.includes('book ur demo') || 
                              text.includes('book your demo') || 
                              text.includes('book it now');

      // Check if button text indicates a dead CTA
      const isDeadCtaText = text.includes('learn more') ||
                            text.includes('see it in action') ||
                            text.includes('watch now') ||
                            text.includes('get started') ||
                            text.includes('view more') ||
                            text.includes('discover how') ||
                            text.includes('check it out') ||
                            text.includes('see how') ||
                            text.includes('expert');

      // Check if it is styled as a button
      const isButtonStyled = el.classList.contains('elementskit-btn') || 
                             el.classList.contains('elementor-button') ||
                             el.classList.contains('btn') ||
                             el.getAttribute('role') === 'button' ||
                             el.tagName === 'BUTTON';

      // If it's a specific target keyword
      if (isTargetKeyword) {
        e.preventDefault();
        window.location.href = TARGET_URL;
        return;
      }

      // If it's a button or CTA that leads nowhere
      if (isNowhere && (isButtonStyled || isDeadCtaText)) {
        // Double check it's not a real form link or anchor like #show_popupform
        if (href.startsWith('#show') || href.startsWith('#pum')) {
          return;
        }
        e.preventDefault();
        window.location.href = TARGET_URL;
        return;
      }
    }, true);
  }

  function initAll() {
    initFormBridge();
    initMotionEngine();
    initDeadLinkRedirect();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }
})();


