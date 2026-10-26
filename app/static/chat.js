const form = document.getElementById('chat-form');
const question = document.getElementById('question');
const messages = document.getElementById('messages');
const send = document.getElementById('send');
const clear = document.getElementById('clear');
const status = document.getElementById('status');
const welcome = messages.innerHTML;
let busy = false;
function addMessage(text, role, sources = []) {
  const article = document.createElement('article');
  article.className = `message ${role}`;
  if (role !== 'user') {
    const label = document.createElement('div');
    label.className = 'label'; label.textContent = role === 'error' ? 'PLEASE TRY AGAIN' : 'DEMOSHOP';
    article.append(label);
  }
  const content = document.createElement('div'); content.textContent = text; article.append(content);
  if (sources.length) {
    const group = document.createElement('div'); group.className = 'sources';
    for (const source of sources) {
      const chip = document.createElement('span'); chip.className = 'source';
      chip.textContent = `[${source.citation}] ${source.file}`;
      chip.title = 'Retrieved policy source'; group.append(chip);
    }
    article.append(group);
  }
  messages.append(article); messages.scrollTop = messages.scrollHeight;
}
async function submit(text) {
  if (busy || !text.trim()) return;
  busy = true; send.disabled = true; clear.disabled = true;
  question.value = ''; addMessage(text, 'user'); status.textContent = 'Finding relevant policy passages…';
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 180000);
  try {
    const response = await fetch('/api/chat', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: text}), signal: controller.signal
    });
    const data = await response.json();
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Unable to process the question. Please try again.');
    addMessage(data.answer, 'assistant', data.sources || []);
  } catch (error) {
    addMessage(error.name === 'AbortError' ? 'The service took too long. It may be starting up; please try again.' : error.message, 'error');
  } finally {
    clearTimeout(timer); busy = false; send.disabled = false; clear.disabled = false;
    status.textContent = 'Sources included · No live order access · Don’t share sensitive details';
    question.focus();
  }
}
form.addEventListener('submit', event => { event.preventDefault(); submit(question.value.trim()); });
question.addEventListener('keydown', event => {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault(); form.requestSubmit();
  }
});
document.querySelectorAll('[data-question]').forEach(button => button.addEventListener('click', () => submit(button.dataset.question)));
clear.addEventListener('click', () => { if (!busy) { messages.innerHTML = welcome; question.focus(); } });
