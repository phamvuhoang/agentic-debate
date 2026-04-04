export interface DebateConfig {
  topic: string;
  outputLocale: string;
  participantCount: number | null;
  roundCount: number | null;
}

interface PromptBarProps {
  onSubmit: (config: DebateConfig) => void;
  placeholder?: string;
}

export function renderPromptBar(props: PromptBarProps): HTMLElement {
  const root = document.createElement('div');
  root.className = 'prompt-bar';

  const topicRow = document.createElement('div');
  topicRow.className = 'prompt-bar__row';

  const input = document.createElement('input');
  input.type = 'text';
  input.className = 'prompt-bar__input';
  input.placeholder = props.placeholder ?? 'Ask a question to begin the debate\u2026';

  const button = document.createElement('button');
  button.className = 'prompt-bar__submit';
  button.textContent = 'Debate';

  topicRow.append(input, button);

  // Config row
  const configRow = document.createElement('div');
  configRow.className = 'prompt-bar__config';

  const langSelect = document.createElement('select');
  langSelect.className = 'prompt-bar__select';
  langSelect.title = 'Language';
  for (const [code, label] of LANGUAGES) {
    const opt = document.createElement('option');
    opt.value = code;
    opt.textContent = label;
    langSelect.append(opt);
  }

  const membersInput = createNumberInput('Members', 2, 10, 3);
  const roundsInput = createNumberInput('Rounds', 1, 5, 2);

  configRow.append(
    labelWrap('Language', langSelect),
    labelWrap('Members', membersInput),
    labelWrap('Rounds', roundsInput),
  );

  const submit = () => {
    const topic = input.value.trim();
    if (!topic) return;
    props.onSubmit({
      topic,
      outputLocale: langSelect.value,
      participantCount: membersInput.value ? Number(membersInput.value) : null,
      roundCount: roundsInput.value ? Number(roundsInput.value) : null,
    });
    input.value = '';
  };

  button.addEventListener('click', submit);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') submit();
  });

  root.append(configRow, topicRow);
  return root;
}

function createNumberInput(label: string, min: number, max: number, defaultVal: number): HTMLInputElement {
  const input = document.createElement('input');
  input.type = 'number';
  input.className = 'prompt-bar__number';
  input.min = String(min);
  input.max = String(max);
  input.value = String(defaultVal);
  input.title = label;
  return input;
}

function labelWrap(text: string, control: HTMLElement): HTMLElement {
  const wrapper = document.createElement('label');
  wrapper.className = 'prompt-bar__label';
  const span = document.createElement('span');
  span.textContent = text;
  wrapper.append(span, control);
  return wrapper;
}

const LANGUAGES: [string, string][] = [
  ['en', 'English'],
  ['vi', 'Ti\u1EBFng Vi\u1EC7t'],
  ['ja', '\u65E5\u672C\u8A9E'],
  ['ko', '\uD55C\uAD6D\uC5B4'],
  ['zh', '\u4E2D\u6587'],
  ['fr', 'Fran\u00E7ais'],
  ['de', 'Deutsch'],
  ['es', 'Espa\u00F1ol'],
  ['pt', 'Portugu\u00EAs'],
  ['ru', '\u0420\u0443\u0441\u0441\u043A\u0438\u0439'],
];
