import * as THREE from "three";
import { OrbitControls } from "/static/vendor/OrbitControls.js";
import { GLTFLoader } from "/static/vendor/GLTFLoader.js";
import { ColladaLoader } from "/static/vendor/ColladaLoader.js";

const loadedModels = new Map();

function box(width, height, depth, color, opacity = 1) {
  const geometry = new THREE.BoxGeometry(width, height, depth);
  const material = new THREE.MeshStandardMaterial({
    color,
    roughness: 0.62,
    metalness: 0.08,
    transparent: opacity < 1,
    opacity,
  });
  return new THREE.Mesh(geometry, material);
}

function wheel() {
  const geometry = new THREE.CylinderGeometry(0.34, 0.34, 0.28, 32);
  const tire = new THREE.Mesh(
    geometry,
    new THREE.MeshStandardMaterial({ color: 0x161b1f, roughness: 0.72 })
  );
  tire.rotation.z = Math.PI / 2;
  return tire;
}

function createTruck(scene) {
  const group = new THREE.Group();

  const chassis = box(4.9, 0.16, 1.25, 0x202a2f);
  chassis.position.set(0.2, 0.55, 0);
  group.add(chassis);

  const cargo = box(3.15, 1.35, 1.38, 0xe7ece8, 0.82);
  cargo.position.set(0.72, 1.35, 0);
  group.add(cargo);

  const cargoFrame = new THREE.LineSegments(
    new THREE.EdgesGeometry(cargo.geometry),
    new THREE.LineBasicMaterial({ color: 0x22715f })
  );
  cargoFrame.position.copy(cargo.position);
  group.add(cargoFrame);

  const cabin = box(1.25, 1.15, 1.28, 0x1f6f5d);
  cabin.position.set(-1.72, 1.15, 0);
  group.add(cabin);

  const hood = box(0.65, 0.55, 1.2, 0x195647);
  hood.position.set(-2.65, 0.9, 0);
  group.add(hood);

  const windshield = box(0.08, 0.42, 0.82, 0x9cc9df, 0.72);
  windshield.position.set(-2.31, 1.4, 0);
  group.add(windshield);

  const backDoorLeft = box(0.04, 1.12, 0.62, 0xf5f7f4);
  backDoorLeft.position.set(2.32, 1.35, -0.33);
  group.add(backDoorLeft);

  const backDoorRight = box(0.04, 1.12, 0.62, 0xf5f7f4);
  backDoorRight.position.set(2.32, 1.35, 0.33);
  group.add(backDoorRight);

  [-1.8, -0.65, 1.25, 2.05].forEach((x) => {
    [-0.72, 0.72].forEach((z) => {
      const tire = wheel();
      tire.position.set(x, 0.42, z);
      group.add(tire);
    });
  });

  const cargoFloor = box(2.7, 0.04, 1.05, 0xb5c0ba);
  cargoFloor.position.set(0.75, 0.72, 0);
  group.add(cargoFloor);

  group.rotation.y = -0.35;
  scene.add(group);
  return group;
}

function fitModel(model) {
  model.updateMatrixWorld(true);
  const box3 = new THREE.Box3().setFromObject(model);
  const size = new THREE.Vector3();
  const center = new THREE.Vector3();
  box3.getSize(size);
  box3.getCenter(center);

  const maxAxis = Math.max(size.x, size.y, size.z) || 1;
  const scale = 3.8 / maxAxis;
  model.scale.multiplyScalar(scale);

  model.updateMatrixWorld(true);
  const scaledBox = new THREE.Box3().setFromObject(model);
  const scaledCenter = new THREE.Vector3();
  scaledBox.getCenter(scaledCenter);

  model.position.x -= scaledCenter.x;
  model.position.z -= scaledCenter.z;
  model.position.y -= scaledBox.min.y;
  model.updateMatrixWorld(true);
}

