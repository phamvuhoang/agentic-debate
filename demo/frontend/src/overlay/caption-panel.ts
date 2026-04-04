import type { CaptionEntry, VerdictView } from '../state/types';
import type { DebatePhase } from '../transport/protocol';

interface CaptionPanelProps {
  text: string | null;
}

export function renderCaptionPanel(_props: CaptionPanelProps): HTMLElement {
  const root = document.createElement('div');
  root.className = 'caption-panel';
  root.setAttribute('hidden', '');
  return root;
}

export function updateCaptionPanel(
  panel: HTMLElement,
  view: {
    phase: DebatePhase;
    currentCaption: CaptionEntry | null;
    verdict: VerdictView | null;
    activeSpeakerLabel?: string;
  },
): void {
  panel.innerHTML = '';

  if (view.phase === 'complete' && view.verdict) {
    panel.removeAttribute('hidden');
    panel.className = 'caption-panel caption-panel--verdict';

    const heading = document.createElement('h3');
    heading.className = 'caption-panel__verdict-heading';
    heading.textContent = 'Final Verdict';
    panel.append(heading);

    if (view.verdict.summary) {
      const summary = document.createElement('p');
      summary.className = 'caption-panel__verdict-summary';
      summary.textContent = view.verdict.summary;
      panel.append(summary);
    }

    if (view.verdict.contested_topics.length > 0) {
      const topics = document.createElement('div');
      topics.className = 'caption-panel__contested';
      const topicLabel = document.createElement('span');
      topicLabel.className = 'caption-panel__contested-label';
      topicLabel.textContent = 'Contested: ';
      topics.append(topicLabel);
      topics.append(document.createTextNode(view.verdict.contested_topics.join(', ')));
      panel.append(topics);
    }
    return;
  }

  if (view.phase === 'verdict') {
    panel.removeAttribute('hidden');
    panel.className = 'caption-panel caption-panel--judging';
    const judging = document.createElement('p');
    judging.className = 'caption-panel__judging';
    judging.textContent = 'Judge is deliberating\u2026';
    panel.append(judging);
    return;
  }

  if (view.currentCaption) {
    panel.removeAttribute('hidden');
    panel.className = 'caption-panel';

    const speaker = document.createElement('span');
    speaker.className = 'caption-panel__speaker';
    speaker.textContent = view.currentCaption.speakerLabel;
    panel.append(speaker);

    const text = document.createElement('p');
    text.className = 'caption-panel__text';
    text.textContent = view.currentCaption.text;
    panel.append(text);
    return;
  }

  panel.setAttribute('hidden', '');
}
