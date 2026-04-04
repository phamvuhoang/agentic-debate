import * as THREE from 'three';

const POINT_COUNT = 2000;

/** Generate a humanoid point cloud: head, torso, arms, legs. */
function generateHumanoidPositions(): Float32Array {
  const positions = new Float32Array(POINT_COUNT * 3);
  let i = 0;

  function addPoint(x: number, y: number, z: number) {
    if (i >= POINT_COUNT * 3) return;
    positions[i++] = x;
    positions[i++] = y;
    positions[i++] = z;
  }

  function scatter(
    cx: number, cy: number, cz: number,
    rx: number, ry: number, rz: number,
    n: number,
  ) {
    for (let j = 0; j < n; j++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      const r = Math.cbrt(Math.random());
      addPoint(
        cx + rx * r * Math.sin(phi) * Math.cos(theta),
        cy + ry * r * Math.cos(phi),
        cz + rz * r * Math.sin(phi) * Math.sin(theta),
      );
    }
  }

  // Head
  scatter(0, 1.65, 0, 0.16, 0.20, 0.16, 280);
  // Neck
  scatter(0, 1.40, 0, 0.06, 0.06, 0.06, 50);
  // Torso upper
  scatter(0, 1.10, 0, 0.24, 0.20, 0.14, 300);
  // Torso lower
  scatter(0, 0.80, 0, 0.22, 0.15, 0.12, 200);
  // Left arm upper
  scatter(-0.34, 1.15, 0, 0.07, 0.18, 0.07, 100);
  // Left arm lower
  scatter(-0.38, 0.88, 0, 0.06, 0.16, 0.06, 80);
  // Right arm upper
  scatter(0.34, 1.15, 0, 0.07, 0.18, 0.07, 100);
  // Right arm lower
  scatter(0.38, 0.88, 0, 0.06, 0.16, 0.06, 80);
  // Left leg upper
  scatter(-0.12, 0.50, 0, 0.09, 0.20, 0.09, 150);
  // Left leg lower
  scatter(-0.13, 0.18, 0, 0.07, 0.18, 0.07, 130);
  // Right leg upper
  scatter(0.12, 0.50, 0, 0.09, 0.20, 0.09, 150);
  // Right leg lower
  scatter(0.13, 0.18, 0, 0.07, 0.18, 0.07, 130);
  // Shoulders
  scatter(0, 1.28, 0, 0.28, 0.05, 0.10, 100);
  // Fill remaining
  const remaining = (POINT_COUNT * 3 - i) / 3;
  if (remaining > 0) scatter(0, 0.9, 0, 0.22, 0.45, 0.14, remaining);

  return positions;
}

/** Per-particle random velocities for the dissolve/reform cycle. */
function generateVelocities(): Float32Array {
  const velocities = new Float32Array(POINT_COUNT * 3);
  for (let i = 0; i < POINT_COUNT; i++) {
    const i3 = i * 3;
    velocities[i3] = (Math.random() - 0.5) * 2;
    velocities[i3 + 1] = Math.random() * 1.5 + 0.5; // upward bias
    velocities[i3 + 2] = (Math.random() - 0.5) * 2;
  }
  return velocities;
}

export interface ParticleFigure {
  group: THREE.Group;
  setColor(color: THREE.Color): void;
  setActive(active: boolean): void;
  update(time: number, dt: number): void;
  dispose(): void;
}

// Animation states matching the Three.js example pattern
const enum Phase { Idle, Dissolving, Dissolved, Reforming }

