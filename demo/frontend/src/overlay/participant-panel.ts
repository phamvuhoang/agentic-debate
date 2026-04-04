import type { DebateParticipantView } from '../state/types';

export function renderParticipantPanel(): HTMLElement {
  const root = document.createElement('aside');
  root.className = 'participant-panel';
  root.setAttribute('hidden', '');
  return root;
}

export function updateParticipantPanel(
  panel: HTMLElement,
  participants: DebateParticipantView[],
  activeSpeakerId: string | null,
): void {
  if (participants.length === 0) {
    panel.setAttribute('hidden', '');
    return;
  }

  panel.removeAttribute('hidden');
  panel.innerHTML = '';

  const heading = document.createElement('h3');
  heading.className = 'participant-panel__heading';
  heading.textContent = `Participants (${participants.length})`;
  panel.append(heading);

  const list = document.createElement('ul');
  list.className = 'participant-panel__list';

  for (const p of participants) {
    const li = document.createElement('li');
    li.className = 'participant-panel__item';
    if (p.participant_id === activeSpeakerId) {
      li.classList.add('participant-panel__item--active');
    }

    const dot = document.createElement('span');
    dot.className = 'participant-panel__dot';
    if (p.accent_color) dot.style.background = p.accent_color;

    const name = document.createElement('span');
    name.className = 'participant-panel__name';
    name.textContent = p.label;

    const role = document.createElement('span');
    role.className = 'participant-panel__role';
    role.textContent = p.role;

    li.append(dot, name);
    if (p.role) li.append(role);

    if (p.stance) {
      const stance = document.createElement('span');
      stance.className = 'participant-panel__stance';
      stance.textContent = p.stance;
      li.append(stance);
    }

    list.append(li);
  }

  panel.append(list);
}
