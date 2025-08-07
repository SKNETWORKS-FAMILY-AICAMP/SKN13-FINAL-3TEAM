import { createMockResponse } from './mockData';

const API_BASE_URL = 'http://localhost:8000/api/v1';
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

// 자산 라이브러리 관련 API
export const getAssets = async (page = 1, pageSize = 10, search = '') => {
  if (USE_MOCK_DATA) {
    let filteredAssets = mockAssets;
    if (search) {
      filteredAssets = mockAssets.filter(asset => 
        asset.documents.toLowerCase().includes(search.toLowerCase())
      );
    }
    
    const mockResponse = await createMockResponse({
      count: filteredAssets.length,
      next: null,
      previous: null,
      results: filteredAssets
    });
    return await mockResponse.json();
  }

  try {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString()
    });
    if (search) params.append('search', search);

    const response = await fetch(`${API_BASE_URL}/library/assets/?${params}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    return await response.json();
  } catch (error) {
    console.error('Get assets error:', error);
    throw error;
  }
};

export const uploadAsset = async (documents, imgPath) => {
  if (USE_MOCK_DATA) {
    const newAsset = {
      lib_id: `lib-${Date.now()}`,
      user_id: 'user-1',
      documents: documents,
      img_path: imgPath
    };
    mockAssets.push(newAsset);
    
    const mockResponse = await createMockResponse(newAsset, 201);
    return await mockResponse.json();
  }

  try {
    const formData = new FormData();
    if (documents) formData.append('documents', documents);
    if (imgPath) formData.append('img_path', imgPath);

    const response = await fetch(`${API_BASE_URL}/library/assets/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
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
  if (USE_MOCK_DATA) {
    const assetComments = mockComments.filter(comment => comment.lib_id === libId);
    const mockResponse = await createMockResponse({
      count: assetComments.length,
      results: assetComments
    });
    return await mockResponse.json();
  }

  try {
    const response = await fetch(`${API_BASE_URL}/library/assets/${libId}/comments/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    return await response.json();
  } catch (error) {
    console.error('Get comments error:', error);
    throw error;
  }
};

export const createComment = async (libId, comment) => {
  if (USE_MOCK_DATA) {
    const newComment = {
      comment_id: `comment-${Date.now()}`,
      lib_id: libId,
      user_id: 'user-1',
      comments: comment
    };
    mockComments.push(newComment);
    
    const mockResponse = await createMockResponse(newComment, 201);
    return await mockResponse.json();
  }

  try {
    const response = await fetch(`${API_BASE_URL}/library/comments/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
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
