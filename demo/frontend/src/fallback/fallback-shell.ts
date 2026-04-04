export function renderFallbackShell(mount: HTMLElement): void {
  mount.innerHTML = '';

  const shell = document.createElement('div');
  shell.className = 'fallback-shell';
  shell.style.cssText =
    'display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;color:#f3ead8;font-family:system-ui,sans-serif;background:#0b0908;gap:16px;';

  const heading = document.createElement('h1');
  heading.textContent = 'Debate chamber unavailable';
  heading.style.fontSize = '24px';

  const body = document.createElement('p');
  body.textContent = 'Your browser does not support WebGL. Please try a modern desktop browser.';
  body.style.cssText = 'opacity:0.7;font-size:14px;text-align:center;max-width:400px;';

  shell.append(heading, body);
  mount.append(shell);
}
