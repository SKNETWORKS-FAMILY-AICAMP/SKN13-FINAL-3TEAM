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
      const ambientLight = new THREE.AmbientLight(0xffffff, 1.2); // 전역 조명 강화로 그림자 감소
      scene.add(ambientLight);

      const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8); // 방향성 조명 강도 감소
      directionalLight.position.set(10, 10, 5);
      directionalLight.castShadow = false; // 그림자 비활성화
      scene.add(directionalLight);

      // 추가 부드러운 조명
      const fillLight = new THREE.DirectionalLight(0xffffff, 0.6); // 채우기 조명 추가
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
        '2026 캐스퍼 일렉트릭': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/2026%20%EC%BA%90%EC%8A%A4%ED%8D%BC%20%EC%9D%BC%EB%A0%89%ED%8A%B8%EB%A6%AD.glb',
        '2026 캐스퍼': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/2026%20%EC%BA%90%EC%8A%A4%ED%8D%BC.glb',
        '그랜저 택시': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EA%B7%B8%EB%9E%9C%EC%A0%80%20%ED%83%9D%EC%8B%9C.glb',
        '그랜저 Hybrid': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EA%B7%B8%EB%9E%9C%EC%A0%80%20Hybrid.glb',
        '그랜저': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EA%B7%B8%EB%9E%9C%EC%A0%80.glb',
        '뉴 슈퍼에어로시티': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EB%89%B4%20%EC%8A%88%ED%8D%BC%EC%97%90%EC%96%B4%EB%A1%9C%EC%8B%9C%ED%8B%B0.glb',
        '뉴파워트럭': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EB%89%B4%ED%8C%8C%EC%9B%8C%ED%8A%B8%EB%9F%AD.glb',
        '더 뉴 마이티': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EB%8D%94%20%EB%89%B4%20%EB%A7%88%EC%9D%B4%ED%8B%B0.glb',
        '더 뉴 아이오닉 6': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EB%8D%94%20%EB%89%B4%20%EC%95%84%EC%9D%B4%EC%98%A4%EB%8B%89%206.glb',
        '더 뉴 엑시언트': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EB%8D%94+%EB%89%B4+%EC%97%91%EC%8B%9C%EC%96%B8%ED%8A%B8.glb',
        '더 뉴 파비스': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EB%8D%94%20%EB%89%B4%20%ED%8C%8C%EB%B9%84%EC%8A%A4.glb',
        '디 올 뉴 넥쏘': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EB%94%94%20%EC%98%AC%20%EB%89%B4%20%EB%84%A5%EC%8F%98.glb',
        '디 올 뉴 팰리세이드 Hybrid': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EB%94%94%20%EC%98%AC%20%EB%89%B4%20%ED%8C%B0%EB%A6%AC%EC%84%B8%EC%9D%B4%EB%93%9C%20Hybrid.glb',
        '디 올 뉴 팰리세이드': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EB%94%94%20%EC%98%AC%20%EB%89%B4%20%ED%8C%B0%EB%A6%AC%EC%84%B8%EC%9D%B4%EB%93%9C.glb',
        '베뉴': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EB%B2%A0%EB%89%B4.glb',
        '스타리아 라운지 리무진 Hybrid': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%8A%A4%ED%83%80%EB%A6%AC%EC%95%84%20%EB%9D%BC%EC%9A%B4%EC%A7%80%20%EB%A6%AC%EB%AC%B4%EC%A7%84%20Hybrid.glb',
        '스타리아 라운지 리무진': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%8A%A4%ED%83%80%EB%A6%AC%EC%95%84%20%EB%9D%BC%EC%9A%B4%EC%A7%80%20%EB%A6%AC%EB%AC%B4%EC%A7%84.glb',
        '스타리아 라운지 모빌리티 Hybrid': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%8A%A4%ED%83%80%EB%A6%AC%EC%95%84%20%EB%9D%BC%EC%9A%B4%EC%A7%80%20%EB%AA%A8%EB%B9%8C%EB%A6%AC%ED%8B%B0%20Hybrid.glb',
        '스타리아 라운지 모빌리티': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%8A%A4%ED%83%80%EB%A6%AC%EC%95%84%20%EB%9D%BC%EC%9A%B4%EC%A7%80%20%EB%AA%A8%EB%B9%8C%EB%A6%AC%ED%8B%B0.glb',
        '스타리아 라운지 캠퍼 Hybrid': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%8A%A4%ED%83%80%EB%A6%AC%EC%95%84%20%EB%9D%BC%EC%9A%B4%EC%A7%80%20%EC%BA%A0%ED%8D%BC%20Hybrid.glb',
        '스타리아 라운지 캠퍼': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%8A%A4%ED%83%80%EB%A6%AC%EC%95%84%20%EB%9D%BC%EC%9A%B4%EC%A7%80%20%EC%BA%A0%ED%8D%BC.glb',
        '스타리아 라운지 Hybrid': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%8A%A4%ED%83%80%EB%A6%AC%EC%95%84%20%EB%9D%BC%EC%9A%B4%EC%A7%80%20Hybrid.glb',
        '스타리아 라운지': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%8A%A4%ED%83%80%EB%A6%AC%EC%95%84%20%EB%9D%BC%EC%9A%B4%EC%A7%80.glb',
        '스타리아 킨더': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%8A%A4%ED%83%80%EB%A6%AC%EC%95%84%20%ED%82%A8%EB%8D%94.glb',
        '스타리아 Hybrid': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%8A%A4%ED%83%80%EB%A6%AC%EC%95%84%20Hybrid.glb',
        '스타리아': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%8A%A4%ED%83%80%EB%A6%AC%EC%95%84.glb',
        '싼타페 Hybrid': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%8B%BC%ED%83%80%ED%8E%98+Hybrid.glb',
        '싼타페': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%8B%BC%ED%83%80%ED%8E%98.glb',
        '쏘나타 디 엣지 Hybrid': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%8F%98%EB%82%98%ED%83%80%20%EB%94%94%20%EC%97%A3%EC%A7%80%20Hybrid.glb',
        '쏘나타 디 엣지': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%8F%98%EB%82%98%ED%83%80%20%EB%94%94%20%EC%97%A3%EC%A7%80.glb',
        '쏘나타 택시': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%8F%98%EB%82%98%ED%83%80%20%ED%83%9D%EC%8B%9C.glb',
        '쏠라티': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%8F%A0%EB%9D%BC%ED%8B%B0.glb',
        '아반떼 Hybrid': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%95%84%EB%B0%98%EB%96%BC%20Hybrid.glb',
        '아반떼 N': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%95%84%EB%B0%98%EB%96%BC%20N.glb',
        '아반떼': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%95%84%EB%B0%98%EB%96%BC.glb',
        '아이오닉 5 N': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%95%84%EC%9D%B4%EC%98%A4%EB%8B%89%205%20N.glb',
        '아이오닉 5': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%95%84%EC%9D%B4%EC%98%A4%EB%8B%89%205.glb',
        '아이오닉 9': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%95%84%EC%9D%B4%EC%98%A4%EB%8B%89%209.glb',
        '엑시언트 수소전기트럭': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%97%91%EC%8B%9C%EC%96%B8%ED%8A%B8+%EC%88%98%EC%86%8C%EC%A0%84%EA%B8%B0%ED%8A%B8%EB%9F%AD.glb',
        '유니버스 모바일 오피스': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%9C%A0%EB%8B%88%EB%B2%84%EC%8A%A4%20%EB%AA%A8%EB%B0%94%EC%9D%BC%20%EC%98%A4%ED%94%BC%EC%8A%A4.glb',
        '유니버스 수소전기버스': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%9C%A0%EB%8B%88%EB%B2%84%EC%8A%A4%20%EC%88%98%EC%86%8C%EC%A0%84%EA%B8%B0%EB%B2%84%EC%8A%A4.glb',
        '유니버스': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%9C%A0%EB%8B%88%EB%B2%84%EC%8A%A4.glb',
        '일렉시티 수소전기버스': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%9D%BC%EB%A0%89%EC%8B%9C%ED%8B%B0%20%EC%88%98%EC%86%8C%EC%A0%84%EA%B8%B0%EB%B2%84%EC%8A%A4.glb',
        '일렉시티 이층버스': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%9D%BC%EB%A0%89%EC%8B%9C%ED%8B%B0%20%EC%9D%B4%EC%B8%B5%EB%B2%84%EC%8A%A4.glb',
        '일렉시티 타운': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%9D%BC%EB%A0%89%EC%8B%9C%ED%8B%B0%20%ED%83%80%EC%9A%B4.glb',
        '일렉시티': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%9D%BC%EB%A0%89%EC%8B%9C%ED%8B%B0.glb',
        '카운티 일렉트릭': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%B9%B4%EC%9A%B4%ED%8B%B0%20%EC%9D%BC%EB%A0%89%ED%8A%B8%EB%A6%AD.glb',
        '카운티': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%B9%B4%EC%9A%B4%ED%8B%B0.glb',
        '코나 Electric': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%BD%94%EB%82%98%20Electric.glb',
        '코나 Hybrid': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%BD%94%EB%82%98%20Hybrid.glb',
        '코나': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%BD%94%EB%82%98.glb',
        '투싼 Hybrid': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%ED%88%AC%EC%8B%BC+Hybrid.glb',
        '투싼': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%ED%88%AC%EC%8B%BC.glb',
        '포터 II 특장차': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%ED%8F%AC%ED%84%B0%20II%20%ED%8A%B9%EC%9E%A5%EC%B0%A8.glb',
        '포터 II Electric 특장차': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%ED%8F%AC%ED%84%B0%20II%20Electric%20%ED%8A%B9%EC%9E%A5%EC%B0%A8.glb',
        '포터 II Electric': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%ED%8F%AC%ED%84%B0%20II%20Electric.glb',
        '포터 II': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%ED%8F%AC%ED%84%B0%20II.glb',
        'ST1': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/ST1.glb',
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