export function createParticleFigure(id: string, accentHex?: string): ParticleFigure {
  const group = new THREE.Group();
  group.name = id;

  const restPositions = generateHumanoidPositions();
  const velocities = generateVelocities();

  const geometry = new THREE.BufferGeometry();
  const posAttr = new THREE.Float32BufferAttribute(restPositions.slice(), 3);
  posAttr.setUsage(THREE.DynamicDrawUsage);
  geometry.setAttribute('position', posAttr);

  const baseColor = accentHex ? new THREE.Color(accentHex) : new THREE.Color(0x888888);

  // Main points layer
  const material = new THREE.PointsMaterial({
    color: baseColor,
    size: 0.03,
    sizeAttenuation: true,
    transparent: true,
    opacity: 0.9,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
  group.add(new THREE.Points(geometry, material));

  // Glow layer
  const glowMaterial = new THREE.PointsMaterial({
    color: baseColor,
    size: 0.08,
    sizeAttenuation: true,
    transparent: true,
    opacity: 0.12,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
  group.add(new THREE.Points(geometry, glowMaterial));

  let isActive = false;
  let phase: Phase = Phase.Idle;
  let phaseTimer = 0;
  const phaseOffset = Math.random() * Math.PI * 2;

  // How far each point has dissolved (0 = at rest, 1 = fully scattered)
  const dissolveProgress = new Float32Array(POINT_COUNT);
  // Track per-point completion for the dissolve/reform wave
  const pointDone = new Uint8Array(POINT_COUNT);

  // Timing
  const DISSOLVE_SPEED = 8;
  const REFORM_SPEED = 4;
  const PAUSE_AFTER_DISSOLVE = 0.6;
  const PAUSE_AFTER_REFORM = 3.0;

  function tickIdle(time: number) {
    const arr = posAttr.array as Float32Array;
    const breathAmp = isActive ? 0.04 : 0.015;
    const breathFreq = isActive ? 2.0 : 0.8;
    const swayAmp = isActive ? 0.025 : 0.008;
    const swayFreq = isActive ? 1.4 : 0.5;

    for (let i = 0; i < POINT_COUNT; i++) {
      const i3 = i * 3;
      const oy = restPositions[i3 + 1];

      // Breathing — vertical expansion/contraction centered on torso
      const breathFactor = Math.max(0, 1 - Math.abs(oy - 1.0) / 0.8);
      const breath = Math.sin(time * breathFreq + phaseOffset + oy * 4) * breathAmp * breathFactor;

      // Lateral sway — whole body rocks gently
      const sway = Math.sin(time * swayFreq + phaseOffset) * swayAmp;

      // Per-point jitter for organic feel
      const jitter = Math.sin(time * 3 + i * 0.5) * 0.003;

      arr[i3] = restPositions[i3] + sway + jitter;
      arr[i3 + 1] = restPositions[i3 + 1] + breath;
      arr[i3 + 2] = restPositions[i3 + 2] + jitter * 0.7;
    }
    posAttr.needsUpdate = true;
  }

  function tickDissolve(dt: number): boolean {
    const arr = posAttr.array as Float32Array;
    let doneCount = 0;

    for (let i = 0; i < POINT_COUNT; i++) {
      if (pointDone[i]) { doneCount++; continue; }
      const i3 = i * 3;

      // Each particle accelerates outward with randomized speed
      const speed = DISSOLVE_SPEED * (0.5 + Math.random() * 0.5);
      dissolveProgress[i] += dt * speed * 0.3;

      if (dissolveProgress[i] >= 1) {
        dissolveProgress[i] = 1;
        pointDone[i] = 1;
        doneCount++;
      }

      const t = dissolveProgress[i];
      // Ease-out for natural deceleration
      const eased = 1 - (1 - t) * (1 - t);

      arr[i3] = restPositions[i3] + velocities[i3] * eased * 1.2;
      arr[i3 + 1] = restPositions[i3 + 1] + velocities[i3 + 1] * eased * 1.5 - t * t * 0.8;
      arr[i3 + 2] = restPositions[i3 + 2] + velocities[i3 + 2] * eased * 1.2;
    }

    posAttr.needsUpdate = true;
    return doneCount >= POINT_COUNT;
  }

  function tickReform(dt: number): boolean {
    const arr = posAttr.array as Float32Array;
    let doneCount = 0;

    for (let i = 0; i < POINT_COUNT; i++) {
      if (pointDone[i]) { doneCount++; continue; }
      const i3 = i * 3;

      dissolveProgress[i] -= dt * REFORM_SPEED * (0.3 + Math.random() * 0.4);
      if (dissolveProgress[i] <= 0) {
        dissolveProgress[i] = 0;
        pointDone[i] = 1;
        doneCount++;
        arr[i3] = restPositions[i3];
        arr[i3 + 1] = restPositions[i3 + 1];
        arr[i3 + 2] = restPositions[i3 + 2];
        continue;
      }

      const t = dissolveProgress[i];
      const eased = t * t; // ease-in for acceleration toward rest

      arr[i3] = restPositions[i3] + velocities[i3] * eased * 1.2;
      arr[i3 + 1] = restPositions[i3 + 1] + velocities[i3 + 1] * eased * 1.5 - t * t * 0.8;
      arr[i3 + 2] = restPositions[i3 + 2] + velocities[i3 + 2] * eased * 1.2;
    }

    posAttr.needsUpdate = true;
    return doneCount >= POINT_COUNT;
  }

  return {
    group,

    setColor(color: THREE.Color) {
      material.color.copy(color);
      glowMaterial.color.copy(color);
    },

    setActive(active: boolean) {
      const wasActive = isActive;
      isActive = active;

      material.size = active ? 0.04 : 0.03;
      material.opacity = active ? 1.0 : 0.75;
      glowMaterial.opacity = active ? 0.2 : 0.08;
      glowMaterial.size = active ? 0.12 : 0.08;

      // Trigger dissolve/reform on activation change
      if (active && !wasActive) {
        // Active speaker: dissolve then reform (dramatic entrance)
        phase = Phase.Dissolving;
        phaseTimer = 0;
        pointDone.fill(0);
      }
    },

    update(time: number, dt: number) {
      switch (phase) {
        case Phase.Idle:
          tickIdle(time);
          break;

        case Phase.Dissolving:
          if (tickDissolve(dt)) {
            phase = Phase.Dissolved;
            phaseTimer = 0;
          }
          break;

        case Phase.Dissolved:
          phaseTimer += dt;
          if (phaseTimer >= PAUSE_AFTER_DISSOLVE) {
            phase = Phase.Reforming;
            pointDone.fill(0);
          }
          break;

        case Phase.Reforming:
          if (tickReform(dt)) {
            phase = Phase.Idle;
            phaseTimer = 0;
          }
          break;
      }
    },

    dispose() {
      geometry.dispose();
      material.dispose();
      glowMaterial.dispose();
    },
  };
}
