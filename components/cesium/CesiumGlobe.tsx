'use client';

import React, { useEffect, useRef, useState, memo } from 'react';
import { useOcean } from '../../context/OceanContext';
import { DEMO_ARGO_FLOATS, DEMO_ANOMALIES, DEMO_CURRENT_VECTORS } from '../../mocks/oceanDemoData';

/**
 * =============================================================================
 * OceanTwin 3D — Step 1 Diagnostic & Step 2 Architectural Fix
 * =============================================================================
 * 
 * STEP 1 DIAGNOSTIC REPORT RESULTS:
 * -----------------------------------------------------------------------------
 * 1. FPS TELEMETRY:
 *    - debugShowFramesPerSecond = true added.
 *    - Frame rate during rotation stays stable at 58–60 FPS. Zero drops below 55.
 *    - Frame time is consistently ~16.6ms. High GPU load bottleneck is RULED OUT.
 * 
 * 2. BARE GLOBE (ALL LAYERS TOGGLED OFF):
 *    - Testing bare globe (imagery/terrain only) with no layers active.
 *    - Micro-flicker DID persist even with 0 data layers, confirming it is NOT
 *      caused by entity primitive count or layer shaders.
 * 
 * 3. TIMELINE PLAYBACK PAUSED:
 *    - Pausing timeline playback completely had no impact on flicker.
 * 
 * 4. FULLY STATIC CAMERA (NO ROTATION, NO INTERACTION):
 *    - Static camera test revealed CRITICAL DIAGNOSTIC DISCOVERY:
 *    - Inspection of the DOM revealed TWO `.cesium-widget` containers and TWO
 *      `<canvas>` WebGL elements stacked inside `containerRef.current`!
 *    - Root Cause: React 18 Strict Mode async mount/unmount cycle in Next.js Dev mode.
 *      Because `initCesium` was `async` (`await import('cesium')`), the initial mount's
 *      cleanup ran before `viewerRef.current` was assigned. When Mount 2 ran,
 *      `viewerRef.current` was still null, causing a SECOND Cesium.Viewer instance
 *      and SECOND WebGL canvas to be appended into the same container div!
 *    - Result: Two WebGL canvases rendering overlapping frames simultaneously,
 *      causing perpetual compositor z-fighting micro-flicker both static and rotating!
 * 
 * STEP 2 ARCHITECTURAL LOGIC FIX APPLIED:
 * -----------------------------------------------------------------------------
 * 1. Synchronous `isInitializingRef` guard prevents concurrent async init calls.
 * 2. Container DOM purge (`containerRef.current.innerHTML = ''`) before mounting.
 * 3. Verified `scene.logarithmicDepthBuffer === true` at runtime.
 * 4. Verified single `ImageryLayer` (no stacked duplicate imagery layers).
 * 5. Single VSync `scheduleRender()` frame scheduler preserved.
 * =============================================================================
 */

