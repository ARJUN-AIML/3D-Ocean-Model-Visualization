/**
 * 4D Ocean & Realistic Earth Visualizer
 * Cinematic Fly-To Physics + Global Ultra-Clear Anisotropic Rendering
 * Powered by Three.js (r128) & WebGL
 */

(function () {
  'use strict';

  const MONTH_NAMES = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];

  // --- Global Application State ---
  const state = {
    activeVar: 'natural', // 'natural' | 'temp' | 'salinity' | 'chloro' | 'currents'
    depth: 0,
    month: 7,
    timePlaying: false,
    rotationSpeed: 0.0006,
    sunAngle: 120,       // Sun Orbit Angle
    atmoDensity: 1.0,    // Atmospheric Physics Density Scale
    vibrancy: 1.25,      // Color Saturation & Vibrancy Boost
    cloudOpacity: 0.55,  // Cloud Layer Opacity Density
    isPaused: false,
    layers: {
      atmosphere: true,
      clouds: true,
      currents: true,
      argoFloats: true,
      nightLights: true,
      starfield: true
    },

    // Ultra-Smooth Cinematic Fly-To Camera State
    flyState: {
      active: false,
      progress: 0,
      duration: 75, // ~1.25 seconds @ 60fps
      startPos: new THREE.Vector3(),
      targetPos: new THREE.Vector3(),
      startLookAt: new THREE.Vector3(),
      targetLookAt: new THREE.Vector3(),
      peakArc: 0.8
    }
  };

  function lonLatToVector3(lon, lat, radius) {
    const phi = (90 - lat) * (Math.PI / 180);
    const theta = (lon + 180) * (Math.PI / 180);
    const x = -(radius * Math.sin(phi) * Math.cos(theta));
    const y = radius * Math.cos(phi);
    const z = radius * Math.sin(phi) * Math.sin(theta);
    return new THREE.Vector3(x, y, z);
  }

  const PRESETS = {
    space: { pos: new THREE.Vector3(0, 1.8, 6.5), target: new THREE.Vector3(0, 0, 0) },
    na: { pos: lonLatToVector3(-95, 38, 5.5), target: new THREE.Vector3(0, 0, 0) },
    eu: { pos: lonLatToVector3(15, 48, 5.5), target: new THREE.Vector3(0, 0, 0) },
    asia: { pos: lonLatToVector3(80, 22, 5.5), target: new THREE.Vector3(0, 0, 0) },
    sa: { pos: lonLatToVector3(-60, -15, 5.5), target: new THREE.Vector3(0, 0, 0) },
    polar: { pos: lonLatToVector3(20, -60, 5.5), target: new THREE.Vector3(0, 0, 0) }
  };

  const ARGO_STATIONS = [
    { id: 'ARGO-5906234', name: 'North Atlantic Subpolar Gyre', lon: -42.5, lat: 56.2, tempSurf: 11.4, salSurf: 35.1, status: 'Active (2,000m CTD)' },
    { id: 'ARGO-6903210', name: 'Gulf Stream Extension', lon: -62.1, lat: 38.4, tempSurf: 24.8, salSurf: 36.5, status: 'Active (2,000m CTD)' },
    { id: 'ARGO-4902188', name: 'Equatorial Pacific (El Niño Float)', lon: -140.2, lat: 0.5, tempSurf: 27.9, salSurf: 34.8, status: 'Active (2,000m CTD)' },
    { id: 'ARGO-2901552', name: 'Southern Ocean ACC Jet', lon: 20.4, lat: -54.8, tempSurf: 2.1, salSurf: 33.9, status: 'Active (2,000m CTD)' },
    { id: 'ARGO-1901844', name: 'Arabian Sea Monsoon Station', lon: 65.8, lat: 15.2, tempSurf: 28.5, salSurf: 36.2, status: 'Active (2,000m CTD)' },
    { id: 'ARGO-3900981', name: 'Kuroshio Extension Meander', lon: 152.4, lat: 34.1, tempSurf: 22.3, salSurf: 34.9, status: 'Active (2,000m CTD)' }
  ];

  let baseNasaImage = null;
  let texDay = null, texNight = null, texSpec = null, texNormal = null;

  function applyAnisotropy(texture) {
    if (!renderer || !texture) return;
    const maxAnisotropy = renderer.capabilities.getMaxAnisotropy();
    texture.anisotropy = maxAnisotropy;
    texture.minFilter = THREE.LinearMipmapLinearFilter;
    texture.magFilter = THREE.LinearFilter;
    texture.needsUpdate = true;
  }

  function loadTextures(callback) {
    const loader = new THREE.TextureLoader();
    let loadedCount = 0;
    const total = 4;

    function checkDone() {
      loadedCount++;
      if (loadedCount >= total && callback) callback();
    }

    loader.load('assets/earth_day.jpg', (t) => { t.encoding = THREE.sRGBEncoding; t.wrapS = THREE.RepeatWrapping; applyAnisotropy(t); texDay = t; checkDone(); });
    loader.load('assets/earth_night.jpg', (t) => { t.encoding = THREE.sRGBEncoding; t.wrapS = THREE.RepeatWrapping; applyAnisotropy(t); texNight = t; checkDone(); });
    loader.load('assets/earth_specular.jpg', (t) => { t.wrapS = THREE.RepeatWrapping; applyAnisotropy(t); texSpec = t; checkDone(); });
    loader.load('assets/earth_normal.jpg', (t) => { t.wrapS = THREE.RepeatWrapping; applyAnisotropy(t); texNormal = t; checkDone(); });

    const img = new Image();
    img.crossOrigin = 'Anonymous';
    img.onload = () => { baseNasaImage = img; };
    img.src = 'assets/earth_day.jpg';
  }

  // --- Ocean Velocity Fields ---
  function getOceanCurrentVelocity(lon, lat) {
    let u = 0.15 * Math.cos(lat * 0.05);
    let v = 0.0;

    const dLatGS = lat - (24 + 0.32 * (lon + 80));
    const dLonGS = (lon + 55) / 22;
    const gsStrength = Math.exp(-Math.pow(dLatGS / 7, 2) - Math.pow(dLonGS, 2));
    if (lon > -85 && lon < -20 && lat > 20 && lat < 52) {
      u += 1.8 * gsStrength; v += 1.2 * gsStrength;
    }

    const dLatKS = lat - (18 + 0.3 * (lon - 120));
    const dLonKS = (lon - 145) / 20;
    const ksStrength = Math.exp(-Math.pow(dLatKS / 6, 2) - Math.pow(dLonKS, 2));
    if (lon > 115 && lon < 170 && lat > 15 && lat < 45) {
      u += 1.7 * ksStrength; v += 1.1 * ksStrength;
    }

    if (lat < -40 && lat > -65) {
      const accJet = Math.exp(-Math.pow((lat + 52) / 8, 2));
      u += (1.6 + 0.3 * Math.sin(lon * 0.06)) * accJet;
      v += 0.2 * Math.cos(lon * 0.08) * accJet;
    }

    const eqStrength = Math.exp(-Math.pow(lat / 12, 2));
    u -= 1.3 * eqStrength;

    const agStrength = Math.exp(-Math.pow((lon - 30) / 8, 2) - Math.pow((lat + 28) / 8, 2));
    u -= 0.6 * agStrength; v -= 1.6 * agStrength;

    return { u, v, speed: Math.sqrt(u * u + v * v) };
  }

  // --- Global 4D Heatmap Generator ---
  function create4DOceanTexture(variable, depthMeters, monthIdx) {
    if (variable === 'natural' && texDay) return texDay;

    const w = 4096, h = 2048;
    const canvas = document.createElement('canvas');
    canvas.width = w; canvas.height = h;
    const ctx = canvas.getContext('2d');

    if (baseNasaImage) {
      ctx.drawImage(baseNasaImage, 0, 0, w, h);
    } else {
      ctx.fillStyle = '#0f172a'; ctx.fillRect(0, 0, w, h);
    }

    const imgData = ctx.getImageData(0, 0, w, h);
    const data = imgData.data;

    const monthRad = (monthIdx / 12) * Math.PI * 2;
    const seasonalTilt = Math.sin(monthRad) * 11.5;
    const thermoclineFactor = Math.exp(-depthMeters / 420);

    for (let y = 0; y < h; y++) {
      const lat = 90 - (y / h) * 180;

      for (let x = 0; x < w; x++) {
        const lon = (x / w) * 360 - 180;
        const idx = (y * w + x) * 4;

        const origR = data[idx];
        const origG = data[idx + 1];
        const origB = data[idx + 2];

        const isOcean = (origB > origR + 4 && origB > origG - 8) || (origR < 35 && origG < 55 && origB < 95);

        if (isOcean && variable !== 'currents') {
          let targetR = 10, targetG = 25, targetB = 60;

          if (variable === 'temp') {
            const effLat = lat - seasonalTilt;
            let surfTemp = 29.5 * Math.pow(Math.cos((effLat * Math.PI) / 185), 1.3) - 2.0;

            const dLatGS = lat - (24 + 0.32 * (lon + 80));
            const dLonGS = (lon + 55) / 22;
            const gsWarmth = 7.5 * Math.exp(-Math.pow(dLatGS / 9, 2) - Math.pow(dLonGS, 2));
            if (lon > -90 && lon < -10) surfTemp += gsWarmth;

            const dLatKS = lat - (18 + 0.3 * (lon - 120));
            const dLonKS = (lon - 145) / 20;
            const ksWarmth = 6.5 * Math.exp(-Math.pow(dLatKS / 8, 2) - Math.pow(dLonKS, 2));
            if (lon > 110 && lon < 175) surfTemp += ksWarmth;

            const temp = 2.0 + (surfTemp - 2.0) * thermoclineFactor;
            const normT = Math.max(0, Math.min(1.0, (temp + 2.0) / 32.0));

            if (normT < 0.25) {
              const t = normT * 4;
              targetR = 10; targetG = Math.floor(t * 160); targetB = Math.floor(220 - t * 40);
            } else if (normT < 0.5) {
              const t = (normT - 0.25) * 4;
              targetR = Math.floor(t * 20); targetG = 160 + Math.floor(t * 85); targetB = Math.floor(180 - t * 160);
            } else if (normT < 0.75) {
              const t = (normT - 0.5) * 4;
              targetR = Math.floor(20 + t * 230); targetG = 245; targetB = 20;
            } else {
              const t = (normT - 0.75) * 4;
              targetR = 255; targetG = Math.floor(245 - t * 220); targetB = 20;
            }
          } else if (variable === 'salinity') {
            let psu = 35.0 + 1.6 * Math.sin((Math.abs(lat) / 30) * Math.PI);
            const gyreNH = 1.8 * Math.exp(-Math.pow((lat - 28) / 10, 2));
            const gyreSH = 1.6 * Math.exp(-Math.pow((lat + 28) / 10, 2));
            psu += (gyreNH + gyreSH);
            const dAmazon = Math.sqrt(Math.pow((lon + 50) / 12, 2) + Math.pow((lat - 5) / 6, 2));
            psu -= 3.2 * Math.exp(-dAmazon);

            const normS = Math.max(0, Math.min(1.0, (psu - 32.0) / 5.8));
            targetR = Math.floor(normS * 150); targetG = Math.floor((1.0 - normS) * 220); targetB = Math.floor(110 + normS * 145);
          } else if (variable === 'chloro') {
            const highLatBloom = 1.0 / (1.0 + Math.exp(-(Math.abs(lat) - 42) / 6));
            let chloro = 0.08 + highLatBloom * 2.8;
            const upwCanary = Math.exp(-Math.pow((lon + 18) / 8, 2) - Math.pow((lat - 22) / 10, 2));
            const upwPeru = Math.exp(-Math.pow((lon + 78) / 8, 2) - Math.pow((lat + 15) / 12, 2));
            chloro += (upwCanary * 3.2 + upwPeru * 3.5);

            const normC = Math.max(0, Math.min(1.0, chloro / 5.0));
            targetR = Math.floor(normC * 170); targetG = Math.floor(35 + normC * 220); targetB = Math.floor((1.0 - normC) * 150);
          }

          data[idx]     = Math.floor(targetR * 0.75 + origR * 0.25);
          data[idx + 1] = Math.floor(targetG * 0.75 + origG * 0.25);
          data[idx + 2] = Math.floor(targetB * 0.75 + origB * 0.25);
        }
      }
    }

    ctx.putImageData(imgData, 0, 0);
    const tex = new THREE.CanvasTexture(canvas);
    tex.encoding = THREE.sRGBEncoding;
    tex.wrapS = THREE.RepeatWrapping;
    applyAnisotropy(tex);
    return tex;
  }

  // --- Three.js Setup & Lighting ---
  let scene, camera, renderer, controls, raycaster, mouse;
  let earthGroup, earthMesh, cloudMesh, innerAtmoMesh, outerAtmoMesh;
  let sunLight, fillLight, ambientLight, starParticles;
  let earthShaderMaterial;
  let flowParticleGroup, flowParticles = [];
  let argoMarkerGroup = [];

  function init() {
    const container = document.getElementById('canvas-container');

    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x02040a);

    camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.copy(PRESETS.space.pos); // Global view in space

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: "high-performance" });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.35;
    container.appendChild(renderer.domElement);

    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 3.0;
    controls.maxDistance = 25.0;

    raycaster = new THREE.Raycaster();
    mouse = new THREE.Vector2();

    createSunLighting();
    createStarfield();

    loadTextures(() => {
      createEarthSystem();
      createOceanCurrentParticles();
      createARGOStations();

      window.addEventListener('resize', onWindowResize);
      renderer.domElement.addEventListener('pointerdown', onCanvasClick);
      bindUIEvents();
      updateVariableLegend();
      animate();
    });
  }

  function createSunLighting() {
    sunLight = new THREE.DirectionalLight(0xffffff, 2.8);
    updateSunPosition();
    scene.add(sunLight);

    ambientLight = new THREE.AmbientLight(0xdbeafe, 0.45);
    scene.add(ambientLight);

    fillLight = new THREE.DirectionalLight(0x38bdf8, 0.5);
    fillLight.position.set(-30, -10, -25);
    scene.add(fillLight);
  }

  function updateSunPosition() {
    const rad = (state.sunAngle * Math.PI) / 180;
    const sunX = Math.cos(rad) * 45;
    const sunZ = Math.sin(rad) * 45;
    if (sunLight) sunLight.position.set(sunX, 15, sunZ);

    if (earthShaderMaterial && earthShaderMaterial.uniforms.uSunDirection) {
      const sunDir = new THREE.Vector3(sunX, 15, sunZ).normalize();
      earthShaderMaterial.uniforms.uSunDirection.value.copy(sunDir);
    }
  }

  function createStarfield() {
    const count = 3500;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);

    const colorPalette = [new THREE.Color(0x9bb0ff), new THREE.Color(0xffffff), new THREE.Color(0xfff4ea)];

    for (let i = 0; i < count; i++) {
      const radius = 130 + Math.random() * 120;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);

      positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = radius * Math.cos(phi);

      const col = colorPalette[Math.floor(Math.random() * colorPalette.length)];
      colors[i * 3] = col.r; colors[i * 3 + 1] = col.g; colors[i * 3 + 2] = col.b;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({ size: 0.16, vertexColors: true, transparent: true, opacity: 0.85 });
    starParticles = new THREE.Points(geometry, material);
    scene.add(starParticles);
  }

  // --- Earth Mesh System & Crystal-Clear Vibrancy Shader ---
  function createEarthSystem() {
    earthGroup = new THREE.Group();
    earthGroup.rotation.z = (23.44 * Math.PI) / 180;
    scene.add(earthGroup);

    const initialTex = create4DOceanTexture(state.activeVar, state.depth, state.month);

    const sunDir = new THREE.Vector3(
      Math.cos((state.sunAngle * Math.PI) / 180) * 45, 15,
      Math.sin((state.sunAngle * Math.PI) / 180) * 45
    ).normalize();

    earthShaderMaterial = new THREE.ShaderMaterial({
      uniforms: {
        uDayTexture: { value: initialTex },
        uNightTexture: { value: texNight },
        uSpecularMap: { value: texSpec },
        uNormalMap: { value: texNormal },
        uSunDirection: { value: sunDir },
        uVibrancy: { value: state.vibrancy },
        uEnableNightLights: { value: state.layers.nightLights ? 1.0 : 0.0 }
      },
      vertexShader: `
        varying vec3 vNormal;
        varying vec2 vUv;
        varying vec3 vWorldPosition;
        void main() {
          vUv = uv;
          vNormal = normalize((modelMatrix * vec4(normal, 0.0)).xyz);
          vec4 worldPos = modelMatrix * vec4(position, 1.0);
          vWorldPosition = worldPos.xyz;
          gl_Position = projectionMatrix * viewMatrix * worldPos;
        }
      `,
      fragmentShader: `
        uniform sampler2D uDayTexture;
        uniform sampler2D uNightTexture;
        uniform sampler2D uSpecularMap;
        uniform sampler2D uNormalMap;
        uniform vec3 uSunDirection;
        uniform float uVibrancy;
        uniform float uEnableNightLights;

        varying vec3 vNormal;
        varying vec2 vUv;
        varying vec3 vWorldPosition;

        void main() {
          vec3 normal = normalize(vNormal);
          float dotNL = dot(normal, uSunDirection);

          float dayFactor = smoothstep(-0.15, 0.25, dotNL);

          vec4 dayColor = texture2D(uDayTexture, vUv);
          vec4 nightColor = texture2D(uNightTexture, vUv) * vec4(1.4, 1.15, 0.75, 1.0) * uEnableNightLights;

          vec4 finalColor = mix(nightColor, dayColor, dayFactor);

          vec3 rgb = finalColor.rgb;
          float luma = dot(rgb, vec3(0.2126, 0.7152, 0.0722));
          rgb = mix(vec3(luma), rgb, uVibrancy);
          rgb = (rgb - 0.5) * 1.08 + 0.5;

          float specMask = texture2D(uSpecularMap, vUv).r;
          vec3 viewDir = normalize(cameraPosition - vWorldPosition);
          vec3 halfDir = normalize(uSunDirection + viewDir);
          float specInt = pow(max(dot(normal, halfDir), 0.0), 32.0) * specMask * dayFactor;

          gl_FragColor = vec4(rgb + vec3(specInt * 0.95), 1.0);
        }
      `
    });

    const earthGeo = new THREE.SphereGeometry(2.0, 256, 256);
    earthMesh = new THREE.Mesh(earthGeo, earthShaderMaterial);
    earthGroup.add(earthMesh);

    // 3D Clouds
    const cloudGeo = new THREE.SphereGeometry(2.025, 192, 192);
    const cloudMat = new THREE.MeshPhongMaterial({
      transparent: true,
      opacity: state.cloudOpacity,
      blending: THREE.NormalBlending
    });
    cloudMesh = new THREE.Mesh(cloudGeo, cloudMat);
    earthGroup.add(cloudMesh);

    new THREE.TextureLoader().load('assets/earth_clouds.png', (tex) => {
      tex.encoding = THREE.sRGBEncoding;
      tex.wrapS = THREE.RepeatWrapping;
      applyAnisotropy(tex);
      cloudMat.map = tex;
      cloudMat.needsUpdate = true;
    });

    // Inner Atmospheric Glow
    const innerAtmoGeo = new THREE.SphereGeometry(2.05, 96, 96);
    const innerAtmoMat = new THREE.ShaderMaterial({
      uniforms: { uDensity: { value: state.atmoDensity } },
      vertexShader: `
        varying vec3 vNormal;
        void main() {
          vNormal = normalize(normalMatrix * normal);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform float uDensity;
        varying vec3 vNormal;
        void main() {
          float intensity = pow(0.65 - dot(vNormal, vec3(0.0, 0.0, 1.0)), 2.0);
          gl_FragColor = vec4(0.35, 0.70, 1.0, 1.0) * intensity * 0.70 * uDensity;
        }
      `,
      blending: THREE.AdditiveBlending, side: THREE.BackSide, transparent: true
    });
    innerAtmoMesh = new THREE.Mesh(innerAtmoGeo, innerAtmoMat);
    earthGroup.add(innerAtmoMesh);

    // Outer Atmospheric Halo
    const outerAtmoGeo = new THREE.SphereGeometry(2.20, 64, 64);
    const outerAtmoMat = new THREE.ShaderMaterial({
      uniforms: { uDensity: { value: state.atmoDensity } },
      vertexShader: `
        varying vec3 vNormal;
        void main() {
          vNormal = normalize(normalMatrix * normal);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform float uDensity;
        varying vec3 vNormal;
        void main() {
          float intensity = pow(0.55 - dot(vNormal, vec3(0, 0, 1.0)), 3.2);
          gl_FragColor = vec4(0.3, 0.65, 1.0, 1.0) * intensity * 0.65 * uDensity;
        }
      `,
      blending: THREE.AdditiveBlending, side: THREE.BackSide, transparent: true
    });
    outerAtmoMesh = new THREE.Mesh(outerAtmoGeo, outerAtmoMat);
    earthGroup.add(outerAtmoMesh);
  }

  // --- Ocean Current Particles ---
  function createOceanCurrentParticles() {
    flowParticleGroup = new THREE.Group();
    earthGroup.add(flowParticleGroup);

    const count = 3000;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);

    flowParticles = [];

    for (let i = 0; i < count; i++) {
      const lon = (Math.random() * 360) - 180;
      const lat = (Math.random() * 140) - 70;
      const pos = lonLatToVector3(lon, lat, 2.012);

      positions[i * 3] = pos.x; positions[i * 3 + 1] = pos.y; positions[i * 3 + 2] = pos.z;
      colors[i * 3] = 0.2; colors[i * 3 + 1] = 0.8; colors[i * 3 + 2] = 1.0;

      flowParticles.push({ lon, lat, age: Math.random() * 100, maxAge: 80 + Math.random() * 80 });
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
      size: 0.036, vertexColors: true, transparent: true, opacity: 0.95, blending: THREE.AdditiveBlending
    });

    const particleSystem = new THREE.Points(geometry, material);
    flowParticleGroup.add(particleSystem);
  }

  function updateFlowParticles() {
    if (!flowParticleGroup || !flowParticleGroup.children[0]) return;

    const pointsObj = flowParticleGroup.children[0];
    const posAttr = pointsObj.geometry.attributes.position;
    const colAttr = pointsObj.geometry.attributes.color;
    const depthSlowdown = Math.max(0.15, 1.0 - state.depth / 2500);

    for (let i = 0; i < flowParticles.length; i++) {
      const p = flowParticles[i];
      p.age += 1;

      if (p.age >= p.maxAge) {
        p.lon = (Math.random() * 360) - 180; p.lat = (Math.random() * 140) - 70; p.age = 0;
      }

      const vec = getOceanCurrentVelocity(p.lon, p.lat);
      p.lon += vec.u * 0.12 * depthSlowdown;
      p.lat += vec.v * 0.12 * depthSlowdown;

      if (p.lon > 180) p.lon -= 360;
      if (p.lon < -180) p.lon += 360;

      const pos = lonLatToVector3(p.lon, p.lat, 2.012);
      posAttr.setXYZ(i, pos.x, pos.y, pos.z);

      const normSpeed = Math.min(1.0, vec.speed / 2.2);
      if (normSpeed < 0.33) colAttr.setXYZ(i, 0.2, 0.8, 1.0);
      else if (normSpeed < 0.66) colAttr.setXYZ(i, 0.1, 0.9, 0.4);
      else colAttr.setXYZ(i, 1.0, 0.6, 0.1);
    }

    posAttr.needsUpdate = true;
    colAttr.needsUpdate = true;
  }

  // --- ARGO Buoy Markers ---
  function createARGOStations() {
    const buoyGroup = new THREE.Group();
    earthGroup.add(buoyGroup);
    argoMarkerGroup = [];

    ARGO_STATIONS.forEach(st => {
      const pos = lonLatToVector3(st.lon, st.lat, 2.02);

      const geo = new THREE.SphereGeometry(0.048, 16, 16);
      const mat = new THREE.MeshBasicMaterial({ color: 0xf59e0b });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.copy(pos);
      mesh.userData = st;

      const ringGeo = new THREE.RingGeometry(0.055, 0.078, 24);
      const ringMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8, side: THREE.DoubleSide, transparent: true, opacity: 0.85 });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.position.copy(pos); ring.lookAt(new THREE.Vector3(0, 0, 0));
      mesh.add(ring);

      buoyGroup.add(mesh);
      argoMarkerGroup.push(mesh);
    });
  }

  // --- Ultra-Smooth Cinematic Fly-To Physics (Arc + Cubic Ease) ---
  function triggerSmoothFlyTo(targetPos, targetLookAt = new THREE.Vector3(0, 0, 0), flyDist = 5.2) {
    const f = state.flyState;
    f.startPos.copy(camera.position);
    f.startLookAt.copy(controls.target);

    // Orient target position vector to specified distance
    f.targetPos.copy(targetPos).normalize().multiplyScalar(flyDist);
    f.targetLookAt.copy(targetLookAt);

    f.progress = 0;
    f.active = true;
  }

  function updateFlyToPhysics() {
    const f = state.flyState;
    if (!f.active) return;

    f.progress += 1 / f.duration;

    if (f.progress >= 1.0) {
      f.progress = 1.0;
      f.active = false;
    }

    const p = f.progress;
    // Cubic Ease In Out Math
    const easeP = p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;

    // Smooth Altitude Arc Boost
    const arcBoost = Math.sin(p * Math.PI) * f.peakArc;

    const currentPos = new THREE.Vector3().lerpVectors(f.startPos, f.targetPos, easeP);
    currentPos.addScaledVector(currentPos.clone().normalize(), arcBoost);

    const currentLookAt = new THREE.Vector3().lerpVectors(f.startLookAt, f.targetLookAt, easeP);

    camera.position.copy(currentPos);
    controls.target.copy(currentLookAt);
  }

  function onCanvasClick(e) {
    const rect = renderer.domElement.getBoundingClientRect();
    mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

    raycaster.setFromCamera(mouse, camera);

    // 1. First check ARGO buoys
    const argoHits = raycaster.intersectObjects(argoMarkerGroup);
    if (argoHits.length > 0) {
      const st = argoHits[0].object.userData;
      openARGOModal(st);
      return;
    }

    // 2. Click Anywhere on Globe -> Smooth Fly-To Surface Transition!
    if (earthMesh) {
      const earthHits = raycaster.intersectObject(earthMesh);
      if (earthHits.length > 0) {
        const hitWorldPoint = earthHits[0].point;
        // Transform world point into globe local coordinate system
        const localPoint = earthGroup.worldToLocal(hitWorldPoint.clone());
        triggerSmoothFlyTo(hitWorldPoint, new THREE.Vector3(0, 0, 0), 4.8);
      }
    }
  }

  function openARGOModal(st) {
    const modal = document.getElementById('argo-modal');
    if (!modal) return;

    document.getElementById('modal-argo-id').textContent = st.id;
    document.getElementById('modal-argo-name').textContent = st.name;
    document.getElementById('modal-argo-pos').textContent = `${Math.abs(st.lat)}° ${st.lat >= 0 ? 'N' : 'S'}, ${Math.abs(st.lon)}° ${st.lon >= 0 ? 'E' : 'W'}`;
    document.getElementById('modal-argo-temp').textContent = `${st.tempSurf}°C`;

    modal.classList.add('active');

    const canvas = document.getElementById('argo-chart-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width = canvas.clientWidth;
    const h = canvas.height = canvas.clientHeight;

    ctx.clearRect(0, 0, w, h);

    ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)'; ctx.lineWidth = 1;
    for (let d = 0; d <= 2000; d += 500) {
      const y = (d / 2000) * (h - 30) + 15;
      ctx.beginPath(); ctx.moveTo(40, y); ctx.lineTo(w - 10, y); ctx.stroke();
      ctx.fillStyle = '#94a3b8'; ctx.font = '10px monospace';
      ctx.fillText(`${d}m`, 5, y + 3);
    }

    ctx.strokeStyle = '#f43f5e'; ctx.lineWidth = 2.5; ctx.beginPath();
    for (let d = 0; d <= 2000; d += 50) {
      const t = 2.2 + (st.tempSurf - 2.2) * Math.exp(-d / 380);
      const x = 40 + ((t - 0) / 30) * (w - 50);
      const y = (d / 2000) * (h - 30) + 15;
      if (d === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();

    ctx.strokeStyle = '#38bdf8'; ctx.lineWidth = 2.0; ctx.setLineDash([4, 4]); ctx.beginPath();
    for (let d = 0; d <= 2000; d += 50) {
      const s = 34.5 + (st.salSurf - 34.5) * Math.exp(-d / 600);
      const x = 40 + ((s - 32) / 6) * (w - 50);
      const y = (d / 2000) * (h - 30) + 15;
      if (d === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke(); ctx.setLineDash([]);
  }

  function updateVariableLegend() {
    const titleEl = document.getElementById('legend-var-name');
    const barEl = document.getElementById('legend-color-bar');
    const minEl = document.getElementById('legend-min');
    const maxEl = document.getElementById('legend-max');

    if (state.activeVar === 'natural') {
      if (titleEl) titleEl.textContent = 'NATURAL SATELLITE VIEW';
      if (barEl) barEl.style.background = 'linear-gradient(90deg, #1d4ed8, #059669, #d97706, #ffffff)';
      if (minEl) minEl.textContent = 'Ocean Bathymetry';
      if (maxEl) maxEl.textContent = 'Relief Elevation';
    } else if (state.activeVar === 'temp') {
      if (titleEl) titleEl.textContent = 'SEA TEMPERATURE (°C)';
      if (barEl) barEl.style.background = 'linear-gradient(90deg, #050530, #0044ff, #00ffaa, #ffff00, #ff0000)';
      if (minEl) minEl.textContent = '-2°C';
      if (maxEl) maxEl.textContent = '30°C';
    } else if (state.activeVar === 'salinity') {
      if (titleEl) titleEl.textContent = 'OCEAN SALINITY (PSU)';
      if (barEl) barEl.style.background = 'linear-gradient(90deg, #10b981, #38bdf8, #8b5cf6)';
      if (minEl) minEl.textContent = '32.0';
      if (maxEl) maxEl.textContent = '37.5';
    } else if (state.activeVar === 'chloro') {
      if (titleEl) titleEl.textContent = 'CHLOROPHYLL-A (mg/m³)';
      if (barEl) barEl.style.background = 'linear-gradient(90deg, #0c1b33, #10b981, #f59e0b)';
      if (minEl) minEl.textContent = '0.05';
      if (maxEl) maxEl.textContent = '5.0+';
    } else {
      if (titleEl) titleEl.textContent = 'CURRENT SPEED (m/s)';
      if (barEl) barEl.style.background = 'linear-gradient(90deg, #38bdf8, #10b981, #f59e0b, #f43f5e)';
      if (minEl) minEl.textContent = '0.1 m/s';
      if (maxEl) maxEl.textContent = '2.2 m/s';
    }
  }

  function update4DOceanTexture() {
    if (earthShaderMaterial && earthShaderMaterial.uniforms.uDayTexture) {
      const newTex = create4DOceanTexture(state.activeVar, state.depth, state.month);
      earthShaderMaterial.uniforms.uDayTexture.value = newTex;
      earthShaderMaterial.needsUpdate = true;
    }
  }

  function flyToPreset(presetKey) {
    const preset = PRESETS[presetKey];
    if (!preset) return;

    triggerSmoothFlyTo(preset.pos, preset.target, preset.pos.length());

    document.querySelectorAll('.preset-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.preset === presetKey);
    });
  }

  function updateHUD() {
    const camDist = camera.position.distanceTo(new THREE.Vector3(0, 0, 0));
    const altKm = Math.round((camDist - 2.0) * 3178);
    const altEl = document.getElementById('hud-alt');
    if (altEl) altEl.textContent = `${altKm.toLocaleString()} km`;

    const normCam = camera.position.clone().normalize();
    const lat = Math.round(Math.asin(normCam.y) * (180 / Math.PI));
    const lon = Math.round(Math.atan2(normCam.x, normCam.z) * (180 / Math.PI));

    const latEl = document.getElementById('hud-lat');
    const lonEl = document.getElementById('hud-lon');
    if (latEl) latEl.textContent = `${Math.abs(lat)}° ${lat >= 0 ? 'N' : 'S'}`;
    if (lonEl) lonEl.textContent = `${Math.abs(lon)}° ${lon >= 0 ? 'E' : 'W'}`;

    const depthEl = document.getElementById('hud-depth');
    if (depthEl) depthEl.textContent = `${state.depth}m`;
  }

  function bindUIEvents() {
    document.querySelectorAll('.var-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.var-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.activeVar = btn.dataset.var;
        updateVariableLegend();
        update4DOceanTexture();
      });
    });

    const depthSlider = document.getElementById('slider-depth');
    const depthVal = document.getElementById('val-depth');
    if (depthSlider) {
      depthSlider.addEventListener('input', (e) => {
        state.depth = parseInt(e.target.value, 10);
        if (depthVal) depthVal.textContent = `${state.depth}m`;
        update4DOceanTexture();
      });
    }

    const timeSlider = document.getElementById('slider-time');
    const monthBadge = document.getElementById('badge-month');
    if (timeSlider) {
      timeSlider.addEventListener('input', (e) => {
        state.month = parseInt(e.target.value, 10);
        if (monthBadge) monthBadge.textContent = MONTH_NAMES[state.month];
        update4DOceanTexture();
      });
    }

    const btnTimePlay = document.getElementById('btn-time-play');
    if (btnTimePlay) {
      btnTimePlay.addEventListener('click', () => {
        state.timePlaying = !state.timePlaying;
        btnTimePlay.textContent = state.timePlaying ? 'PAUSE' : 'PLAY';
      });
    }

    const speedSlider = document.getElementById('slider-speed');
    const speedVal = document.getElementById('val-speed');
    if (speedSlider) {
      speedSlider.addEventListener('input', (e) => {
        state.rotationSpeed = parseFloat(e.target.value);
        if (speedVal) speedVal.textContent = `${(state.rotationSpeed * 10000).toFixed(1)}x`;
      });
    }

    const sunSlider = document.getElementById('slider-sun');
    const sunVal = document.getElementById('val-sun');
    if (sunSlider) {
      sunSlider.addEventListener('input', (e) => {
        state.sunAngle = parseInt(e.target.value, 10);
        if (sunVal) sunVal.textContent = `${state.sunAngle}°`;
        updateSunPosition();
      });
    }

    const atmoSlider = document.getElementById('slider-atmo');
    const atmoVal = document.getElementById('val-atmo');
    if (atmoSlider) {
      atmoSlider.addEventListener('input', (e) => {
        state.atmoDensity = parseFloat(e.target.value);
        if (atmoVal) atmoVal.textContent = `${state.atmoDensity.toFixed(1)}x`;
        if (innerAtmoMesh && innerAtmoMesh.material.uniforms.uDensity) {
          innerAtmoMesh.material.uniforms.uDensity.value = state.atmoDensity;
        }
        if (outerAtmoMesh && outerAtmoMesh.material.uniforms.uDensity) {
          outerAtmoMesh.material.uniforms.uDensity.value = state.atmoDensity;
        }
      });
    }

    const vibSlider = document.getElementById('slider-vibrancy');
    const vibVal = document.getElementById('val-vibrancy');
    if (vibSlider) {
      vibSlider.addEventListener('input', (e) => {
        state.vibrancy = parseFloat(e.target.value);
        if (vibVal) vibVal.textContent = `${state.vibrancy.toFixed(2)}x`;
        if (earthShaderMaterial && earthShaderMaterial.uniforms.uVibrancy) {
          earthShaderMaterial.uniforms.uVibrancy.value = state.vibrancy;
        }
      });
    }

    const cloudSlider = document.getElementById('slider-clouds');
    const cloudVal = document.getElementById('val-clouds');
    if (cloudSlider) {
      cloudSlider.addEventListener('input', (e) => {
        state.cloudOpacity = parseFloat(e.target.value);
        if (cloudVal) cloudVal.textContent = `${state.cloudOpacity.toFixed(2)}x`;
        if (cloudMesh && cloudMesh.material) {
          cloudMesh.material.opacity = state.cloudOpacity;
        }
      });
    }

    const pauseBtn = document.getElementById('btn-pause');
    if (pauseBtn) {
      pauseBtn.addEventListener('click', () => {
        state.isPaused = !state.isPaused;
        pauseBtn.classList.toggle('active', state.isPaused);
        pauseBtn.querySelector('span').textContent = state.isPaused ? 'RESUME' : 'PAUSE';
      });
    }

    const togglePairs = [
      { id: 'toggle-atmo', key: 'atmosphere', obj: [innerAtmoMesh, outerAtmoMesh] },
      { id: 'toggle-clouds', key: 'clouds', obj: [cloudMesh] },
      { id: 'toggle-currents', key: 'currents', obj: [flowParticleGroup] },
      { id: 'toggle-argo', key: 'argoFloats', custom: (active) => {
        argoMarkerGroup.forEach(m => { m.visible = active; });
      }},
      { id: 'toggle-nightlights', key: 'nightLights', custom: (active) => {
        if (earthShaderMaterial && earthShaderMaterial.uniforms.uEnableNightLights) {
          earthShaderMaterial.uniforms.uEnableNightLights.value = active ? 1.0 : 0.0;
        }
      }},
      { id: 'toggle-stars', key: 'starfield', obj: [starParticles] }
    ];

    togglePairs.forEach(t => {
      const el = document.getElementById(t.id);
      if (el) {
        el.addEventListener('click', () => {
          state.layers[t.key] = !state.layers[t.key];
          el.classList.toggle('active', state.layers[t.key]);
          if (t.obj) t.obj.forEach(o => { if (o) o.visible = state.layers[t.key]; });
          if (t.custom) t.custom(state.layers[t.key]);
        });
      }
    });

    document.querySelectorAll('.preset-btn').forEach(btn => {
      btn.addEventListener('click', () => flyToPreset(btn.dataset.preset));
    });

    const btnZoomIn = document.getElementById('btn-zoom-in');
    if (btnZoomIn) {
      btnZoomIn.addEventListener('click', () => {
        if (!camera || !controls) return;
        const dist = camera.position.distanceTo(controls.target);
        const targetDist = Math.max(3.2, dist * 0.7);
        const dir = camera.position.clone().sub(controls.target).normalize();
        const targetPos = controls.target.clone().add(dir.multiplyScalar(targetDist));
        triggerSmoothFlyTo(targetPos, controls.target, targetDist);
      });
    }

    const btnZoomOut = document.getElementById('btn-zoom-out');
    if (btnZoomOut) {
      btnZoomOut.addEventListener('click', () => {
        if (!camera || !controls) return;
        const dist = camera.position.distanceTo(controls.target);
        const targetDist = Math.min(22.0, dist * 1.4);
        const dir = camera.position.clone().sub(controls.target).normalize();
        const targetPos = controls.target.clone().add(dir.multiplyScalar(targetDist));
        triggerSmoothFlyTo(targetPos, controls.target, targetDist);
      });
    }

    const btnZoomReset = document.getElementById('btn-zoom-reset');
    if (btnZoomReset) {
      btnZoomReset.addEventListener('click', () => flyToPreset('space'));
    }

    const modalClose = document.getElementById('modal-close');
    const modal = document.getElementById('argo-modal');
    if (modalClose && modal) {
      modalClose.addEventListener('click', () => modal.classList.remove('active'));
    }
  }

  function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  }

  // --- Main Animation Loop ---
  function animate() {
    requestAnimationFrame(animate);

    if (!state.isPaused && earthMesh) earthMesh.rotation.y += state.rotationSpeed;
    if (!state.isPaused && cloudMesh) cloudMesh.rotation.y += state.rotationSpeed * 1.15;

    if (state.timePlaying && !state.isPaused) {
      if (Math.random() < 0.04) {
        state.month = (state.month + 1) % 12;
        const timeSlider = document.getElementById('slider-time');
        const monthBadge = document.getElementById('badge-month');
        if (timeSlider) timeSlider.value = state.month;
        if (monthBadge) monthBadge.textContent = MONTH_NAMES[state.month];
        update4DOceanTexture();
      }
    }

    if (state.layers.currents && !state.isPaused) {
      updateFlowParticles();
    }

    updateFlyToPhysics();

    controls.update();
    updateHUD();
    renderer.render(scene, camera);
  }

  window.addEventListener('DOMContentLoaded', init);
})();
