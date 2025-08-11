import React, { useEffect, useRef, useState } from 'react';

const ThreeDViewer = ({ carName, className = "" }) => {
  const mountRef = useRef(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const initializedRef = useRef(false);

  useEffect(() => {
    console.log('ThreeDViewer useEffect 실행됨');
    console.log('carName:', carName);
    console.log('mountRef.current:', mountRef.current);
    console.log('mountRef.current?.clientWidth:', mountRef.current?.clientWidth);
    
    if (!carName) {
      console.log('carName이 없어서 early return');
      return;
    }

    // 이미 초기화되었다면 중복 실행 방지
    if (initializedRef.current) {
      console.log('이미 초기화됨, 중복 실행 방지');
      return;
    }

    // ref가 준비될 때까지 기다리기
    const waitForRef = () => {
      if (mountRef.current && mountRef.current.clientWidth > 0) {
        console.log('ref가 준비됨, Three.js 초기화 시작');
        initializedRef.current = true;
        initThreeJS();
      } else {
        console.log('ref가 아직 준비되지 않음, 100ms 후 재시도');
        setTimeout(waitForRef, 100);
      }
    };

    waitForRef();

    // Cleanup 함수
    return () => {
      console.log('ThreeDViewer cleanup 실행');
      initializedRef.current = false;
    };
  }, [carName]);

  const initThreeJS = async () => {
    try {
      console.log('Three.js 초기화 시작');
      
      // Three.js 모듈들을 동적으로 import
      const THREE = await import('three');
      const { GLTFLoader } = await import('three/examples/jsm/loaders/GLTFLoader');
      const { OrbitControls } = await import('three/examples/jsm/controls/OrbitControls');

      console.log('Three.js 모듈 로드 완료');

      // Scene 생성
      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0x1f2937);

      // Camera 생성
      const camera = new THREE.PerspectiveCamera(
        45, // FOV를 75에서 45로 줄여서 원근 왜곡 감소
        mountRef.current.clientWidth / mountRef.current.clientHeight,
        0.1,
        1000
      );
      camera.position.set(1.5, 1.5, 1.5); // 카메라를 3배 가깝게 조정

      // Renderer 생성
      const renderer = new THREE.WebGLRenderer({ antialias: true });
      renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;

      // DOM에 추가
      mountRef.current.appendChild(renderer.domElement);

      // 조명 추가
      const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
      scene.add(ambientLight);

      const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
      directionalLight.position.set(10, 10, 5);
      scene.add(directionalLight);

      // Controls 추가
      const controls = new OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.maxDistance = 10; // 최대 줌아웃 거리 제한
      controls.minDistance = 0.5; // 최소 줌인 거리 제한

      // Grid helper 제거 (격자선 안보이게)
      // const gridHelper = new THREE.GridHelper(10, 10);
      // scene.add(gridHelper);

      // 3D 모델 로드
      const loader = new GLTFLoader();
      const modelPath = `/models/${carName}.glb`;
      
      console.log('모델 로드 시작:', modelPath);
      console.log('차량명:', carName);

      loader.load(
        modelPath,
        (gltf) => {
          console.log('모델 로드 성공!');
          console.log('gltf 객체:', gltf);
          console.log('scene:', gltf.scene);
          console.log('animations:', gltf.animations);
          
          const model = gltf.scene;
          
          // 모델 크기 조정
          const box = new THREE.Box3().setFromObject(model);
          const center = box.getCenter(new THREE.Vector3());
          const size = box.getSize(new THREE.Vector3());
          const maxDim = Math.max(size.x, size.y, size.z);
          const scale = 3 / maxDim;
          
          console.log('모델 바운딩 박스:', { center, size, maxDim, scale });
          
          model.scale.setScalar(scale);
          model.position.sub(center.multiplyScalar(scale));
          
          scene.add(model);
          setIsLoading(false);
          console.log('3D 뷰어 초기화 완료');
        },
        (progress) => {
          console.log('로딩 진행률:', (progress.loaded / progress.total * 100) + '%');
          console.log('로딩된 바이트:', progress.loaded, '총 바이트:', progress.total);
        },
        (error) => {
          console.error('모델 로드 실패:', error);
          console.error('에러 타입:', error.type);
          console.error('에러 메시지:', error.message);
          console.error('에러 상세:', error);
          setError(`3D 모델을 불러올 수 없습니다: ${error.message}`);
          setIsLoading(false);
        }
      );

      // 애니메이션 루프
      const animate = () => {
        requestAnimationFrame(animate);
        controls.update();
        renderer.render(scene, camera);
      };
      animate();

      // 리사이즈 핸들러
      const handleResize = () => {
        if (mountRef.current && camera && renderer) {
          const width = mountRef.current.clientWidth;
          const height = mountRef.current.clientHeight;
          camera.aspect = width / height;
          camera.updateProjectionMatrix();
          renderer.setSize(width, height);
        }
      };

      window.addEventListener('resize', handleResize);

    } catch (err) {
      console.error('Three.js 초기화 실패:', err);
      setError('3D 뷰어를 초기화할 수 없습니다.');
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className={`relative ${className}`}>
        <div className="absolute inset-0 flex items-center justify-center bg-gray-700 rounded-lg z-10">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-white text-sm">3D 모델 로딩 중...</p>
          </div>
        </div>
        <div ref={mountRef} className="w-full h-full min-h-[320px] rounded-lg overflow-hidden bg-gray-700" />
      </div>
    );
  }

  if (error) {
    return (
      <div className={`relative ${className}`}>
        <div className="absolute inset-0 flex items-center justify-center bg-gray-700 rounded-lg z-10">
          <div className="text-center">
            <div className="text-red-400 text-4xl mb-4">⚠️</div>
            <p className="text-white text-sm">{error}</p>
          </div>
        </div>
        <div ref={mountRef} className="w-full h-full min-h-[320px] rounded-lg overflow-hidden bg-gray-700" />
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      <div ref={mountRef} className="w-full h-full min-h-[320px] rounded-lg overflow-hidden" />
    </div>
  );
};

export default ThreeDViewer;