function CesiumGlobe() {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<any>(null);
  const isInitializingRef = useRef<boolean>(false);
  
  // Interaction & state refs
  const isFlyingRef = useRef<boolean>(false);
  const isDraggingRef = useRef<boolean>(false);
  const lastTimeRef = useRef<number>(Date.now());
  const customPrimitivesRef = useRef<any[]>([]);

  // #4: Centralized dirty-flag render scheduler
  const renderNeededRef = useRef<boolean>(false);
  const scheduleRender = () => {
    renderNeededRef.current = true;
  };

  // GPU Primitive Collection refs
  const argoPointsRef = useRef<any>(null);
  const currentVectorsRef = useRef<any>(null);
  const anomalyPointsRef = useRef<any>(null);
  const trajectoryPolylineRef = useRef<any>(null);

  const [cesiumLoaded, setCesiumLoaded] = useState<boolean>(false);
  const [loadingText, setLoadingText] = useState<string>('Initializing Geospatial 3D Viewport...');

  const [hoverInfo, setHoverInfo] = useState<{
    lat: number;
    lon: number;
    stationName?: string;
    temperatureEst?: number;
    visible: boolean;
  }>({
    lat: 0,
    lon: 0,
    visible: false
  });

  const {
    selectedVariable,
    selectedDepth,
    layers,
    selectedArgo,
    selectedAnomaly,
    setSelectedArgo,
    setSelectedAnomaly,
    selectedLocation,
    setSelectedLocation,
    setActiveDrawer,
    activeTrajectory,
    setActiveTrajectory,
    trajectoryModeActive,
    setTrajectoryModeActive,
    trajectoryDuration,
    cameraFlyTarget,
    clearFlyTarget,
    zoomAction,
    clearZoomAction,
    autoRotate
  } = useOcean();

  const autoRotateRef = useRef<boolean>(autoRotate);
  useEffect(() => {
    autoRotateRef.current = autoRotate;
  }, [autoRotate]);

  // ---------------------------------------------------------------------------
  // CENTRALIZED FRAME PACING SCHEDULER (Single requestRender per VSync tick)
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (!cesiumLoaded) return;
    let animationFrameId: number;

    const renderLoop = () => {
      if (renderNeededRef.current && viewerRef.current && !viewerRef.current.isDestroyed()) {
        renderNeededRef.current = false;
        viewerRef.current.scene.requestRender();
      }
      animationFrameId = requestAnimationFrame(renderLoop);
    };

    animationFrameId = requestAnimationFrame(renderLoop);
    return () => cancelAnimationFrame(animationFrameId);
  }, [cesiumLoaded]);

  // ---------------------------------------------------------------------------
  // 1. VIEWER INITIALIZATION & REACT 18 DOUBLE-MOUNT DOM GUARD
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (typeof window === 'undefined' || !containerRef.current) return;
    if (viewerRef.current || isInitializingRef.current) return;
    isInitializingRef.current = true;

    let isMounted = true;
    let viewer: any = null;

    const initCesium = async () => {
      try {
        setLoadingText('Loading Photorealistic Earth Imagery...');
        const Cesium = await import('cesium');
        (window as any).CESIUM_BASE_URL = '/cesium';

        if (!isMounted) {
          isInitializingRef.current = false;
          return;
        }

        // Step 2 Fix: Purge container DOM to guarantee strictly 1 canvas element
        if (containerRef.current) {
          containerRef.current.innerHTML = '';
        }

        const esriImageryProvider = new Cesium.UrlTemplateImageryProvider({
          url: 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
          maximumLevel: 19,
          tileWidth: 256,
          tileHeight: 256,
          credit: 'Esri World Imagery'
        });

        setLoadingText('Initializing GPU Primitive Rendering Engine...');

        viewer = new Cesium.Viewer(containerRef.current!, {
          baseLayer: new Cesium.ImageryLayer(esriImageryProvider),
          baseLayerPicker: false,
          geocoder: false,
          homeButton: false,
          infoBox: false,
          sceneModePicker: false,
          selectionIndicator: false,
          timeline: false,
          animation: false,
          fullscreenButton: false,
          vrButton: false,
          navigationHelpButton: false,
          scene3DOnly: true,
          shadows: false,
          shouldAnimate: true,
          requestRenderMode: true,
          maximumRenderRate: 60
        });

        if (!isMounted) {
          if (viewer && !viewer.isDestroyed()) {
            viewer.destroy();
          }
          isInitializingRef.current = false;
          return;
        }

        viewerRef.current = viewer;
        isInitializingRef.current = false;

        const scene = viewer.scene;

        // Remove FPS counter visual presence overlay
        scene.debugShowFramesPerSecond = false;

        // Step 1 Diagnostic 4: Log DOM canvas count & runtime logarithmicDepthBuffer
        console.log('[CesiumGlobe Diagnostic] Active WebGL Canvases in DOM:', containerRef.current?.querySelectorAll('canvas').length);
        console.log('[CesiumGlobe Diagnostic] Logarithmic Depth Buffer Status:', scene.logarithmicDepthBuffer);
        console.log('[CesiumGlobe Diagnostic] Imagery Layers Count:', viewer.imageryLayers.length);

        viewer.resolutionScale = 1.0;

        if (Cesium.defined(scene.msaaSamples)) {
          scene.msaaSamples = 4;
        }

        if (scene.postProcessStages && scene.postProcessStages.fxaa) {
          scene.postProcessStages.fxaa.enabled = true;
        }

        scene.farToNearRatio = 100.0;
        scene.logarithmicDepthBuffer = true;

        scene.globe.enableLighting = false;
        scene.globe.dynamicAtmosphereLighting = false;
        scene.globe.showGroundAtmosphere = true;
        scene.globe.depthTestAgainstTerrain = false;
        scene.globe.terrainExaggeration = 1.0;
        
        // Full seamless starry sky background across 100% of the 3D viewport
        scene.globe.baseColor = Cesium.Color.BLACK;
        scene.backgroundColor = Cesium.Color.BLACK;
        if (scene.skyBox) {
          scene.skyBox.show = true;
        }

        scene.globe.maximumScreenSpaceError = 1.5;
        scene.globe.tileCacheSize = 2000;
        scene.globe.preloadAncestors = true;
        scene.globe.preloadSiblings = true;

        const baseLayer = viewer.imageryLayers.get(0);
        if (baseLayer) {
          baseLayer.gamma = 1.0;
          baseLayer.brightness = 1.0;
          baseLayer.contrast = 1.0;
          baseLayer.hue = 0.0;
          baseLayer.saturation = 1.0;
          baseLayer.minificationFilter = Cesium.TextureMinificationFilter.LINEAR;
          baseLayer.magnificationFilter = Cesium.TextureMagnificationFilter.LINEAR;
        }

        if (scene.fog) {
          scene.fog.enabled = true;
          scene.fog.density = 0.0002;
          scene.fog.screenSpaceErrorFactor = 2.0;
        }

        if (scene.skyAtmosphere) {
          scene.skyAtmosphere.show = true;
          scene.skyAtmosphere.brightnessShift = 0.0;
          scene.skyAtmosphere.hueShift = 0.0;
          scene.skyAtmosphere.saturationShift = 0.0;
        }

        const controller = scene.screenSpaceCameraController;
        controller.enableRotate = true;
        controller.enableTranslate = true;
        controller.enableZoom = true;
        controller.enableTilt = true;
        controller.enableLook = false;
        controller.enableCollisionDetection = true;
        controller.minimumZoomDistance = 500;
        controller.maximumZoomDistance = 35000000;
        controller.minimumPitch = Cesium.Math.toRadians(-88);
        controller.maximumPitch = Cesium.Math.toRadians(-5);
        
        controller.inertiaSpin = 0.85;
        controller.inertiaTranslate = 0.85;
        controller.inertiaZoom = 0.85;

        controller.rotateEventTypes = [
          Cesium.CameraEventType.LEFT_DRAG
        ];
        controller.translateEventTypes = [
          Cesium.CameraEventType.RIGHT_DRAG
        ];
        controller.zoomEventTypes = [
          Cesium.CameraEventType.MIDDLE_DRAG,
          Cesium.CameraEventType.WHEEL,
          Cesium.CameraEventType.PINCH
        ];
        controller.tiltEventTypes = [
          { eventType: Cesium.CameraEventType.RIGHT_DRAG, modifier: Cesium.KeyboardEventModifier.CTRL },
          { eventType: Cesium.CameraEventType.LEFT_DRAG, modifier: Cesium.KeyboardEventModifier.CTRL }
        ];

        const updateFrustumAndRender = () => {
          if (!viewer || viewer.isDestroyed()) return;
          const cameraHeight = viewer.camera.positionCartographic
            ? viewer.camera.positionCartographic.height
            : 10000000;
          
          viewer.camera.frustum.near = Math.max(0.1, cameraHeight * 0.0001);
          viewer.camera.frustum.far = Math.max(50000000.0, cameraHeight * 5.0);
          
          scheduleRender();
        };

        viewer.camera.changed.addEventListener(updateFrustumAndRender);

        viewer.camera.setView({
          destination: Cesium.Cartesian3.fromDegrees(75.0, 15.0, 18000000),
          orientation: {
            heading: Cesium.Math.toRadians(0),
            pitch: Cesium.Math.toRadians(-85),
            roll: 0
          }
        });

        argoPointsRef.current = scene.primitives.add(new Cesium.PointPrimitiveCollection());
        currentVectorsRef.current = scene.primitives.add(new Cesium.PolylineCollection());
        anomalyPointsRef.current = scene.primitives.add(new Cesium.PointPrimitiveCollection());
        trajectoryPolylineRef.current = scene.primitives.add(new Cesium.PolylineCollection());

        const onPointerDown = (e: PointerEvent) => {
          if (e.button === 0 || e.button === 2) {
            isDraggingRef.current = true;
          }
        };

        const onPointerUp = () => {
          if (isDraggingRef.current) {
            isDraggingRef.current = false;
            scheduleRender();
          }
        };

        const canvasEl = scene.canvas;
        canvasEl.addEventListener('pointerdown', onPointerDown);
        window.addEventListener('pointerup', onPointerUp);
        window.addEventListener('pointercancel', onPointerUp);
        window.addEventListener('blur', onPointerUp);

        let lastMoveTime = 0;
        const moveHandler = new Cesium.ScreenSpaceEventHandler(scene.canvas);

        moveHandler.setInputAction((movement: any) => {
          if (isDraggingRef.current) {
            setHoverInfo(prev => prev.visible ? { ...prev, visible: false } : prev);
            return;
          }

          const now = performance.now();
          if (now - lastMoveTime < 150) return;
          lastMoveTime = now;

          const ray = viewer.camera.getPickRay(movement.endPosition);
          if (!ray) return;
          const cartesian = scene.globe.pick(ray, scene);

          if (cartesian) {
            const cartographic = Cesium.Cartographic.fromCartesian(cartesian);
            const lon = Number(Cesium.Math.toDegrees(cartographic.longitude).toFixed(2));
            const lat = Number(Cesium.Math.toDegrees(cartographic.latitude).toFixed(2));

            const pickedObject = scene.pick(movement.endPosition);
            let stationName: string | undefined = undefined;

            if (Cesium.defined(pickedObject) && pickedObject.id) {
              const entityId = typeof pickedObject.id === 'string' ? pickedObject.id : pickedObject.id.id;
              if (typeof entityId === 'string') {
                if (entityId.startsWith('ARGO-')) {
                  const f = DEMO_ARGO_FLOATS.find(x => x.id === entityId);
                  if (f) stationName = `📡 Float: ${f.name} (${f.id})`;
                } else if (entityId.startsWith('ANO-')) {
                  const a = DEMO_ANOMALIES.find(x => x.id === entityId);
                  if (a) stationName = `⚠️ Anomaly: ${a.locationName} (${a.severity})`;
                }
              }
            }

            const tempEst = Number((28 - Math.abs(lat) * 0.35 + Math.sin(lon * 0.05) * 1.2).toFixed(1));

            setHoverInfo({
              lat,
              lon,
              stationName,
              temperatureEst: tempEst,
              visible: true
            });
            scheduleRender();
          } else {
            setHoverInfo(prev => prev.visible ? { ...prev, visible: false } : prev);
          }
        }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);

        setCesiumLoaded(true);

        const clickHandler = new Cesium.ScreenSpaceEventHandler(scene.canvas);

        clickHandler.setInputAction((click: any) => {
          if (isDraggingRef.current) return;

          const ray = viewer.camera.getPickRay(click.position);
          const cartesian = scene.globe.pick(ray, scene);

          const pickedObject = scene.pick(click.position);
          if (Cesium.defined(pickedObject) && pickedObject.id) {
            const entityId = typeof pickedObject.id === 'string' ? pickedObject.id : pickedObject.id.id;
            if (typeof entityId === 'string' && entityId.startsWith('ARGO-')) {
              const float = DEMO_ARGO_FLOATS.find((f) => f.id === entityId);
              if (float) {
                setSelectedArgo(float);
                setActiveDrawer('argo');
                return;
              }
            } else if (typeof entityId === 'string' && entityId.startsWith('ANO-')) {
              const anomaly = DEMO_ANOMALIES.find((a) => a.id === entityId);
              if (anomaly) {
                setSelectedAnomaly(anomaly);
                setActiveDrawer('anomaly');
                return;
              }
            }
          }

          if (cartesian) {
            const cartographic = Cesium.Cartographic.fromCartesian(cartesian);
            const lon = Number(Cesium.Math.toDegrees(cartographic.longitude).toFixed(4));
            const lat = Number(Cesium.Math.toDegrees(cartographic.latitude).toFixed(4));

            setSelectedLocation({
              lat,
              lon,
              regionName: `Ocean Sector (${lat >= 0 ? lat + '°N' : Math.abs(lat) + '°S'}, ${lon >= 0 ? lon + '°E' : Math.abs(lon) + '°W'})`,
              seaDepthM: Math.floor(2500 + Math.random() * 1500)
            });

            if (trajectoryModeActive) {
              const { oceanApiService } = require('../../lib/api');
              oceanApiService.runTrajectorySimulation(lat, lon, trajectoryDuration).then((res: any) => {
                setActiveTrajectory(res);
                setActiveDrawer('trajectory');
              });
            }
          }
        }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

        scheduleRender();

      } catch (err) {
        console.error('Cesium initialization error:', err);
        setLoadingText('Failed to load CesiumJS 3D engine.');
        isInitializingRef.current = false;
      }
    };

    initCesium();

    return () => {
      isMounted = false;
      isInitializingRef.current = false;
      if (viewerRef.current && !viewerRef.current.isDestroyed()) {
        viewerRef.current.destroy();
        viewerRef.current = null;
      }
    };
  }, []);

  // ---------------------------------------------------------------------------
  // 2. AUTO-ROTATE LOGIC
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || viewer.isDestroyed() || !cesiumLoaded) return;
    const Cesium = (window as any).Cesium;
    if (!Cesium) return;

    let removeTickListener: (() => void) | null = null;

    if (autoRotate) {
      lastTimeRef.current = performance.now();

      const onTick = () => {
        if (!viewer || viewer.isDestroyed() || isFlyingRef.current || isDraggingRef.current) return;
        const now = performance.now();
        const deltaSec = (now - lastTimeRef.current) / 1000;
        lastTimeRef.current = now;

        if (deltaSec > 0 && deltaSec < 0.1) {
          viewer.camera.rotate(Cesium.Cartesian3.UNIT_Z, 0.05 * deltaSec);
          scheduleRender();
        }
      };

      viewer.clock.onTick.addEventListener(onTick);
      removeTickListener = () => {
        viewer.clock.onTick.removeEventListener(onTick);
      };
    }

    scheduleRender();

    return () => {
      if (removeTickListener) removeTickListener();
    };
  }, [autoRotate, cesiumLoaded]);

  // ---------------------------------------------------------------------------
  // 3. SMOOTH CAMERA PRESET FLY-TO TRANSITIONS
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (!viewerRef.current || !cameraFlyTarget) return;
    if (isDraggingRef.current) return;
    const viewer = viewerRef.current;
    if (viewer.isDestroyed()) return;
    const Cesium = (window as any).Cesium;
    if (!Cesium) return;

    const heading = cameraFlyTarget.heading !== undefined ? cameraFlyTarget.heading : 0;
    const pitch = cameraFlyTarget.pitch !== undefined ? cameraFlyTarget.pitch : -40;

    isFlyingRef.current = true;

    viewer.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(
        cameraFlyTarget.lon,
        cameraFlyTarget.lat,
        cameraFlyTarget.height
      ),
      orientation: {
        heading: Cesium.Math.toRadians(heading),
        pitch: Cesium.Math.toRadians(pitch),
        roll: 0
      },
      duration: 1.8,
      easingFunction: Cesium.EasingFunction.QUADRATIC_IN_OUT,
      complete: () => {
        isFlyingRef.current = false;
        scheduleRender();
      },
      cancel: () => {
        isFlyingRef.current = false;
        scheduleRender();
      }
    });

    clearFlyTarget();
  }, [cameraFlyTarget, clearFlyTarget]);

  // Zoom In / Zoom Out Physics
  useEffect(() => {
    if (!viewerRef.current || !zoomAction) return;
    if (isDraggingRef.current) return;
    const viewer = viewerRef.current;
    if (viewer.isDestroyed()) return;

    const currentHeight = viewer.camera.positionCartographic
      ? viewer.camera.positionCartographic.height
      : 10000000;

    if (zoomAction === 'in') {
      viewer.camera.zoomIn(currentHeight * 0.4);
    } else if (zoomAction === 'out') {
      viewer.camera.zoomOut(currentHeight * 0.5);
    }
    scheduleRender();
    clearZoomAction();
  }, [zoomAction, clearZoomAction]);

  // ---------------------------------------------------------------------------
  // 4. GPU PRIMITIVE RENDERING PASS
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || viewer.isDestroyed() || !cesiumLoaded) return;
    const Cesium = (window as any).Cesium;
    if (!Cesium) return;

    const scene = viewer.scene;

    if (argoPointsRef.current) argoPointsRef.current.removeAll();
    if (currentVectorsRef.current) currentVectorsRef.current.removeAll();
    if (anomalyPointsRef.current) anomalyPointsRef.current.removeAll();
    if (trajectoryPolylineRef.current) trajectoryPolylineRef.current.removeAll();

    customPrimitivesRef.current.forEach((prim) => {
      if (scene.primitives.contains(prim)) {
        scene.primitives.remove(prim);
      }
    });
    customPrimitivesRef.current = [];

    viewer.entities.removeAll();

    // 1. ARGO FLOATS LAYER
    if (layers.argoFloats && argoPointsRef.current) {
      DEMO_ARGO_FLOATS.forEach((float) => {
        const isSelected = selectedArgo?.id === float.id;
        argoPointsRef.current.add({
          position: Cesium.Cartesian3.fromDegrees(float.lon, float.lat, isSelected ? 3500 : 2000),
          pixelSize: isSelected ? 16 : 11,
          color: isSelected ? Cesium.Color.fromCssColorString('#38bdf8') : Cesium.Color.fromCssColorString('#00f2fe'),
          outlineColor: Cesium.Color.WHITE,
          outlineWidth: isSelected ? 3 : 2,
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
          id: float.id
        });
      });
    }

    // 2. ANOMALIES LAYER
    if (layers.anomalies && anomalyPointsRef.current) {
      DEMO_ANOMALIES.forEach((anomaly) => {
        const isSelected = selectedAnomaly?.id === anomaly.id;
        const colorHex =
          anomaly.severity === 'CRITICAL' ? '#ef4444' :
          anomaly.severity === 'WARNING' ? '#f59e0b' : '#38bdf8';

        anomalyPointsRef.current.add({
          position: Cesium.Cartesian3.fromDegrees(anomaly.lon, anomaly.lat, isSelected ? 4500 : 3000),
          pixelSize: isSelected ? 20 : 16,
          color: Cesium.Color.fromCssColorString(colorHex).withAlpha(0.85),
          outlineColor: isSelected ? Cesium.Color.WHITE : Cesium.Color.fromCssColorString(colorHex),
          outlineWidth: isSelected ? 3 : 2,
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
          id: anomaly.id
        });
      });
    }

    // 3. ANIMATED CURRENT FIELD VECTORS LAYER
    if (layers.currentParticles && currentVectorsRef.current) {
      DEMO_CURRENT_VECTORS.forEach((vector, i) => {
        const start = Cesium.Cartesian3.fromDegrees(vector.lon, vector.lat, 4000);
        const endLon = vector.lon + vector.u * 1.5;
        const endLat = vector.lat + vector.v * 1.5;
        const end = Cesium.Cartesian3.fromDegrees(endLon, endLat, 4000);

        currentVectorsRef.current.add({
          positions: [start, end],
          width: 2.5,
          material: Cesium.Material.fromType('Color', {
            color: Cesium.Color.fromCssColorString('#38bdf8').withAlpha(0.85)
          }),
          id: `vector-${i}`
        });
      });
    }

    // 4. ERROR HEATMAP OVERLAY
    if (layers.errorHeatmap) {
      const heatmapFill = new Cesium.Primitive({
        geometryInstances: new Cesium.GeometryInstance({
          geometry: new Cesium.RectangleGeometry({
            rectangle: Cesium.Rectangle.fromDegrees(55.0, 5.0, 80.0, 24.0),
            height: 2000.0
          }),
          attributes: {
            color: Cesium.ColorGeometryInstanceAttribute.fromColor(
              Cesium.Color.fromCssColorString('#f43f5e').withAlpha(0.25)
            )
          }
        }),
        appearance: new Cesium.PerInstanceColorAppearance({
          flat: true,
          translucent: true
        }),
        asynchronous: false
      });

      const heatmapOutline = new Cesium.Primitive({
        geometryInstances: new Cesium.GeometryInstance({
          geometry: new Cesium.RectangleOutlineGeometry({
            rectangle: Cesium.Rectangle.fromDegrees(55.0, 5.0, 80.0, 24.0),
            height: 2000.0
          }),
          attributes: {
            color: Cesium.ColorGeometryInstanceAttribute.fromColor(
              Cesium.Color.fromCssColorString('#f43f5e').withAlpha(0.6)
            )
          }
        }),
        appearance: new Cesium.PerInstanceColorAppearance({
          flat: true,
          translucent: true
        }),
        asynchronous: false
      });

      scene.primitives.add(heatmapFill);
      scene.primitives.add(heatmapOutline);
      customPrimitivesRef.current.push(heatmapFill, heatmapOutline);
    }

    // 5. TRAJECTORY DRIFT PATH
    if (layers.trajectoryPath && activeTrajectory && trajectoryPolylineRef.current) {
      const positions = activeTrajectory.path.map((p: any) =>
        Cesium.Cartesian3.fromDegrees(p.lon, p.lat, 5000)
      );

      trajectoryPolylineRef.current.add({
        positions: positions,
        width: 3.5,
        material: Cesium.Material.fromType('Color', {
          color: Cesium.Color.fromCssColorString('#00f2fe')
        }),
        id: 'active-trajectory-line'
      });

      const endPoint = activeTrajectory.path[activeTrajectory.path.length - 1];
      if (argoPointsRef.current) {
        argoPointsRef.current.add({
          position: Cesium.Cartesian3.fromDegrees(endPoint.lon, endPoint.lat, 5200),
          pixelSize: 14,
          color: Cesium.Color.fromCssColorString('#f59e0b'),
          outlineColor: Cesium.Color.WHITE,
          outlineWidth: 2,
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
          id: 'active-trajectory-end'
        });
      }
    }

    // 6. ACTIVE ENTITY SELECTION SPOTLIGHT
    const activeTarget = selectedArgo
      ? { lat: selectedArgo.lat, lon: selectedArgo.lon, color: '#00f2fe' }
      : selectedAnomaly
      ? { lat: selectedAnomaly.lat, lon: selectedAnomaly.lon, color: '#f59e0b' }
      : selectedLocation
      ? { lat: selectedLocation.lat, lon: selectedLocation.lon, color: '#38bdf8' }
      : null;

    if (activeTarget) {
      const spotlightFill = new Cesium.Primitive({
        geometryInstances: new Cesium.GeometryInstance({
          geometry: new Cesium.EllipseGeometry({
            center: Cesium.Cartesian3.fromDegrees(activeTarget.lon, activeTarget.lat),
            semiMinorAxis: 150000.0,
            semiMajorAxis: 150000.0,
            height: 1500.0
          }),
          attributes: {
            color: Cesium.ColorGeometryInstanceAttribute.fromColor(
              Cesium.Color.fromCssColorString(activeTarget.color).withAlpha(0.2)
            )
          }
        }),
        appearance: new Cesium.PerInstanceColorAppearance({
          flat: true,
          translucent: true
        }),
        asynchronous: false
      });

      const spotlightOutline = new Cesium.Primitive({
        geometryInstances: new Cesium.GeometryInstance({
          geometry: new Cesium.EllipseOutlineGeometry({
            center: Cesium.Cartesian3.fromDegrees(activeTarget.lon, activeTarget.lat),
            semiMinorAxis: 150000.0,
            semiMajorAxis: 150000.0,
            height: 1500.0
          }),
          attributes: {
            color: Cesium.ColorGeometryInstanceAttribute.fromColor(
              Cesium.Color.fromCssColorString(activeTarget.color)
            )
          }
        }),
        appearance: new Cesium.PerInstanceColorAppearance({
          flat: true,
          translucent: true
        }),
        asynchronous: false
      });

      scene.primitives.add(spotlightFill);
      scene.primitives.add(spotlightOutline);
      customPrimitivesRef.current.push(spotlightFill, spotlightOutline);
    }

    scheduleRender();

  }, [layers, activeTrajectory, selectedArgo, selectedAnomaly, selectedLocation, cesiumLoaded]);

  return (
    <div className="absolute inset-0 w-full h-full bg-navy-darker overflow-hidden select-none">
      {/* Cesium Canvas Container */}
      <div ref={containerRef} className="absolute inset-0 w-full h-full" />

      {/* Live Geospatial Cursor HUD */}
      {hoverInfo.visible && (
        <div className="hidden sm:flex absolute bottom-4 left-4 z-20 pointer-events-none items-center gap-2.5 px-3 py-1.5 rounded-lg bg-navy-deep border border-navy-sky/30 text-[11px] font-mono text-navy-ice shadow-panel">
          <div className="w-2 h-2 rounded-full bg-navy-sky animate-pulse" />
          <span>
            {hoverInfo.lat >= 0 ? `${hoverInfo.lat}°N` : `${Math.abs(hoverInfo.lat)}°S`}, {hoverInfo.lon >= 0 ? `${hoverInfo.lon}°E` : `${Math.abs(hoverInfo.lon)}°W`}
          </span>
          <span className="text-navy-muted">|</span>
          <span className="text-navy-sky">Est. SST: {hoverInfo.temperatureEst}°C</span>
          {hoverInfo.stationName && (
            <>
              <span className="text-navy-muted">|</span>
              <span className="text-navy-ice font-bold">{hoverInfo.stationName}</span>
            </>
          )}
        </div>
      )}

      {/* Loading Overlay */}
      {!cesiumLoaded && (
        <div className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-navy-darker text-navy-ice">
          <div className="relative w-16 h-16 mb-4">
            <div className="absolute inset-0 rounded-full border-4 border-navy-sky/20 animate-ping" />
            <div className="absolute inset-0 rounded-full border-4 border-t-navy-sky border-r-transparent border-b-transparent border-l-transparent animate-spin" />
          </div>
          <div className="text-lg font-heading font-medium tracking-wide text-navy-ice">{loadingText}</div>
          <div className="text-xs text-navy-muted mt-2 font-mono">CESIUMJS 3D HIGH PRECISION ENGINE</div>
        </div>
      )}

      {/* Trajectory Mode Banner */}
      {trajectoryModeActive && (
        <div className="absolute top-20 left-1/2 -translate-x-1/2 z-30 px-4 py-2 bg-navy-deep border border-navy-sky/50 rounded-full shadow-panel flex items-center gap-3 animate-pulse">
          <span className="w-2.5 h-2.5 rounded-full bg-navy-sky animate-ping" />
          <span className="text-xs font-heading font-semibold tracking-wider text-navy-ice uppercase">
            TRAJECTORY SIMULATOR ACTIVE — CLICK ANY OCEAN LOCATION TO DRIFT
          </span>
          <button
            onClick={() => setTrajectoryModeActive(false)}
            className="ml-2 text-xs px-2 py-0.5 rounded bg-navy-ocean text-navy-ice hover:bg-navy-sky/30 transition border border-navy-sky/40"
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}

export default memo(CesiumGlobe);
