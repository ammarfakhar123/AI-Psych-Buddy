// Chat page: sends messages with fetch() and renders replies. Uses textContent (never innerHTML
// with user data) to avoid XSS.
(function () {
  var form = document.getElementById('chatForm');
  var input = document.getElementById('chatInput');
  var box = document.getElementById('chatMessages');
  var sendBtn = document.getElementById('sendBtn');
  var strip = document.getElementById('suggestionStrip');
  var titleEl = document.getElementById('chatTitle');

  function csrfToken() {
    var match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
  }

  function scrollDown() { box.scrollTop = box.scrollHeight; }

  function addBubble(text, kind, extra) {
    extra = extra || {};
    var bubble = document.createElement('div');
    bubble.className = 'bubble ' + kind + (extra.crisis ? ' crisis' : '');
    var body = document.createElement('div');
    renderText(body, text);
    bubble.appendChild(body);
    if (extra.sources && extra.sources.length) {
      var wrap = document.createElement('div');
      extra.sources.forEach(function (s) {
        var chip = document.createElement('span');
        chip.className = 'source-chip';
        chip.textContent = '\u{1F4D6} ' + s;
        wrap.appendChild(chip);
      });
      bubble.appendChild(wrap);
    }
    box.appendChild(bubble);
    scrollDown();
    return bubble;
  }

  // Render **bold**, bullets and line breaks safely using DOM nodes.
  function renderText(container, text) {
    text.split('\n').forEach(function (line, i) {
      if (i > 0) { container.appendChild(document.createElement('br')); }
      line.split(/(\*\*[^*]+\*\*)/).forEach(function (part) {
        if (/^\*\*[^*]+\*\*$/.test(part)) {
          var strong = document.createElement('strong');
          strong.textContent = part.slice(2, -2);
          container.appendChild(strong);
        } else {
          container.appendChild(document.createTextNode(part));
        }
      });
    });
  }

  function showTyping() {
    var t = document.createElement('div');
    t.className = 'bubble assistant typing';
    t.id = 'typingBubble';
    t.innerHTML = '<span></span><span></span><span></span>';
    box.appendChild(t);
    scrollDown();
  }
  function hideTyping() {
    var t = document.getElementById('typingBubble');
    if (t) { t.remove(); }
  }

  function showSuggestions(items) {
    strip.innerHTML = '';
    (items || []).forEach(function (s) {
      var el = document.createElement(s.url ? 'a' : 'span');
      el.className = 'badge rounded-pill text-bg-light border me-2 mb-1 py-2 px-3 fw-semibold';
      el.title = s.description;
      el.textContent = s.title;
      if (s.url) { el.href = s.url; }
      strip.appendChild(el);
    });
  }

  // Re-render stored messages with the same safe formatter (bold + line breaks).
  document.querySelectorAll('.bubble[data-raw]').forEach(function (bubble) {
    var target = bubble.querySelector('.bubble-text');
    if (target) { target.textContent = ''; renderText(target, bubble.dataset.raw); }
  });
  scrollDown();

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var text = input.value.trim();
    if (!text) { input.focus(); return; }

    var welcome = document.getElementById('welcomeBubble');
    if (welcome) { welcome.remove(); }
    addBubble(text, 'user');
    input.value = '';
    input.disabled = true; sendBtn.disabled = true;
    strip.innerHTML = '';
    showTyping();

    fetch(window.CHAT_CONFIG.sendUrl, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
      body: JSON.stringify({ message: text })
    })
      .then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
      .then(function (res) {
        hideTyping();
        if (!res.ok) {
          addBubble(res.data.error || 'Something went wrong. Please try again.', 'assistant');
          return;
        }
        addBubble(res.data.reply, 'assistant', { sources: res.data.sources, crisis: res.data.is_crisis });
        if (res.data.title && titleEl) { titleEl.textContent = res.data.title; }
        showSuggestions(res.data.suggestions);
      })
      .catch(function () {
        hideTyping();
        addBubble("I'm having trouble connecting to the AI service right now. Please try again in a moment.", 'assistant');
      })
      .finally(function () {
        input.disabled = false; sendBtn.disabled = false; input.focus();
      });
  });
})();
