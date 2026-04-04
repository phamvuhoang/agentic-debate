interface TimelineBeat {
  sequence: number;
  type: string;
  label: string;
}

interface TimelineRailProps {
  beats: TimelineBeat[];
  activeBeat?: number;
}

export function renderTimelineRail(props: TimelineRailProps): HTMLElement {
  const root = document.createElement('div');
  root.className = 'timeline-rail';

  for (const beat of props.beats) {
    const marker = document.createElement('button');
    marker.className = 'timeline-rail__beat';
    marker.dataset.sequence = String(beat.sequence);
    marker.title = beat.label;
    if (beat.sequence === props.activeBeat) marker.classList.add('timeline-rail__beat--active');
    root.append(marker);
  }

  return root;
}
