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

// HTTP 요청 시뮬레이션 함수 (목업 모드용)
const simulateHttpRequest = async (url, options, mockData) => {
  console.log('🌐 HTTP 요청 시뮬레이션:', {
    url,
    method: options.method,
    headers: options.headers,
    body: options.body
  });

  // 목업 모드에서는 실제 HTTP 요청을 보내지 않음
  console.log('🔄 목업 모드: 실제 HTTP 요청 건너뛰기');

  // 목업 응답 반환
  const mockResponse = await createMockResponse(mockData);
  console.log('✅ 목업 응답 반환:', mockData);
  return mockResponse;
};

// Unsplash 서비스 import
import { searchImageByTitle } from './unsplashService.js';

// 자산 라이브러리 관련 API
export const getAssets = async (page = 1, pageSize = 6, search = '', searchType = 'all') => {
  if (USE_MOCK_DATA) {
    // 목업 모드: 기존 로직 유지
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

  // 실제 Django API 모드
  try {
    console.log('🔍 Django 서버에서 자산 목록 조회 중...');
    
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString()
    });
    if (search) params.append('search', search);
    if (searchType !== 'all') params.append('search_type', searchType);

    const response = await apiRequest(`${API_BASE_URL}/library/assets/?${params}`, {
      method: 'GET',
    });
    
    const data = await response.json();
    console.log('✅ Django 서버 응답:', data);
    return data;
  } catch (error) {
    console.error('❌ Django 서버 자산 조회 실패:', error);
    throw error;
  }
};

