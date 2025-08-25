import { createMockResponse } from './mockData';
import { apiRequest } from './authService';

const API_BASE_URL = 'http://localhost:8000/api';
const USE_MOCK_DATA = true;

// 새로운 테이블 구조에 맞는 목업 데이터
const mockAssets = [
  {
    lib_id: 'lib-1',
    user_id: 'user-1',
    title: '현대자동차 디자인 철학에 내재하는 미의식의 신경학적 해석',
    summary: '현대자동차의 디자인 철학과 미의식이 신경학적으로 어떻게 작용하는지 분석한 연구 논문입니다. 감성적 디자인 요소와 사용자의 뇌 반응을 연관지어 설명합니다.',
    documents: '현대자동차 디자인 철학에 내재하는 미의식의 신경학적 해석.pdf',
    pdf_path: '/src/assets/asset_library/현대자동차 디자인 철학에 내재하는 미의식의 신경학적 해석.pdf',
    img_path: 'https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=400&h=300&fit=crop',
    upload_date: '2024-01-15',
    likes: 24,
    comment_count: 8,
    category: '디자인 철학'
  },
  {
    lib_id: 'lib-2',
    user_id: 'user-1',
    title: '현대 모터스튜디오 디자인 관련 문서',
    summary: '현대 모터스튜디오에서 진행하는 디자인 프로젝트와 컨셉카 개발 과정을 상세히 다룬 문서입니다. 디자인 워크숍과 프로토타입 제작 과정을 포함합니다.',
    documents: '현대 모터스튜디오_디자인 관련 문서.pdf',
    pdf_path: '/src/assets/asset_library/현대 모터스튜디오_디자인 관련 문서.pdf',
    img_path: 'https://images.unsplash.com/photo-1552519507-da3b142c6e3d?w=400&h=300&fit=crop',
    upload_date: '2024-01-20',
    likes: 31,
    comment_count: 12,
    category: '모터스튜디오'
  },
  {
    lib_id: 'lib-3',
    user_id: 'user-2',
    title: '자동차 차체 형태 디자인이 공기역학 성능에 미치는 영향에 대한 연구',
    summary: '자동차 디자인과 공기역학 성능의 상관관계를 분석한 연구 논문입니다. 다양한 차체 형태와 풍동 실험 결과를 통해 최적의 디자인 방향을 제시합니다.',
    documents: '자동차 차체 형태 디자인이 공기역학 성능에 미치는영향에 대한 연구.pdf',
    pdf_path: '/src/assets/asset_library/자동차 차체 형태 디자인이 공기역학 성능에 미치는영향에 대한 연구.pdf',
    img_path: 'https://images.unsplash.com/photo-1582639510494-c80b5de9f148?w=400&h=300&fit=crop',
    upload_date: '2024-01-25',
    likes: 18,
    comment_count: 6,
    category: '공기역학'
  },
  {
    lib_id: 'lib-4',
    user_id: 'user-3',
    title: '자동차 개발단계에서의 인간공학의 역할',
    summary: '자동차 개발 과정에서 인간공학적 요소가 어떻게 적용되는지 설명하는 문서입니다. 운전자 편의성과 안전성을 위한 디자인 원칙을 다룹니다.',
    documents: '자동차 개발단계에서의 인간공학의 역할.pdf',
    pdf_path: '/src/assets/asset_library/자동차 개발단계에서의 인간공학의 역할.pdf',
    img_path: 'https://images.unsplash.com/photo-1541899481282-d53bffe3c35d?w=400&h=300&fit=crop',
    upload_date: '2024-01-30',
    likes: 22,
    comment_count: 9,
    category: '인간공학'
  }
];

