import { describe, expect, it } from 'vitest';
import { bootstrapApp } from './bootstrap';

describe('bootstrapApp', () => {
  it('falls back to the 2D shell when WebGL is unavailable', async () => {
    const mount = document.createElement('div');
    const result = await bootstrapApp(mount, { hasWebGL: false });

    expect(result.mode).toBe('fallback');
    expect(mount.textContent).toContain('Debate chamber unavailable');
  });

  it('renders fallback shell content into the mount element', async () => {
    const mount = document.createElement('div');
    await bootstrapApp(mount, { hasWebGL: false });

    expect(mount.querySelector('h1')?.textContent).toBe('Debate chamber unavailable');
  });
});
