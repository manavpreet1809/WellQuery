const form = document.querySelector('#question-form');
const input = document.querySelector('#question');
const button = form.querySelector('button[type=submit]');
const welcome = document.querySelector('#welcome');
const evidenceList = document.querySelector('#evidence-list');
const evidenceEmpty = document.querySelector('#evidence-empty');
const resetButton = document.querySelector('#new-session');
const status = document.querySelector('#status');
const messages = document.querySelector('#messages');
let responseNumber = 0;

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function safeSource(url) {
  try {
    const parsed = new URL(url);
    return ['https:', 'http:'].includes(parsed.protocol) ? parsed.href : null;
  } catch { return null; }
}
function addMessage(label, text) {
  const p = element('p', undefined, 'message');
  p.append(element('strong', label + ': '), document.createTextNode(text));
  messages.append(p);
}
function renderAnswer(data) {
  responseNumber += 1;
  const section = element('article', undefined, 'answer');
  section.append(element('h2', 'WellQuery'));
  const style = data.answer_style === 'excerpts' ? 'Source excerpts — not AI synthesis'
    : data.answer_style === 'ollama' ? 'AI synthesis — inspect supporting quotes' : data.mode;
  section.append(element('p', style, 'answer-label'));
  if (data.refused) section.append(element('p', 'Response limited: ' + (data.refusal_reason || 'unsupported request'), 'notice'));
  const evidence = new Map((data.citations || []).map(c => [c.n, c]));
  if (data.claims?.length) {
    for (const claim of data.claims) {
      const p = element('p', claim.text + ' ');
      if (evidence.has(claim.citation)) {
        const a = element('a', '[' + claim.citation + ']');
        const target = `evidence-${responseNumber}-${claim.citation}`;
        a.href = '#' + target;
        a.setAttribute('aria-label', 'View source ' + claim.citation);
        a.addEventListener('click', () => { document.getElementById(target).open = true; });
        p.append(a);
      }
      section.append(p);
    }
  } else section.append(element('p', data.answer));
  const evidenceGroup = element('section', undefined, 'evidence-group');
  evidenceGroup.append(element('h3', `ANSWER ${String(responseNumber).padStart(2, '0')} / SOURCES`));
  if (!data.citations?.length) evidenceGroup.append(element('p', 'No supporting sources for this response.', 'evidence-empty-response'));
  for (const citation of data.citations || []) {
    const details = element('details');
    details.id = `evidence-${responseNumber}-${citation.n}`;
    details.append(element('summary', `[${citation.n}] ${citation.title}`));
    details.append(element('p', citation.publisher + ' · ' + citation.section_path, 'source-meta'));
    const url = safeSource(citation.url);
    if (url) {
      const a = element('a', 'Open original source');
      a.href = url; a.target = '_blank'; a.rel = 'noopener noreferrer'; details.append(a);
    }
    const quotes = (data.claims || []).filter(c => c.citation === citation.n);
    for (const claim of quotes) details.append(element('blockquote', claim.quote));
    const passage = element('details', undefined, 'full-passage');
    passage.append(element('summary', 'Full retrieved passage'));
    passage.append(element('p', citation.text, 'passage'));
    details.append(passage);
    details.append(element('small', citation.licence || ''));
    evidenceGroup.append(details);
  }
  section.append(element('p', `${data.chunks_used} supporting passages · ${Math.round(data.latency_ms || 0)} ms server time`, 'source-meta'));
  messages.append(section);
  evidenceEmpty.hidden = true;
  evidenceList.append(evidenceGroup);
}
form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const question = input.value.trim();
  if (!question || button.disabled) return;
  welcome.hidden = true;
  resetButton.disabled = true;
  button.disabled = true; form.setAttribute('aria-busy', 'true');
  status.textContent = 'Finding evidence…';
  addMessage('You', question);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 120000);
  try {
    const response = await fetch('/ask', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({question, answer_style: document.querySelector('#answer-style')?.value || 'excerpts'}),
      signal: controller.signal
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(typeof error.detail === 'string' ? error.detail : 'The request could not be completed. Please try again.');
    }
    renderAnswer(await response.json());
    input.value = ''; status.textContent = '';
  } catch (error) {
    status.textContent = error.name === 'AbortError' ? 'Request timed out. Please try again.' : error.message;
  } finally {
    clearTimeout(timer); button.disabled = false; resetButton.disabled = false; form.setAttribute('aria-busy', 'false'); input.focus();
  }
});

for (const suggestion of document.querySelectorAll('[data-question]')) {
  suggestion.addEventListener('click', () => {
    input.value = suggestion.dataset.question;
    input.focus();
    input.scrollIntoView({block: 'center', behavior: 'auto'});
  });
}
resetButton.addEventListener('click', () => {
  if (button.disabled) return;
  messages.replaceChildren();
  evidenceList.replaceChildren();
  welcome.hidden = false; evidenceEmpty.hidden = false;
  responseNumber = 0; input.value = ''; status.textContent = '';
  history.replaceState(null, '', location.pathname);
  input.focus();
});