const mockComments = [
  {
    comment_id: 'comment-1',
    lib_id: 'lib-1',
    user_id: 'user-2',
    username: '디자인연구원',
    comments: '이 논문의 신경학적 접근 방식이 매우 흥미롭습니다. 디자인과 뇌 과학의 연결점을 잘 설명하고 있어요.',
    created_at: '2024-01-16T10:30:00Z',
    likes: 5,
    user_liked: false
  },
  {
    comment_id: 'comment-2',
    lib_id: 'lib-1',
    user_id: 'user-3',
    username: 'UX디자이너',
    comments: '실제 사용자 테스트 결과와 연관지어 설명한 부분이 인상적이었습니다. 디자인 의사결정에 활용할 수 있을 것 같아요.',
    created_at: '2024-01-16T14:20:00Z',
    likes: 3,
    user_liked: true
  },
  {
    comment_id: 'comment-3',
    lib_id: 'lib-2',
    user_id: 'user-4',
    username: '컨셉디자이너',
    comments: '모터스튜디오의 작업 과정을 이렇게 자세히 볼 수 있어서 좋았습니다. 프로토타입 제작 과정이 특히 흥미로웠어요.',
    created_at: '2024-01-21T09:15:00Z',
    likes: 7,
    user_liked: false
  },
  {
    comment_id: 'comment-4',
    lib_id: 'lib-2',
    user_id: 'user-5',
    username: '디자인학생',
    comments: '디자인 워크숍 참여 경험담도 포함되어 있어서 실제 현장의 분위기를 느낄 수 있었습니다.',
    created_at: '2024-01-21T16:45:00Z',
    likes: 4,
    user_liked: false
  },
  {
    comment_id: 'comment-5',
    lib_id: 'lib-3',
    user_id: 'user-6',
    username: '엔지니어',
    comments: '풍동 실험 데이터가 체계적으로 정리되어 있어서 공학적 관점에서 매우 유용했습니다.',
    created_at: '2024-01-26T11:30:00Z',
    likes: 6,
    user_liked: true
  },
  {
    comment_id: 'comment-6',
    lib_id: 'lib-4',
    user_id: 'user-7',
    username: '안전성전문가',
    comments: '인간공학적 요소가 실제 사고 예방에 어떻게 기여하는지 잘 설명되어 있습니다.',
    created_at: '2024-01-31T13:20:00Z',
    likes: 8,
    user_liked: false
  }
];

// 사용자별 좋아요 상태 관리
const userLikes = new Map();

// HTTP 요청 시뮬레이션 함수
const simulateHttpRequest = async (url, options, mockData) => {
  console.log('🌐 HTTP 요청 시뮬레이션:', {
    url,
    method: options.method,
    headers: options.headers,
    body: options.body
  });

  // 실제 fetch 요청을 보내지만 목업 응답을 반환
  try {
    const response = await fetch(url, options);
    console.log('📡 실제 HTTP 요청 전송됨:', {
      status: response.status,
      statusText: response.statusText,
      url: response.url
    });
  } catch (error) {
    console.log('❌ 네트워크 오류 (예상됨 - Django 서버가 실행되지 않음):', error.message);
  }

  // 목업 응답 반환
  const mockResponse = await createMockResponse(mockData);
  console.log('✅ 목업 응답 반환:', mockData);
  return mockResponse;
};

// Unsplash 서비스 import
import { searchImageByTitle } from './unsplashService.js';

