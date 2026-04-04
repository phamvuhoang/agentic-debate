import * as THREE from 'three';

export interface TableView {
  mode: string;
}

export interface RoundTable {
  group: THREE.Group;
  apply(view: TableView): void;
}

export function createRoundTable(): RoundTable {
  const group = new THREE.Group();

  // Table surface
  const geometry = new THREE.CylinderGeometry(2, 2, 0.1, 32);
  const material = new THREE.MeshStandardMaterial({ color: 0x3a2a1a });
  const mesh = new THREE.Mesh(geometry, material);
  group.add(mesh);

  return {
    group,
    apply(view: TableView) {
      // Visual state transitions based on mode
      const scale = view.mode === 'converged' ? 1.1 : 1.0;
      group.scale.setScalar(scale);
    },
  };
}
