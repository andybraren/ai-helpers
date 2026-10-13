(function () {
  const deck = JSON.parse(document.getElementById('deck-data').textContent);
  const slides = Array.isArray(deck.slides) ? deck.slides : [];
  const viewport = document.getElementById('viewport');
  const title = document.getElementById('deck-title');
  const count = document.getElementById('count');
  const notes = document.getElementById('notes');
  const notesBody = document.getElementById('notes-body');
  const notesToggle = document.getElementById('notes-toggle');
  const presentButton = document.getElementById('present');
  const progress = document.getElementById('progress');
  const banner = document.getElementById('banner');
  let index = initialIndex();

  title.textContent = deck.title || 'Slide deck';
  document.title = deck.title || 'Slide deck';
  renderBanner();
  slides.forEach((slide, slideIndex) => viewport.appendChild(renderSlide(slide, slideIndex)));
  if (slides.length === 0) {
    viewport.appendChild(Object.assign(document.createElement('p'), {
      textContent: 'This deck has no slides.',
      style: 'padding: 48px; color: #151515;'
    }));
  }

  document.getElementById('prev').addEventListener('click', () => go(index - 1));
  document.getElementById('next').addEventListener('click', () => go(index + 1));
  notesToggle.addEventListener('click', toggleNotes);
  presentButton.addEventListener('click', togglePresent);
  window.addEventListener('resize', fit);
  window.addEventListener('hashchange', () => go(initialIndex(), { updateHash: false }));
  window.addEventListener('keydown', onKey);
  viewport.addEventListener('click', (event) => {
    if (event.target.closest('a, button')) return;
    const rect = viewport.getBoundingClientRect();
    go(index + (event.clientX - rect.left > rect.width / 2 ? 1 : -1));
  });

  go(index, { updateHash: false });
  fit();

  function initialIndex() {
    const hashed = Number(location.hash.replace('#', ''));
    if (!Number.isInteger(hashed) || hashed < 1) return 0;
    return Math.min(slides.length - 1, hashed - 1);
  }

  function go(nextIndex, { updateHash = true } = {}) {
    if (slides.length === 0) return;
    index = Math.max(0, Math.min(slides.length - 1, nextIndex));
    viewport.querySelectorAll('.slide').forEach((slide, slideIndex) => {
      slide.classList.toggle('is-active', slideIndex === index);
      slide.hidden = slideIndex !== index;
    });
    count.textContent = `${index + 1} / ${slides.length}`;
    progress.style.transform = `scaleX(${(index + 1) / slides.length})`;
    notesBody.textContent = slides[index].notes || 'No speaker notes for this slide.';
    if (updateHash) history.replaceState(null, '', `#${index + 1}`);
  }

  function toggleNotes() {
    const open = notes.hidden;
    notes.hidden = !open;
    notesToggle.setAttribute('aria-pressed', open ? 'true' : 'false');
    fit();
  }

  function togglePresent() {
    const on = !document.body.classList.contains('is-present');
    document.body.classList.toggle('is-present', on);
    presentButton.setAttribute('aria-pressed', on ? 'true' : 'false');
    fit();
  }

  function onKey(event) {
    const key = event.key;
    if (['ArrowRight', 'ArrowDown', 'PageDown', ' '].includes(key)) {
      event.preventDefault();
      go(index + 1);
    } else if (['ArrowLeft', 'ArrowUp', 'PageUp'].includes(key)) {
      event.preventDefault();
      go(index - 1);
    } else if (key === 'Home') go(0);
    else if (key === 'End') go(slides.length - 1);
    else if (key === 's' || key === 'S') toggleNotes();
    else if (key === 'f' || key === 'F') togglePresent();
    else if (key === 'Escape') {
      document.body.classList.remove('is-present');
      presentButton.setAttribute('aria-pressed', 'false');
      fit();
    }
  }

  function fit() {
    const stage = document.querySelector('.stage');
    const scale = Math.min(stage.clientWidth / 1920, stage.clientHeight / 1080);
    viewport.style.transform = `translate(-50%, -50%) scale(${scale || 1})`;
  }

  function renderBanner() {
    const url = safeUrl(deck.canonical && deck.canonical.url);
    if (!url) return;
    const label = deck.canonical.target === 'figma-slides' ? 'Figma Slides' : 'Google Slides';
    banner.hidden = false;
    banner.textContent = '';
    const stale = deck.status !== 'published';
    banner.append(stale
      ? 'This local deck has changed since it was shared. Last shared copy: '
      : 'Shared copy: ');
    const link = document.createElement('a');
    link.href = url;
    link.textContent = label;
    banner.append(link);
  }

  function renderSlide(slide, slideIndex) {
    const section = document.createElement('section');
    section.className = `slide slide-${slide.type || 'content'}`;
    section.hidden = true;
    section.setAttribute('aria-label', `Slide ${slideIndex + 1} of ${slides.length}: ${slide.heading || slide.type}`);
    const inner = document.createElement('div');
    inner.className = 'slide-inner';
    section.appendChild(inner);

    if (slide.type === 'split') {
      const copy = document.createElement('div');
      copy.className = 'copy-col';
      appendHeading(copy, slide);
      copy.appendChild(renderBlocks(slide.blocks));
      inner.append(copy, renderMedia(slide.media));
      return section;
    }

    if (slide.type === 'quote') {
      appendKicker(inner, slide.kicker);
      const quote = slide.blocks.find((block) => block.type === 'quote');
      const quoteText = document.createElement('blockquote');
      quoteText.innerHTML = inline(quote ? quote.text : slide.heading);
      inner.appendChild(quoteText);
      if (quote && slide.heading) {
        const attribution = document.createElement('p');
        attribution.className = 'attribution';
        attribution.innerHTML = inline(slide.heading);
        inner.appendChild(attribution);
      }
      return section;
    }

    appendHeading(inner, slide, { bar: slide.type === 'title' || slide.type === 'closing' || slide.type === 'section' });
    if (slide.blocks.length > 0) inner.appendChild(renderBlocks(slide.blocks));
    return section;
  }

  function appendHeading(parent, slide, { bar = false } = {}) {
    appendKicker(parent, slide.kicker);
    if (bar) {
      const accent = document.createElement('span');
      accent.className = 'accent-bar';
      accent.setAttribute('aria-hidden', 'true');
      parent.appendChild(accent);
    }
    if (slide.heading) parent.appendChild(textEl('h1', slide.heading));
    if (slide.subheading) parent.appendChild(textEl('h2', slide.subheading));
  }

  function appendKicker(parent, kicker) {
    if (kicker) parent.appendChild(textEl('p', kicker, 'kicker'));
  }

  function renderBlocks(blocks) {
    const copy = document.createElement('div');
    copy.className = 'slide-copy';
    for (const block of blocks) {
      if (block.type === 'h3') copy.appendChild(textEl('h3', block.text));
      else if (block.type === 'paragraph') copy.appendChild(textEl('p', block.text));
      else if (block.type === 'quote') copy.appendChild(textEl('blockquote', block.text));
      else if (block.type === 'bullets') {
        const list = document.createElement('ul');
        for (const item of block.items) list.appendChild(textEl('li', item));
        copy.appendChild(list);
      } else if (block.type === 'code') {
        const pre = document.createElement('pre');
        const code = document.createElement('code');
        code.textContent = block.text;
        pre.appendChild(code);
        copy.appendChild(pre);
      } else if (block.type === 'image') {
        copy.appendChild(renderImage(block.src, block.alt, 'inline-image'));
      }
    }
    return copy;
  }

  function renderMedia(media) {
    const figure = document.createElement('figure');
    figure.className = 'media';
    if (media && media.src) figure.appendChild(renderImage(media.src, ''));
    else figure.textContent = 'Add a screenshot in assets/';
    return figure;
  }

  function renderImage(src, alt, className) {
    const image = document.createElement('img');
    image.src = src;
    image.alt = alt || '';
    if (className) image.className = className;
    image.addEventListener('error', () => {
      const fallback = document.createElement('p');
      fallback.textContent = src;
      image.replaceWith(fallback);
    });
    return image;
  }

  function textEl(tag, value, className) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    node.innerHTML = inline(value);
    return node;
  }

  function inline(value) {
    return escapeHtml(value)
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, '<a href="$2">$1</a>');
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function safeUrl(url) {
    try {
      const parsed = new URL(url);
      return parsed.protocol === 'https:' ? parsed.href : '';
    } catch {
      return '';
    }
  }
}());