export const uploadAsset = async (documents, title, summary, category, coverPhoto = null) => {
  console.log('🚀 자산 업로드 시작:', { title, category, hasCoverPhoto: !!coverPhoto });
  
  if (USE_MOCK_DATA) {
    // 목업 모드: 기존 로직 유지
    let imgPath;
    
    if (coverPhoto) {
      imgPath = URL.createObjectURL(coverPhoto);
      console.log('📸 사용자 업로드 커버 사진 사용:', imgPath);
    } else {
      console.log('🔍 Unsplash 이미지 검색 시작...');
      try {
        imgPath = await searchImageByTitle(title);
        console.log('✅ Unsplash 이미지 검색 완료:', imgPath);
      } catch (error) {
        console.error('❌ Unsplash 이미지 검색 실패:', error);
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

  // 실제 Django API 모드: 단일 POST 요청으로 통합
  try {
    console.log('🚀 Django 서버에 파일 업로드 중...');
    
    // FormData로 파일과 메타데이터를 함께 전송
    const formData = new FormData();
    formData.append('documents', documents);
    formData.append('title', title);
    formData.append('summary', summary);
    formData.append('category', category);
    
    if (coverPhoto) {
      formData.append('cover_photo', coverPhoto);
      console.log('📸 커버 사진 포함 업로드');
    }

    // Django 서버에서 S3 업로드 및 메타데이터 저장을 모두 처리
    const response = await apiRequest(`${API_BASE_URL}/library/assets/`, {
      method: 'POST',
      body: formData
    });

    const result = await response.json();
    console.log('✅ 자산 업로드 완료:', result);
    
    return result;
  } catch (error) {
    console.error('❌ Django 서버 자산 업로드 실패:', error);
    throw error;
  }
};

// 댓글 관련 API
export const getComments = async (libId) => {
  if (USE_MOCK_DATA) {
    // 목업 모드
    const assetComments = mockComments.filter(comment => comment.lib_id === libId);
    const mockData = {
      count: assetComments.length,
      results: assetComments
    };

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

  // 실제 Django API 모드
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
  if (USE_MOCK_DATA) {
    // 목업 모드
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

  // 실제 Django API 모드
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
  if (USE_MOCK_DATA) {
    // 목업 모드
    const asset = mockAssets.find(a => a.lib_id === libId);
    if (!asset) return;

    const userId = 'user-1';
    const likeKey = `${userId}-${libId}`;
    
    if (userLikes.has(likeKey)) {
      userLikes.delete(likeKey);
      asset.likes = Math.max(0, asset.likes - 1);
    } else {
      userLikes.set(likeKey, true);
      asset.likes += 1;
    }

    const mockData = { likes: asset.likes, user_liked: userLikes.has(likeKey) };

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

  // 실제 Django API 모드
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
  if (USE_MOCK_DATA) {
    // 목업 모드
    const comment = mockComments.find(c => c.comment_id === commentId);
    if (!comment) return;

    const userId = 'user-1';
    const likeKey = `${userId}-${commentId}`;
    
    if (userLikes.has(likeKey)) {
      userLikes.delete(likeKey);
      comment.likes = Math.max(0, comment.likes - 1);
      comment.user_liked = false;
    } else {
      userLikes.set(likeKey, true);
      comment.likes += 1;
      comment.user_liked = true;
    }

    const mockData = { likes: comment.likes, user_liked: comment.user_liked };

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

  // 실제 Django API 모드
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

// 자산 삭제 API
export const deleteAsset = async (assetId) => {
  if (USE_MOCK_DATA) {
    // 목업 모드
    const assetIndex = mockAssets.findIndex(a => a.lib_id === assetId);
    if (assetIndex === -1) {
      throw new Error('자산을 찾을 수 없습니다.');
    }
    
    // 관련 댓글도 삭제
    const commentIndices = mockComments
      .map((comment, index) => comment.lib_id === assetId ? index : -1)
      .filter(index => index !== -1)
      .reverse(); // 역순으로 삭제하여 인덱스 변화 방지
    
    commentIndices.forEach(index => mockComments.splice(index, 1));
    
    // 자산 삭제
    mockAssets.splice(assetIndex, 1);
    
    console.log('✅ 자산 삭제 완료:', assetId);
    return { message: '자산이 성공적으로 삭제되었습니다.' };
  }

  // 실제 Django API 모드
  try {
    const response = await apiRequest(`${API_BASE_URL}/library/assets/${assetId}/`, {
      method: 'DELETE'
    });
    return { message: '자산이 성공적으로 삭제되었습니다.' };
  } catch (error) {
    console.error('Delete asset error:', error);
    throw error;
  }
};

// 자산 수정 API
export const updateAsset = async (assetId, updateData) => {
  if (USE_MOCK_DATA) {
    // 목업 모드
    const asset = mockAssets.find(a => a.lib_id === assetId);
    if (!asset) {
      throw new Error('자산을 찾을 수 없습니다.');
    }
    
    // 업데이트할 필드만 수정
    Object.keys(updateData).forEach(key => {
      if (key in asset) {
        asset[key] = updateData[key];
      }
    });
    
    console.log('✅ 자산 수정 완료:', assetId);
    return {
      message: '자산이 성공적으로 수정되었습니다.',
      asset: asset
    };
  }

  // 실제 Django API 모드
  try {
    const formData = new FormData();
    Object.keys(updateData).forEach(key => {
      if (updateData[key] !== undefined) {
        if (key === 'documents' || key === 'cover_photo') {
          formData.append(key, updateData[key]);
        } else {
          formData.append(key, updateData[key]);
        }
      }
    });

    const response = await apiRequest(`${API_BASE_URL}/library/assets/${assetId}/`, {
      method: 'PUT',
      body: formData
    });
    
    const result = await response.json();
    console.log('✅ 자산 수정 완료:', result);
    return result;
  } catch (error) {
    console.error('Update asset error:', error);
    throw error;
  }
};

// 댓글 삭제 API
export const deleteComment = async (commentId) => {
  if (USE_MOCK_DATA) {
    // 목업 모드
    const commentIndex = mockComments.findIndex(c => c.comment_id === commentId);
    if (commentIndex === -1) {
      throw new Error('댓글을 찾을 수 없습니다.');
    }
    
    const comment = mockComments[commentIndex];
    const asset = mockAssets.find(a => a.lib_id === comment.lib_id);
    
    // 댓글 삭제
    mockComments.splice(commentIndex, 1);
    
    // 자산의 댓글 수 감소
    if (asset) {
      asset.comment_count = Math.max(0, asset.comment_count - 1);
    }
    
    console.log('✅ 댓글 삭제 완료:', commentId);
    return { message: '댓글이 성공적으로 삭제되었습니다.' };
  }

  // 실제 Django API 모드
  try {
    const response = await apiRequest(`${API_BASE_URL}/library/comments/${commentId}/`, {
      method: 'DELETE'
    });
    return { message: '댓글이 성공적으로 삭제되었습니다.' };
  } catch (error) {
    console.error('Delete comment error:', error);
    throw error;
  }
};

export default {
  getAssets,
  uploadAsset,
  getComments,
  createComment,
  toggleAssetLike,
  toggleCommentLike,
  deleteAsset,
  updateAsset,
  deleteComment
};
