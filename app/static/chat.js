(() => {
  const KEY = 'cb-state';
  let state;
  try { state = JSON.parse(sessionStorage.getItem(KEY)) || null; } catch { state = null; }
  if (!state) state = { id: (crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + Math.random().toString(16).slice(2)), messages: [] };
  const save = () => { try { sessionStorage.setItem(KEY, JSON.stringify(state)); } catch {} };

  const el = (tag, attrs = {}, text = '') => { const e = document.createElement(tag); Object.assign(e, attrs); if (text) e.textContent = text; return e; };
  const toggle = el('button', { id: 'cb-toggle', title: 'Chat with us', ariaLabel: 'Open chat' }, '💬');
  const panel = el('div', { id: 'cb-panel', role: 'dialog', ariaLabel: 'Chat assistant' });
  const head = el('div', { id: 'cb-head' });
  const title = el('div', {}, 'Northstar Assistant'); const sub = el('small', {}, 'Ask a question or talk to sales'); title.append(sub);
  const close = el('button', { id: 'cb-close', ariaLabel: 'Close chat' }, '×'); head.append(title, close);
  const log = el('div', { id: 'cb-log', ariaLive: 'polite' });
  const form = el('form', { id: 'cb-form' });
  const input = el('input', { id: 'cb-input', placeholder: 'Type your message…', maxLength: 1000, autocomplete: 'off' });
  const send = el('button', { id: 'cb-send', type: 'submit' }, 'Send');
  form.append(input, send); panel.append(head, log, form); document.body.append(toggle, panel);

  const add = (role, text, cls = '') => { const m = el('div', { className: `cb-msg cb-${role === 'user' ? 'user' : 'bot'} ${cls}` }, text); log.append(m); log.scrollTop = log.scrollHeight; return m; };
  const greeting = 'Hi! 👋 I can answer questions about Northstar CRM or connect you with our sales team. How can I help?';
  if (state.messages.length) state.messages.forEach(m => add(m.role, m.content)); else add('assistant', greeting);
  toggle.onclick = () => { panel.classList.toggle('open'); if (panel.classList.contains('open')) input.focus(); };
  close.onclick = () => panel.classList.remove('open');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = input.value.trim(); if (!text) return;
    input.value = ''; add('user', text); state.messages.push({ role: 'user', content: text }); save();
    send.disabled = true; const typing = add('assistant', 'Typing…', 'cb-typing');
    try {
      const res = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: state.id, messages: state.messages }) });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Something went wrong.');
      typing.remove(); add('assistant', data.reply); state.messages.push({ role: 'assistant', content: data.reply });
    } catch (err) {
      typing.remove(); add('assistant', err.message || 'Sorry, I could not reach the server. Please try again.');
      state.messages.pop();  // drop the unanswered user turn so history stays alternating
    } finally { save(); send.disabled = false; input.focus(); }
  });
})();