function prepareMaterials(model) {
  model.traverse((object) => {
    if (!object.isMesh) return;

    object.castShadow = true;
    object.receiveShadow = true;

    const materials = Array.isArray(object.material) ? object.material : [object.material];
    materials.forEach((material) => {
      if (!material) return;
      if (material.map && material.map.image) {
        material.map.colorSpace = THREE.SRGBColorSpace;
        material.map.needsUpdate = true;
      }
      if (material.emissive) {
        material.emissive.setHex(0x000000);
      }
      material.side = THREE.DoubleSide;
      material.needsUpdate = true;
    });
  });
}

function useLoadedModel(scene, currentModel, loadedModel) {
  scene.remove(currentModel);
  prepareMaterials(loadedModel);

  const pivot = new THREE.Group();
  pivot.add(loadedModel);
  fitModel(pivot);
  pivot.userData.externalModel = true;
  scene.add(pivot);
  return pivot;
}

function loadExternalModel(modelUrl) {
  if (loadedModels.has(modelUrl)) {
    return loadedModels.get(modelUrl);
  }

  const extension = modelUrl.split(".").pop().toLowerCase();
  const promise = new Promise((resolve, reject) => {
    if (extension === "dae") {
      new ColladaLoader().load(modelUrl, (collada) => resolve(collada.scene), undefined, reject);
    } else {
      new GLTFLoader().load(modelUrl, (gltf) => resolve(gltf.scene), undefined, reject);
    }
  });

  loadedModels.set(modelUrl, promise);
  return promise;
}

function initViewer(container) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xf6f7f4);

  const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 100);
  camera.position.set(4.6, 2.4, 4.8);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, preserveDrawingBuffer: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.9;
  renderer.shadowMap.enabled = true;
  container.appendChild(renderer.domElement);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.enablePan = false;
  controls.minDistance = 3.3;
  controls.maxDistance = 8;
  controls.target.set(0, 1, 0);

  const viewBar = document.createElement("div");
  viewBar.className = "viewer-tools";
  const views = [
    ["Спереди", [0, 1.8, 5.4], [0, 0.9, 0]],
    ["Сбоку", [5.4, 1.8, 0], [0, 0.9, 0]],
    ["Сзади", [0, 1.8, -5.4], [0, 0.9, 0]],
    ["Кузов", [3.2, 2.8, -3.2], [0.9, 1.0, 0]],
  ];
  views.forEach(([label, position, target]) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.addEventListener("click", () => {
      camera.position.set(...position);
      controls.target.set(...target);
      controls.update();
    });
    viewBar.appendChild(button);
  });
  container.appendChild(viewBar);

  scene.add(new THREE.HemisphereLight(0xffffff, 0x5b625e, 1.45));
  const key = new THREE.DirectionalLight(0xffffff, 2.1);
  key.position.set(4, 5, 3);
  key.castShadow = true;
  scene.add(key);

  const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(8, 5),
    new THREE.MeshStandardMaterial({ color: 0xdde4df, roughness: 0.85 })
  );
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  scene.add(floor);

  let activeTruck = createTruck(scene);
  activeTruck.userData.externalModel = false;

  const modelUrl = container.dataset.model;
  if (modelUrl) {
    loadExternalModel(modelUrl)
      .then((model) => {
        activeTruck = useLoadedModel(scene, activeTruck, model.clone(true));
      })
      .catch(() => {
        container.classList.add("fallback-model");
      });
  }

  function resize() {
    const width = Math.max(container.clientWidth, 220);
    const height = Math.max(container.clientHeight, 180);
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
  }

  function animate() {
    if (!activeTruck.userData.externalModel) {
      activeTruck.rotation.y += 0.0025;
    }
    controls.update();
    renderer.render(scene, camera);
    requestAnimationFrame(animate);
  }

  resize();
  animate();
  window.addEventListener("resize", resize);
}

document.querySelectorAll("[data-truck-viewer]").forEach(initViewer);
