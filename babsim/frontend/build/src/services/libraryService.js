import { createMockResponse } from './mockData';
import { apiRequest } from './authService';

const API_BASE_URL = 'http://localhost:8000/api';
const USE_MOCK_DATA = true;

// 목업 데이터
const mockAssets = [
  {
    lib_id: 'lib-1',
    user_id: 'user-1',
    documents: '현대차 디자인 가이드라인.pdf',
    img_path: '/assets/design-1.jpg'
  },
  {
    lib_id: 'lib-2',
    user_id: 'user-1',
    documents: '색상 팔레트 분석.pdf',
    img_path: '/assets/color-palette.jpg'
  }
];

const mockComments = [
  {
    comment_id: 'comment-1',
    lib_id: 'lib-1',
    user_id: 'user-1',
    comments: '이 디자인 가이드라인이 매우 유용합니다.'
  }
];

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

// 자산 라이브러리 관련 API
export const getAssets = async (page = 1, pageSize = 10, search = '') => {
  let filteredAssets = mockAssets;
  if (search) {
    filteredAssets = mockAssets.filter(asset => 
      asset.documents.toLowerCase().includes(search.toLowerCase())
    );
  }
  
  const mockData = {
    count: filteredAssets.length,
    next: null,
    previous: null,
    results: filteredAssets
  };

  if (USE_MOCK_DATA) {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString()
    });
    if (search) params.append('search', search);

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

    const response = await apiRequest(`${API_BASE_URL}/library/assets/?${params}`, {
      method: 'GET',
    });
    return await response.json();
  } catch (error) {
    console.error('Get assets error:', error);
    throw error;
  }
};

export const uploadAsset = async (documents, imgPath) => {
  const newAsset = {
    lib_id: `lib-${Date.now()}`,
    user_id: 'user-1',
    documents: documents,
    img_path: imgPath
  };
  mockAssets.push(newAsset);

  const mockData = newAsset;

  if (USE_MOCK_DATA) {
    const formData = new FormData();
    if (documents) formData.append('documents', documents);
    if (imgPath) formData.append('img_path', imgPath);

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
    if (imgPath) formData.append('img_path', imgPath);

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
    comments: comment
  };
  mockComments.push(newComment);

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

export default {
  getAssets,
  uploadAsset,
  getComments,
  createComment
};
