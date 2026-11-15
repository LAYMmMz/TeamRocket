import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { SVGRenderer } from "three/addons/renderers/SVGRenderer.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
export default function Astronaut({
  color,
  name,
}: {
  color: string;
  name: string;
}) {
  const host = useRef<HTMLDivElement>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    if (!host.current) return;
    const el = host.current;
    let renderer: THREE.WebGLRenderer | SVGRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    } catch {
      renderer = new SVGRenderer();
      setFailed(true);
    }
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    el.appendChild(renderer.domElement);
    const scene = new THREE.Scene(),
      camera = new THREE.PerspectiveCamera(34, 1, 0.1, 100);
    camera.position.set(0, 1.2, 7.8);
    scene.add(new THREE.HemisphereLight(0xd4f5ff, 0x182332, 3));
    const light = new THREE.DirectionalLight(0xffffff, 4);
    light.position.set(3, 4, 5);
    scene.add(light);
    const rim = new THREE.PointLight(color, 8, 20);
    rim.position.set(-3, 1, 0);
    scene.add(rim);
    const astronaut = new THREE.Group();
    scene.add(astronaut);
    const suit = new THREE.MeshStandardMaterial({
      color: 0xd9e3ea,
      roughness: 0.55,
      metalness: 0.12,
    });
    const dark = new THREE.MeshStandardMaterial({
      color: 0x23303c,
      roughness: 0.5,
    });
    const accent = new THREE.MeshStandardMaterial({
      color,
      roughness: 0.3,
      metalness: 0.4,
    });
    const visor = new THREE.MeshStandardMaterial({
      color: 0x182638,
      metalness: 0.85,
      roughness: 0.13,
    });
    function sphere(
      x: number,
      y: number,
      z: number,
      sx: number,
      sy: number,
      sz: number,
      mat: THREE.Material = suit,
    ) {
      const m = new THREE.Mesh(new THREE.SphereGeometry(1, 16, 12), mat);
      m.position.set(x, y, z);
      m.scale.set(sx, sy, sz);
      astronaut.add(m);
      return m;
    }
    function box(
      x: number,
      y: number,
      z: number,
      sx: number,
      sy: number,
      sz: number,
      mat: THREE.Material = suit,
    ) {
      const m = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz), mat);
      m.position.set(x, y, z);
      astronaut.add(m);
      return m;
    }
    sphere(0, 0.35, 0, 0.59, 0.78, 0.35);
    box(0, 0.45, -0.32, 0.86, 1.15, 0.42);
    sphere(0, 1.37, 0, 0.48, 0.5, 0.44);
    sphere(0, 1.39, 0.24, 0.38, 0.33, 0.29, visor);
    sphere(0, 0.94, 0, 0.43, 0.1, 0.36, dark);
    for (const sign of [-1, 1]) {
      sphere(sign * 0.66, 0.55, 0, 0.24, 0.43, 0.24).rotation.z = sign * 0.25;
      sphere(sign * 0.82, -0.02, 0.01, 0.2, 0.39, 0.2).rotation.z = sign * 0.1;
      sphere(sign * 0.86, -0.4, 0.04, 0.19, 0.21, 0.21, dark);
      sphere(sign * 0.3, -0.66, 0, 0.27, 0.49, 0.28);
      sphere(sign * 0.3, -1.23, 0, 0.23, 0.36, 0.24);
      box(sign * 0.3, -1.52, 0.12, 0.44, 0.26, 0.67, dark);
      sphere(sign * 0.3, -0.98, 0.1, 0.24, 0.12, 0.23, accent);
      sphere(sign * 0.65, 0.72, 0.02, 0.245, 0.1, 0.245, accent);
    }
    box(0, 0.42, 0.35, 0.61, 0.42, 0.13, dark);
    box(-0.13, 0.48, 0.43, 0.17, 0.1, 0.02, accent);
    box(0.13, 0.48, 0.43, 0.13, 0.1, 0.02, accent);
    box(0, 0.3, 0.43, 0.37, 0.04, 0.02, suit);
    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(1.18, 0.008, 8, 90),
      new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.45 }),
    );
    ring.rotation.x = Math.PI / 2;
    ring.position.y = -1.77;
    scene.add(ring);
    const controls = new OrbitControls(
      camera,
      renderer.domElement as unknown as HTMLElement,
    );
    controls.target.set(0, 0, 0);
    controls.enablePan = false;
    controls.minDistance = 4;
    controls.maxDistance = 10;
    controls.enableDamping = true;
    controls.autoRotate =
      renderer instanceof THREE.WebGLRenderer &&
      !matchMedia("(prefers-reduced-motion: reduce)").matches;
    controls.autoRotateSpeed = 0.65;
    const resize = () => {
      const w = el.clientWidth,
        h = el.clientHeight;
      renderer.setSize(w, h);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    };
    const obs = new ResizeObserver(resize);
    obs.observe(el);
    resize();
    let frame = 0;
    const tick = () => {
      controls.update();
      renderer.render(scene, camera);
      frame = requestAnimationFrame(tick);
    };
    tick();
    return () => {
      cancelAnimationFrame(frame);
      obs.disconnect();
      controls.dispose();
      scene.traverse((o) => {
        if (o instanceof THREE.Mesh) o.geometry.dispose();
      });
      [suit, dark, accent, visor, ring.material].forEach((m) => m.dispose());
      if (renderer instanceof THREE.WebGLRenderer) renderer.dispose();
      renderer.domElement.remove();
    };
  }, [color]);
  return (
    <div
      className="model"
      ref={host}
      role="img"
      aria-label={`Interactive 3D suit model for ${name}. Drag to rotate, scroll to zoom.`}
    >
      {failed && (
        <span className="model-fallback">3D compatibility renderer</span>
      )}
      <span className="model-tag">CREW DIGITAL MODEL</span>
      <span className="model-caption">
        Drag to orbit · Scroll to zoom
        <br />
        Illustrative suit model, not a medical scan
      </span>
    </div>
  );
}
