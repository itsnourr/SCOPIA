import React, { useState, useEffect, useRef } from "react";
import { useParams } from "react-router-dom";
import { runColmap } from "../../services/colmapService";

import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls";
import { PLYLoader } from "three/examples/jsm/loaders/PLYLoader";

export default function StudioScreen() {
  const { caseKey } = useParams(); 
  const [status, setStatus] = useState("");
  const mountRef = useRef(null);

  useEffect(() => {
    if (!caseKey) return;

    const container = mountRef.current;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(container.clientWidth, 500);
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);

    // Scene & Camera
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xaaaaaa);

    const camera = new THREE.PerspectiveCamera(
      60,
      container.clientWidth / 500,
      0.1,
      1000
    );
    camera.position.set(0, 2, 6);

    // Lights
    scene.add(new THREE.AmbientLight(0xffffff, 0.8));

    const dirLight = new THREE.DirectionalLight(0xffffff, 0.7);
    dirLight.position.set(5, 10, 7);
    dirLight.castShadow = true;
    scene.add(dirLight);

    // Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;

    // Room group
    const roomGroup = new THREE.Group();
    scene.add(roomGroup);

    // Load PLY dynamically
    const loader = new PLYLoader();
    const plyUrl = `/api/scene/${caseKey}/model`;
    
    loader.load(
      plyUrl,
      (geometry) => {
        geometry.computeVertexNormals();

        const material = new THREE.MeshStandardMaterial({
          color: 0x999999,
          roughness: 0.5,
          metalness: 0.0,
        });

        const mesh = new THREE.Mesh(geometry, material);

        // Center geometry
        const box = new THREE.Box3().setFromObject(mesh);
        const center = box.getCenter(new THREE.Vector3());
        mesh.position.sub(center);

        const size = box.getSize(new THREE.Vector3()).length();
        if (size > 100) mesh.scale.setScalar(0.1);

        roomGroup.add(mesh);
      },
      undefined,
      (err) => {
        console.error("Failed loading PLY:", err);
      }
    );

    // Animate
    const clock = new THREE.Clock();

    const animate = () => {
      controls.update();
      renderer.render(scene, camera);
      requestAnimationFrame(animate);
    };

    animate();

    // Cleanup
    return () => {
      container.removeChild(renderer.domElement);
      renderer.dispose();
    };
  }, [caseKey]);

  const handleRunColmap = async () => {
    if (!caseKey) {
      setStatus("Missing case key in URL");
      return;
    }

    setStatus("Running Colmap...");
    try {
      const response = await runColmap(caseKey);
      setStatus(response.data);
    } catch (error) {
      setStatus(error.response?.data || "Error running Colmap");
    }
  };

  return (
    <div>
      <h1 className="screen-title" style={{ paddingBottom: "0px", marginBottom: "0px" }}>3D Studio</h1>

      <div
        ref={mountRef}
        style={{ width: "1000px", height: "500px" }}
      />

      <h3 style={{ marginTop: "20px", marginBottom: "6px", color: "gray" }}>Not up-to-date?</h3>

      <button onClick={handleRunColmap}>
        Run Colmap
      </button>

      {status && (
        <pre style={{ marginTop: "10px" }}>
          {status}
        </pre>
      )}
    </div>
  );
}