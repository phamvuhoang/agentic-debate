import * as THREE from 'three';
import { createRoundTable, type RoundTable } from './objects/round-table';
import { createParticleFigure, type ParticleFigure } from './objects/particle-figure';
import { createAmbientLight, createPointLight, createFog } from './objects/atmosphere';
import { CameraController } from './camera-controller';
import type { SceneViewModel } from '../state/selectors';

export class ChamberScene {
  private readonly scene: THREE.Scene;
  private readonly camera: THREE.PerspectiveCamera;
  private readonly table: RoundTable;
  private readonly figures: Map<string, ParticleFigure> = new Map();
  private readonly cameraController: CameraController;
  private readonly clock = new THREE.Clock();
  private elapsed = 0;

  constructor(width: number, height: number) {
    this.scene = new THREE.Scene();
    this.scene.fog = createFog();
    this.scene.background = new THREE.Color(0x0b0908);

    this.camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 100);
    this.camera.position.set(0, 8, 10);
    this.camera.lookAt(0, 0, 0);

    this.cameraController = new CameraController(this.camera);

    this.table = createRoundTable();
    this.scene.add(this.table.group);

    this.scene.add(createAmbientLight());
    this.scene.add(createPointLight(new THREE.Vector3(0, 5, 0)));
  }

  applyState(view: SceneViewModel): void {
    this.table.apply(view.table);
    this.cameraController.applyPreset(view.cameraPreset as Parameters<CameraController['applyPreset']>[0]);

    for (const p of view.participants) {
      if (!this.figures.has(p.participant_id)) {
        const total = Math.max(view.participants.length, 1);
        const index = this.figures.size;
        const angle = (index / total) * Math.PI * 2 - Math.PI / 2;
        const radius = 2.4;
        const position = new THREE.Vector3(
          Math.cos(angle) * radius,
          0,
          Math.sin(angle) * radius,
        );

        const figure = createParticleFigure(p.participant_id, p.accent_color);
        figure.group.position.copy(position);
        figure.group.lookAt(0, 0, 0);
        this.figures.set(p.participant_id, figure);
        this.scene.add(figure.group);
      }

      const seatView = view.seats[p.participant_id];
      if (seatView) {
        this.figures.get(p.participant_id)!.setActive(seatView.mode === 'active');
      }
    }
  }

  /** Call each frame to animate particle breathing/dissolve. */
  tick(): void {
    const dt = Math.min(this.clock.getDelta(), 0.05); // cap to avoid large jumps
    this.elapsed += dt;
    for (const figure of this.figures.values()) {
      figure.update(this.elapsed, dt);
    }
  }

  getScene(): THREE.Scene {
    return this.scene;
  }

  getCamera(): THREE.PerspectiveCamera {
    return this.camera;
  }
}
