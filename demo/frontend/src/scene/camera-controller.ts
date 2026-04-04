import * as THREE from 'three';
import type { SceneCuePlan } from './animation-orchestrator';

export class CameraController {
  private readonly camera: THREE.PerspectiveCamera;

  constructor(camera: THREE.PerspectiveCamera) {
    this.camera = camera;
  }

  applyPreset(preset: SceneCuePlan['cameraPreset']): void {
    switch (preset) {
      case 'verdict-center':
        this.camera.position.set(0, 6, 8);
        this.camera.lookAt(0, 0, 0);
        break;
      case 'challenge-confrontation':
        this.camera.position.set(4, 4, 6);
        this.camera.lookAt(0, 0, 0);
        break;
      case 'speaker-focus':
        this.camera.position.set(2, 5, 7);
        this.camera.lookAt(0, 0, 0);
        break;
      default:
        this.camera.position.set(0, 8, 10);
        this.camera.lookAt(0, 0, 0);
    }
  }
}