// 자산 라이브러리 관련 API
export const getAssets = async (page = 1, pageSize = 6, search = '', searchType = 'all') => {
  let filteredAssets = [...mockAssets];
  
  if (search) {
    if (searchType === 'title') {
      filteredAssets = mockAssets.filter(asset => 
        asset.title.toLowerCase().includes(search.toLowerCase())
      );
    } else if (searchType === 'summary') {
      filteredAssets = mockAssets.filter(asset => 
        asset.summary.toLowerCase().includes(search.toLowerCase())
      );
    } else {
      // 전체 검색 (제목 + 요약)
      filteredAssets = mockAssets.filter(asset => 
        asset.title.toLowerCase().includes(search.toLowerCase()) ||
        asset.summary.toLowerCase().includes(search.toLowerCase())
      );
    }
  }
  
  // 페이지네이션 적용
  const startIndex = (page - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const paginatedAssets = filteredAssets.slice(startIndex, endIndex);
  
  const mockData = {
    count: filteredAssets.length,
    next: page * pageSize < filteredAssets.length ? page + 1 : null,
    previous: page > 1 ? page - 1 : null,
    results: paginatedAssets
  };

  if (USE_MOCK_DATA) {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString()
    });
    if (search) params.append('search', search);
    if (searchType !== 'all') params.append('search_type', searchType);

    return await simulateHttpRequest(
      `${API_BASE_URL}/library/assets/?${params}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      },
      mockData
    ).then(response => response.json());
  }

  try {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString()
    });
    if (search) params.append('search', search);
    if (searchType !== 'all') params.append('search_type', searchType);

    const response = await apiRequest(`${API_BASE_URL}/library/assets/?${params}`, {
      method: 'GET',
    });
    return await response.json();
  } catch (error) {
    console.error('Get assets error:', error);
    throw error;
  }
};

export const uploadAsset = async (documents, title, summary, category, coverPhoto = null) => {
  console.log('🚀 자산 업로드 시작:', { title, category, hasCoverPhoto: !!coverPhoto });
  
  // 커버 사진이 있으면 사용하고, 없으면 Unsplash에서 제목 관련 이미지 검색
  let imgPath;
  
  if (coverPhoto) {
    // 사용자가 업로드한 커버 사진을 사용
    imgPath = URL.createObjectURL(coverPhoto);
    console.log('📸 사용자 업로드 커버 사진 사용:', imgPath);
  } else {
    // Unsplash에서 제목 관련 이미지 검색
    console.log('🔍 Unsplash 이미지 검색 시작...');
    try {
      imgPath = await searchImageByTitle(title);
      console.log('✅ Unsplash 이미지 검색 완료:', imgPath);
    } catch (error) {
      console.error('❌ Unsplash 이미지 검색 실패:', error);
      // 기본 이미지 사용
      imgPath = `https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=400&h=300&fit=crop&auto=format&q=80`;
      console.log('🔄 기본 이미지 사용:', imgPath);
    }
  }
  
  const newAsset = {
    lib_id: `lib-${Date.now()}`,
    user_id: 'user-1',
    title: title,
    summary: summary,
    documents: documents.name,
    pdf_path: `/src/assets/asset_library/${documents.name}`,
    img_path: imgPath,
    upload_date: new Date().toISOString().split('T')[0],
    likes: 0,
    comment_count: 0,
    category: category
  };
  mockAssets.push(newAsset);

  console.log('✅ 새 자산 생성 완료:', {
    lib_id: newAsset.lib_id,
    title: newAsset.title,
    category: newAsset.category,
    img_path: newAsset.img_path
  });

  const mockData = newAsset;

  if (USE_MOCK_DATA) {
    const formData = new FormData();
    if (documents) formData.append('documents', documents);
    if (coverPhoto) formData.append('cover_photo', coverPhoto);
    formData.append('title', title);
    formData.append('summary', summary);
    formData.append('category', category);

    return await simulateHttpRequest(
      `${API_BASE_URL}/library/assets/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: formData
      },
      mockData
    ).then(response => response.json());
  }

  try {
    const formData = new FormData();
    if (documents) formData.append('documents', documents);
    if (coverPhoto) formData.append('cover_photo', coverPhoto);
    formData.append('title', title);
    formData.append('summary', summary);
    formData.append('category', category);

    const response = await apiRequest(`${API_BASE_URL}/library/assets/`, {
      method: 'POST',
      body: formData
    });
    return await response.json();
  } catch (error) {
    console.error('Upload asset error:', error);
    throw error;
  }
};

