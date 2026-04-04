export interface AppEnvironment {
  hasWebGL: boolean;
  reducedMotion: boolean;
}

export function detectPreferences(overrides: Partial<AppEnvironment> = {}): AppEnvironment {
  const hasWebGL = overrides.hasWebGL ?? detectWebGL();
  const reducedMotion =
    overrides.reducedMotion ??
    window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ??
    false;

  return { hasWebGL, reducedMotion };
}

function detectWebGL(): boolean {
  try {
    const canvas = document.createElement('canvas');
    return !!(
      canvas.getContext('webgl') ||
      canvas.getContext('experimental-webgl')
    );
  } catch {
    return false;
  }
}
