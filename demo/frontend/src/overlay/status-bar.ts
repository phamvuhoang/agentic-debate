import type { DebatePhase } from '../transport/protocol';

export function renderStatusBar(): HTMLElement {
  const root = document.createElement('div');
  root.className = 'status-bar';
  root.setAttribute('hidden', '');
  return root;
}

const PHASE_LABELS: Record<DebatePhase, string> = {
  idle: 'Idle',
  summoning: 'Summoning Agents',
  debate: 'Debate',
  clash: 'Clash',
  verdict: 'Judging',
  complete: 'Complete',
  error: 'Error',
};

export function updateStatusBar(
  bar: HTMLElement,
  view: {
    phase: DebatePhase;
    topic: string | null;
    currentRound: number;
    totalRounds: number | null;
    participantCount: number;
  },
): void {
  if (view.phase === 'idle' && !view.topic) {
    bar.setAttribute('hidden', '');
    return;
  }

  bar.removeAttribute('hidden');
  bar.innerHTML = '';

  if (view.topic) {
    const topic = document.createElement('span');
    topic.className = 'status-bar__topic';
    topic.textContent = view.topic;
    bar.append(topic);
  }

  const phase = document.createElement('span');
  phase.className = 'status-bar__phase';
  phase.dataset.phase = view.phase;
  phase.textContent = PHASE_LABELS[view.phase] ?? view.phase;
  bar.append(phase);

  if (view.currentRound > 0) {
    const round = document.createElement('span');
    round.className = 'status-bar__round';
    round.textContent = view.totalRounds
      ? `Round ${view.currentRound} / ${view.totalRounds}`
      : `Round ${view.currentRound}`;
    bar.append(round);
  }
}
