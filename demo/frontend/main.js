// demo/frontend/main.js
import { v0_8 as a2ui } from '@a2ui/lit';
import { ContextProvider } from '@lit/context';
import { renderMarkdown } from '@a2ui/markdown-it';

const SURFACE_ID = 'debate-surface';

// ---------------------------------------------------------------------------
// Theme — drives visual styling of all a2ui-* components via additionalStyles.
// The CSS class maps (components.*) are left empty; all visual styling is done
// via inline styles in additionalStyles so we don't rely on external CSS vars.
// ---------------------------------------------------------------------------
const DEBATE_THEME = {
  components: {
    AudioPlayer: {}, Button: {}, Card: {}, Column: {},
    CheckBox: { container: {}, element: {}, label: {} },
    DateTimeInput: { container: {}, element: {}, label: {} },
    Divider: {},
    Image: { all: {}, icon: {}, avatar: {}, smallFeature: {}, mediumFeature: {}, largeFeature: {}, header: {} },
    Icon: {}, List: {},
    Modal: { backdrop: {}, element: {} },
    MultipleChoice: { container: {}, element: {}, label: {} },
    Row: {},
    Slider: { container: {}, element: {}, label: {} },
    Tabs: { container: {}, element: {}, controls: { all: {}, selected: {} } },
    Text: { all: {}, h1: {}, h2: {}, h3: {}, h4: {}, h5: {}, caption: {}, body: {} },
    TextField: { container: {}, element: {}, label: {} },
    Video: {},
  },
  elements: {
    a: {}, audio: {}, body: {}, button: {}, h1: {}, h2: {}, h3: {}, h4: {}, h5: {},
    iframe: {}, input: {}, p: {}, pre: {}, textarea: {}, video: {},
  },
  additionalStyles: {
    Card: {
      background: 'rgba(255,255,255,0.06)',
      'border-radius': '10px',
      padding: '16px 20px',
      'border-left': '3px solid rgba(255,255,255,0.15)',
      'box-shadow': '0 2px 8px rgba(0,0,0,0.3)',
      'margin-bottom': '4px',
    },
    Column: {
      gap: '10px',
    },
    Row: {
      gap: '8px',
    },
    Button: {
      background: 'rgba(255,255,255,0.1)',
      color: '#fff',
      'border-radius': '6px',
      padding: '10px 20px',
      cursor: 'pointer',
      border: '1px solid rgba(255,255,255,0.2)',
      'font-size': '14px',
      'font-weight': '500',
    },
    // Text uses per-hint styles (object with h1/h2/h3/body keys)
    Text: {
      h1: { 'font-size': '22px', 'font-weight': '700', color: '#ffffff', 'line-height': '1.3', margin: '0' },
      h2: { 'font-size': '18px', 'font-weight': '600', color: '#e8e8e8', 'line-height': '1.4', margin: '0' },
      h3: { 'font-size': '15px', 'font-weight': '600', color: '#d0d0d0', 'line-height': '1.4', margin: '0' },
      h4: { 'font-size': '13px', 'font-weight': '500', color: '#b8b8b8', 'line-height': '1.4', margin: '0' },
      h5: { 'font-size': '12px', 'font-weight': '500', color: '#b0b0b0', 'line-height': '1.4', margin: '0' },
      caption: { 'font-size': '11px', color: '#888', 'line-height': '1.4', margin: '0' },
      body: { 'font-size': '14px', color: '#c8c8c8', 'line-height': '1.6', margin: '0' },
    },
    markdown: {},
  },
};

// Provide theme context to all a2ui-* components in the tree
const themeProvider = new ContextProvider(document.getElementById('app'), {
  context: a2ui.UI.Context.theme,
  initialValue: DEBATE_THEME,
});
themeProvider.hostConnected();

// Provide markdown renderer so text with usageHint h1/h2/h3 renders as HTML
const markdownProvider = new ContextProvider(document.getElementById('app'), {
  context: a2ui.UI.Context.markdown,
  initialValue: renderMarkdown,
});
markdownProvider.hostConnected();

// ---------------------------------------------------------------------------
// Processor and surface wiring
// ---------------------------------------------------------------------------
const processor = a2ui.Data.createSignalA2uiMessageProcessor();

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
  processor.clearSurfaces();
  surfaceEl.surface = null;
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
          processor.processMessages([msg]);
          surfaceEl.surface = processor.getSurfaces().get(SURFACE_ID) ?? null;
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
