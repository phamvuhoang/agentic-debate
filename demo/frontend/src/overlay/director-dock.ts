import type { SessionActionRequest, SessionActionType } from '../transport/protocol';

interface DirectorDockProps {
  onAction: (action: SessionActionRequest) => void;
}

const DOCK_ACTIONS: SessionActionType[] = [
  'pause_debate',
  'inject_challenge',
  'advance_round',
  'request_verdict',
];

const ACTION_LABELS: Record<SessionActionType, string> = {
  pause_debate: 'Pause',
  resume_debate: 'Resume',
  focus_agent: 'Focus',
  inject_challenge: 'Challenge',
  redirect_debate: 'Redirect',
  advance_round: 'Next Round',
  request_verdict: 'Verdict',
  move_camera: 'Camera',
};

export function renderDirectorDock(props: DirectorDockProps): HTMLElement {
  const root = document.createElement('aside');
  root.className = 'director-dock';

  for (const action of DOCK_ACTIONS) {
    const button = document.createElement('button');
    button.className = 'director-dock__btn';
    button.dataset.action = action;
    button.textContent = ACTION_LABELS[action];
    button.addEventListener('click', () => props.onAction({ action, payload: {} }));
    root.append(button);
  }

  return root;
}
