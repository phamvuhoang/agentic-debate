import * as THREE from 'three';
import { ChamberScene } from './chamber-scene';
import type { SceneViewModel } from '../state/selectors';

export class SceneRenderer {
  private readonly renderer: THREE.WebGLRenderer;
  private readonly chamberScene: ChamberScene;
  private animationId: number | null = null;

  constructor(mount: HTMLElement) {
    const width = mount.clientWidth || 800;
    const height = mount.clientHeight || 600;

    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mount.appendChild(this.renderer.domElement);

    this.chamberScene = new ChamberScene(width, height);
    this.startLoop();
  }

  private startLoop(): void {
    const animate = () => {
      this.animationId = requestAnimationFrame(animate);
      this.chamberScene.tick();
      this.renderer.render(this.chamberScene.getScene(), this.chamberScene.getCamera());
    };
    animate();
  }

  render(view: SceneViewModel): void {
    this.chamberScene.applyState(view);
  }

  dispose(): void {
    if (this.animationId !== null) cancelAnimationFrame(this.animationId);
    this.renderer.dispose();
  }
}
