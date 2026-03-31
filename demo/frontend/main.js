// demo/frontend/main.js
import { v0_8 as a2ui } from '@a2ui/lit';

// Register A2UI custom elements (auto-registers a2ui-surface, a2ui-card, etc.)
// The import above registers elements as a side-effect.

const SURFACE_ID = 'debate-surface';

// Create the reactive message processor using the versioned namespace API
// v0_8.Data.createSignalA2uiMessageProcessor() returns a signal-backed processor
const processor = a2ui.Data.createSignalA2uiMessageProcessor();

// Wire processor to <a2ui-surface>
const surfaceEl = document.getElementById(SURFACE_ID);
surfaceEl.processor = processor;
surfaceEl.surfaceId = SURFACE_ID;

const topicInput = document.getElementById('topic-input');
const submitBtn = document.getElementById('submit-btn');

function setRunning(running) {
  submitBtn.disabled = running;
  topicInput.disabled = running;
}

function resetSurface() {
  if (processor.clearSurfaces) processor.clearSurfaces();
  else if (processor.reset) processor.reset();
}

async function startDebate(topic) {
  setRunning(true);
  resetSurface();

  let response;
  try {
    response = await fetch('/debate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic }),
    });
  } catch (err) {
    console.error('fetch failed', err);
    setRunning(false);
    return;
  }

  if (!response.ok) {
    console.error('debate endpoint error', response.status);
    setRunning(false);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop(); // keep incomplete line

      for (const line of lines) {
        if (!line.startsWith('data:')) continue;
        const raw = line.slice(5).trim();
        if (!raw || raw === '[DONE]') continue;
        try {
          const msg = JSON.parse(raw);
          // Feed into A2UI processor — processMessages takes an array
          processor.processMessages([msg]);
        } catch (e) {
          console.warn('failed to parse SSE message', raw, e);
        }
      }
    }
  } finally {
    setRunning(false);
  }
}

// Submit handler
submitBtn.addEventListener('click', () => {
  const topic = topicInput.value.trim();
  if (!topic) return;
  startDebate(topic);
});

topicInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') submitBtn.click();
});

// Handle A2UI action events (e.g., restart button)
surfaceEl.addEventListener('a2uiaction', (event) => {
  const { name } = event.detail || {};
  if (name === 'restart_debate') {
    topicInput.value = '';
    topicInput.focus();
    resetSurface();
    setRunning(false);
  }
});
