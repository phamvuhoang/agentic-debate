import * as THREE from 'three';

export interface SeatView {
  mode: 'active' | 'idle' | 'tension' | 'audience';
}

export interface SpeakerSeat {
  id: string;
  group: THREE.Group;
  apply(view: SeatView): void;
}

export function createSpeakerSeat(id: string, position: THREE.Vector3): SpeakerSeat {
  const group = new THREE.Group();
  group.position.copy(position);

  const geometry = new THREE.CylinderGeometry(0.3, 0.3, 0.05, 16);
  const material = new THREE.MeshStandardMaterial({ color: 0x888888 });
  const mesh = new THREE.Mesh(geometry, material);
  group.add(mesh);

  return {
    id,
    group,
    apply(view: SeatView) {
      if (view.mode === 'active') {
        (material as THREE.MeshStandardMaterial).color.set(0xd5a44a);
      } else {
        (material as THREE.MeshStandardMaterial).color.set(0x888888);
      }
    },
  };
}
