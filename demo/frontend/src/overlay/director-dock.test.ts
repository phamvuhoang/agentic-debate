import { describe, expect, it, vi } from 'vitest';
import { renderDirectorDock } from './director-dock';

describe('renderDirectorDock', () => {
  it('emits a request_verdict action when the verdict button is clicked', () => {
    const onAction = vi.fn();
    const dock = renderDirectorDock({ onAction });

    dock.querySelector('[data-action="request_verdict"]')?.dispatchEvent(new MouseEvent('click'));

    expect(onAction).toHaveBeenCalledWith({ action: 'request_verdict', payload: {} });
  });

  it('emits a pause_debate action when the pause button is clicked', () => {
    const onAction = vi.fn();
    const dock = renderDirectorDock({ onAction });

    dock.querySelector('[data-action="pause_debate"]')?.dispatchEvent(new MouseEvent('click'));

    expect(onAction).toHaveBeenCalledWith({ action: 'pause_debate', payload: {} });
  });
});
