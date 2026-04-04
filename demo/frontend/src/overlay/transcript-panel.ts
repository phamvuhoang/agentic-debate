import type { CaptionEntry, VerdictView } from '../state/types';

export interface TranscriptPanelElements {
  root: HTMLElement;
  update(captions: CaptionEntry[], verdict: VerdictView | null, currentRound: number): void;
  toggle(): void;
}

export function renderTranscriptPanel(): TranscriptPanelElements {
  const root = document.createElement('div');
  root.className = 'transcript-panel';
  root.setAttribute('hidden', '');

  // Header with toggle and download
  const header = document.createElement('div');
  header.className = 'transcript-panel__header';

  const title = document.createElement('span');
  title.className = 'transcript-panel__title';
  title.textContent = 'Transcript';

  const actions = document.createElement('div');
  actions.className = 'transcript-panel__actions';

  const downloadBtn = document.createElement('button');
  downloadBtn.className = 'transcript-panel__btn';
  downloadBtn.textContent = 'Download';
  downloadBtn.title = 'Download transcript as text file';

  const closeBtn = document.createElement('button');
  closeBtn.className = 'transcript-panel__btn';
  closeBtn.textContent = '\u00D7';
  closeBtn.title = 'Close transcript';

  actions.append(downloadBtn, closeBtn);
  header.append(title, actions);

  const body = document.createElement('div');
  body.className = 'transcript-panel__body';

  root.append(header, body);

  let lastCaptionCount = 0;
  let userScrolled = false;

  body.addEventListener('scroll', () => {
    const atBottom = body.scrollHeight - body.scrollTop - body.clientHeight < 40;
    userScrolled = !atBottom;
  });

  let userClosed = false;

  closeBtn.addEventListener('click', () => {
    root.setAttribute('hidden', '');
    userClosed = true;
  });

  downloadBtn.addEventListener('click', () => {
    const text = buildDownloadText(body);
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `debate-transcript-${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  });

  return {
    root,
    update(captions: CaptionEntry[], verdict: VerdictView | null, currentRound: number) {
      if (captions.length === 0 && !verdict) {
        root.setAttribute('hidden', '');
        userClosed = false;
        return;
      }

      // Don't force-open if the user closed it
      if (!userClosed) {
        root.removeAttribute('hidden');
      }

      // Only re-render if new content arrived
      const totalItems = captions.length + (verdict ? 1 : 0);
      if (totalItems === lastCaptionCount) return;
      lastCaptionCount = totalItems;

      body.innerHTML = '';
      let prevRound = -1;

      for (const entry of captions) {
        if (entry.round !== prevRound) {
          prevRound = entry.round;
          const sep = document.createElement('div');
          sep.className = 'transcript-panel__round-sep';
          sep.textContent = `Round ${entry.round}`;
          body.append(sep);
        }

        const item = document.createElement('div');
        item.className = 'transcript-panel__entry';

        const speaker = document.createElement('span');
        speaker.className = 'transcript-panel__speaker';
        speaker.textContent = entry.speakerLabel;

        const text = document.createElement('p');
        text.className = 'transcript-panel__text';
        text.textContent = entry.text;

        item.append(speaker, text);
        body.append(item);
      }

      if (verdict) {
        const sep = document.createElement('div');
        sep.className = 'transcript-panel__round-sep transcript-panel__round-sep--verdict';
        sep.textContent = 'Final Verdict';
        body.append(sep);

        const item = document.createElement('div');
        item.className = 'transcript-panel__entry transcript-panel__entry--verdict';
        const text = document.createElement('p');
        text.className = 'transcript-panel__text';
        text.textContent = verdict.summary;
        item.append(text);

        if (verdict.contested_topics.length > 0) {
          const ct = document.createElement('p');
          ct.className = 'transcript-panel__contested';
          ct.textContent = 'Contested: ' + verdict.contested_topics.join(', ');
          item.append(ct);
        }

        body.append(item);
      }

      // Auto-scroll to bottom unless user is reading earlier content
      if (!userScrolled) {
        body.scrollTop = body.scrollHeight;
      }
    },

    toggle() {
      if (root.hasAttribute('hidden')) {
        root.removeAttribute('hidden');
        userClosed = false;
      } else {
        root.setAttribute('hidden', '');
        userClosed = true;
      }
    },
  };
}

/** Toggle the transcript panel open. */
export function createTranscriptToggle(transcriptPanel: TranscriptPanelElements): HTMLElement {
  const btn = document.createElement('button');
  btn.className = 'transcript-toggle';
  btn.textContent = 'Transcript';
  btn.title = 'View full debate transcript';
  btn.addEventListener('click', () => transcriptPanel.toggle());
  return btn;
}

function buildDownloadText(body: HTMLElement): string {
  const lines: string[] = [];
  for (const child of body.children) {
    if (child.classList.contains('transcript-panel__round-sep')) {
      lines.push('', `=== ${child.textContent} ===`, '');
    } else if (child.classList.contains('transcript-panel__entry')) {
      const speaker = child.querySelector('.transcript-panel__speaker');
      const text = child.querySelector('.transcript-panel__text');
      if (speaker) lines.push(`[${speaker.textContent}]`);
      if (text) lines.push(text.textContent ?? '');
      lines.push('');
    }
  }
  return lines.join('\n');
}
