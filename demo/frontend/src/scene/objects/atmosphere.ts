import * as THREE from 'three';

export function createAmbientLight(): THREE.AmbientLight {
  return new THREE.AmbientLight(0xf3ead8, 0.4);
}

export function createPointLight(position: THREE.Vector3): THREE.PointLight {
  const light = new THREE.PointLight(0xd5a44a, 1.5, 20);
  light.position.copy(position);
  return light;
}

export function createFog(): THREE.FogExp2 {
  return new THREE.FogExp2(0x0b0908, 0.05);
}