// 댓글 관련 API
export const getComments = async (libId) => {
  const assetComments = mockComments.filter(comment => comment.lib_id === libId);
  const mockData = {
    count: assetComments.length,
    results: assetComments
  };

  if (USE_MOCK_DATA) {
    return await simulateHttpRequest(
      `${API_BASE_URL}/library/assets/${libId}/comments/`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      },
      mockData
    ).then(response => response.json());
  }

  try {
    const response = await apiRequest(`${API_BASE_URL}/library/assets/${libId}/comments/`, {
      method: 'GET',
    });
    return await response.json();
  } catch (error) {
    console.error('Get comments error:', error);
    throw error;
  }
};

export const createComment = async (libId, comment) => {
  const newComment = {
    comment_id: `comment-${Date.now()}`,
    lib_id: libId,
    user_id: 'user-1',
    username: '현재사용자',
    comments: comment,
    created_at: new Date().toISOString(),
    likes: 0,
    user_liked: false
  };
  mockComments.push(newComment);

  // 댓글 수 증가
  const asset = mockAssets.find(a => a.lib_id === libId);
  if (asset) {
    asset.comment_count += 1;
  }

  const mockData = newComment;

  if (USE_MOCK_DATA) {
    return await simulateHttpRequest(
      `${API_BASE_URL}/library/comments/`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          lib_id: libId,
          comments: comment
        })
      },
      mockData
    ).then(response => response.json());
  }

  try {
    const response = await apiRequest(`${API_BASE_URL}/library/comments/`, {
      method: 'POST',
      body: JSON.stringify({
        lib_id: libId,
        comments: comment
      })
    });
    return await response.json();
  } catch (error) {
    console.error('Create comment error:', error);
    throw error;
  }
};

// 좋아요 관련 API
export const toggleAssetLike = async (libId) => {
  const asset = mockAssets.find(a => a.lib_id === libId);
  if (!asset) return;

  const userId = 'user-1'; // 실제로는 현재 로그인한 사용자 ID
  const likeKey = `${userId}-${libId}`;
  
  if (userLikes.has(likeKey)) {
    // 좋아요 취소
    userLikes.delete(likeKey);
    asset.likes = Math.max(0, asset.likes - 1);
  } else {
    // 좋아요 추가
    userLikes.set(likeKey, true);
    asset.likes += 1;
  }

  const mockData = { likes: asset.likes, user_liked: userLikes.has(likeKey) };

  if (USE_MOCK_DATA) {
    return await simulateHttpRequest(
      `${API_BASE_URL}/library/assets/${libId}/like/`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      },
      mockData
    ).then(response => response.json());
  }

  try {
    const response = await apiRequest(`${API_BASE_URL}/library/assets/${libId}/like/`, {
      method: 'POST'
    });
    return await response.json();
  } catch (error) {
    console.error('Toggle asset like error:', error);
    throw error;
  }
};

export const toggleCommentLike = async (commentId) => {
  const comment = mockComments.find(c => c.comment_id === commentId);
  if (!comment) return;

  const userId = 'user-1'; // 실제로는 현재 로그인한 사용자 ID
  const likeKey = `${userId}-${commentId}`;
  
  if (userLikes.has(likeKey)) {
    // 좋아요 취소
    userLikes.delete(likeKey);
    comment.likes = Math.max(0, comment.likes - 1);
    comment.user_liked = false;
  } else {
    // 좋아요 추가
    userLikes.set(likeKey, true);
    comment.likes += 1;
    comment.user_liked = true;
  }

  const mockData = { likes: comment.likes, user_liked: comment.user_liked };

  if (USE_MOCK_DATA) {
    return await simulateHttpRequest(
      `${API_BASE_URL}/library/comments/${commentId}/like/`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      },
      mockData
    ).then(response => response.json());
  }

  try {
    const response = await apiRequest(`${API_BASE_URL}/library/comments/${commentId}/like/`, {
      method: 'POST'
    });
    return await response.json();
  } catch (error) {
    console.error('Toggle comment like error:', error);
    throw error;
  }
};

export default {
  getAssets,
  uploadAsset,
  getComments,
  createComment,
  toggleAssetLike,
  toggleCommentLike
};
