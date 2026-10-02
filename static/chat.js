const form = document.querySelector('#question-form');
const input = document.querySelector('#question');
const button = form.querySelector('button');
const status = document.querySelector('#status');
const messages = document.querySelector('#messages');
function addMessage(label, text) {
  const p = document.createElement('p');
  const title = document.createElement('strong');
  title.textContent = label + ': ';
  p.append(title, document.createTextNode(text));
  messages.append(p);
}
form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const question = input.value.trim();
  if (!question || button.disabled) return;
  button.disabled = true;
  status.textContent = 'Working…';
  addMessage('You', question);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 120000);
  try {
    const response = await fetch('/ask', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({question}), signal: controller.signal
    });
    if (!response.ok) throw new Error('The request could not be completed. Please try again.');
    const data = await response.json();
    addMessage('WellQuery', data.answer);
    input.value = '';
    status.textContent = '';
  } catch (error) {
    status.textContent = error.name === 'AbortError' ? 'Request timed out. Please try again.' : error.message;
  } finally {
    clearTimeout(timer);
    button.disabled = false;
    input.focus();
  }
});
