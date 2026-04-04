import type { DebateParticipantView } from '../state/types';

export function renderSpeakerBanner(): HTMLElement {
  const root = document.createElement('div');
  root.className = 'speaker-banner';
  root.setAttribute('hidden', '');
  return root;
}

export function updateSpeakerBanner(
  banner: HTMLElement,
  speaker: DebateParticipantView | null,
): void {
  if (!speaker) {
    banner.setAttribute('hidden', '');
    return;
  }

  banner.removeAttribute('hidden');
  banner.innerHTML = '';

  if (speaker.accent_color) {
    banner.style.borderLeftColor = speaker.accent_color;
  }

  const label = document.createElement('span');
  label.className = 'speaker-banner__label';
  label.textContent = speaker.label;
  banner.append(label);

  if (speaker.role) {
    const role = document.createElement('span');
    role.className = 'speaker-banner__role';
    role.textContent = speaker.role;
    banner.append(role);
  }

  if (speaker.stance) {
    const stance = document.createElement('p');
    stance.className = 'speaker-banner__thesis';
    stance.textContent = speaker.stance;
    banner.append(stance);
  }
}
