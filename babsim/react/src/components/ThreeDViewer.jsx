import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

const ThreeDViewer = ({ carName }) => {
  const mountRef = useRef(null);

  useEffect(() => {
    if (mountRef.current && carName) {
      // Scene setup
      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0x111827);

      // Camera setup - 왼쪽 아래에서 올려다보는 각도
      const camera = new THREE.PerspectiveCamera(45, mountRef.current.clientWidth / mountRef.current.clientHeight, 0.1, 1000); // FOV를 60에서 45로 줄여서 원근감 감소
      camera.position.set(-12, -4, 12); // 카메라 거리를 늘려서 원근감 감소
      camera.lookAt(0, 0, 0);

      // Renderer setup
      const renderer = new THREE.WebGLRenderer({ antialias: true });
      renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
      renderer.shadowMap.enabled = false; // 그림자 비활성화로 입체감 감소
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      mountRef.current.appendChild(renderer.domElement);

      // Lighting - 입체감을 줄이기 위해 조명 조정
      const ambientLight = new THREE.AmbientLight(0xffffff, 0.8); // 전역 조명 강화로 그림자 감소
      scene.add(ambientLight);

      const directionalLight = new THREE.DirectionalLight(0xffffff, 0.4); // 방향성 조명 강도 감소
      directionalLight.position.set(10, 10, 5);
      directionalLight.castShadow = false; // 그림자 비활성화
      scene.add(directionalLight);

      // 추가 부드러운 조명
      const fillLight = new THREE.DirectionalLight(0xffffff, 0.3); // 채우기 조명 추가
      fillLight.position.set(-10, 5, -10);
      scene.add(fillLight);

      // Controls setup
      const controls = new OrbitControls(camera, renderer.domElement);
      controls.target.set(0, 0, 0);
      controls.enableZoom = false;
      controls.enablePan = false;
      controls.maxDistance = 20; // 최대 거리 증가
      controls.minDistance = 8; // 최소 거리 증가
      controls.maxPolarAngle = Math.PI / 2; // 수평선 위로만 회전 가능
      controls.minPolarAngle = 0; // 수평선 아래로는 회전 불가
      
      // 부드러운 회전을 위한 설정
      controls.enableDamping = true; // 댐핑 활성화로 부드러운 움직임
      controls.dampingFactor = 0.05; // 댐핑 강도 (낮을수록 부드러움)
      controls.rotateSpeed = 0.5; // 회전 속도 감소 (기본값 1.0)
      controls.enableSmoothing = true; // 스무딩 활성화
      
      // 초기 각도 설정 - 왼쪽 아래에서 올려다보는 구도 유지
      controls.azimuthAngle = Math.PI / 4; // 45도 (왼쪽)
      controls.polarAngle = Math.PI / 3; // 60도 (아래에서 올려다보는 각도)
      controls.update();

      // GLTF Loader
      const loader = new GLTFLoader();
      
      // 사용 가능한 GLB 파일 목록
      const availableModels = {
        '쏘나타 디 엣지': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%8F%98%EB%82%98%ED%83%80+%EB%94%94+%EC%97%A3%EC%A7%80.glb',
    '산타페': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%82%B0%ED%83%80%ED%8E%98.glb',
    '아이오닉 5': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%95%84%EC%9D%B4%EC%98%A4%EB%8B%89+5.glb',
    '코나': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%BD%94%EB%82%98.glb',
    '포터2': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%ED%8F%AC%ED%84%B02.glb'
      };
      
      const modelPath = availableModels[carName];
      
      if (!modelPath) {
        console.warn(`GLB model not available for: ${carName}`);
        // 모델이 없을 때 기본 차량 모델 사용
        const defaultModelPath = 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/쏘나타 디 엣지.glb';
        loadModel(defaultModelPath);
      } else {
        loadModel(modelPath);
      }
      
      function loadModel(path) {
        loader.load(
          path,
          (gltf) => {
            const model = gltf.scene;
            
            // Model scaling and positioning
            const box = new THREE.Box3().setFromObject(model);
            const center = box.getCenter(new THREE.Vector3());
            const size = box.getSize(new THREE.Vector3());
            const maxDim = Math.max(size.x, size.y, size.z);
            const scale = 20 / maxDim; // 4에서 8로 증가하여 2배 확대
            
            model.scale.setScalar(scale);
            const scaledCenter = center.clone().multiplyScalar(scale);
            model.position.sub(scaledCenter);
            
            scene.add(model);
            controls.target.set(0, 0, 0);
            controls.update();
          },
          (progress) => {
            console.log('Loading progress:', (progress.loaded / progress.total * 100) + '%');
          },
          (error) => {
            console.error('Error loading model:', error);
            console.error('Model path attempted:', path);
          }
        );
      }

      // Animation loop
      const animate = () => {
        requestAnimationFrame(animate);
        controls.update();
        renderer.render(scene, camera);
      };
      animate();

      // Handle resize
      const handleResize = () => {
        if (mountRef.current) {
          const width = mountRef.current.clientWidth;
          const height = mountRef.current.clientHeight;
          camera.aspect = width / height;
          camera.updateProjectionMatrix();
          renderer.setSize(width, height);
        }
      };

      window.addEventListener('resize', handleResize);

      // Cleanup
      return () => {
        window.removeEventListener('resize', handleResize);
        if (mountRef.current) {
          mountRef.current.removeChild(renderer.domElement);
        }
        renderer.dispose();
      };
    }
  }, [carName]);

  return (
    <div 
      ref={mountRef} 
      className="w-full h-full"
      style={{ backgroundColor: '#111827' }}
    />
  );
};

export default ThreeDViewer;
