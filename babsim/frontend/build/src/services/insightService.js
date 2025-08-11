import { createMockResponse } from './mockData';
import { apiRequest } from './authService';

const API_BASE_URL = 'http://localhost:8000/api';
const USE_MOCK_DATA = true;

// 목업 데이터
const mockCarModels = [
  {
    car_model_id: 'car-1',
    car_name: '아이오닉 5',
    type: 'SUV',
    release_year: 2021
  },
  {
    car_model_id: 'car-2',
    car_name: '그랜저',
    type: '세단',
    release_year: 2022
  },
  {
    car_model_id: 'car-3',
    car_name: '투싼',
    type: 'SUV',
    release_year: 2023
  }
];

const mockDesignMaterials = [
  {
    material_id: 'mat-1',
    car_model_id: 'car-1',
    material_type: '알루미늄',
    usage_area: '후드'
  },
  {
    material_id: 'mat-2',
    car_model_id: 'car-1',
    material_type: '강철',
    usage_area: '차체'
  }
];

const mockEngineeringSpecs = [
  {
    spec_id: 'spec-1',
    car_model_id: 'car-1',
    cd_value: 0.25,
    weight: 1500,
    material_al_ratio: 0.3,
    wheel_base: 2700,
    pedestrian_safety_score: 85.5,
    sensor_ready: true
  }
];

const mockSalesStats = [
  {
    car_model_id: 'car-1',
    year: 2024,
    month: 1,
    units_sold: 1500
  },
  {
    car_model_id: 'car-1',
    year: 2024,
    month: 2,
    units_sold: 1800
  }
];

const mockUserReviews = [
  {
    review_id: 'review-1',
    car_model_id: 'car-1',
    sentiment_score: 4.2,
    mentioned_features: '디자인, 성능, 안전성'
  },
  {
    review_id: 'review-2',
    car_model_id: 'car-1',
    sentiment_score: 3.8,
    mentioned_features: '연비, 편의성'
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

// 차량 모델 관련 API
export const getCarModels = async (type = '', releaseYear = '', page = 1, pageSize = 10) => {
  let filteredModels = mockCarModels;
  
  if (type) {
    filteredModels = filteredModels.filter(model => model.type === type);
  }
  if (releaseYear) {
    filteredModels = filteredModels.filter(model => model.release_year === parseInt(releaseYear));
  }
  
  const mockData = {
    count: filteredModels.length,
    next: null,
    previous: null,
    results: filteredModels
  };

  if (USE_MOCK_DATA) {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString()
    });
    if (type) params.append('type', type);
    if (releaseYear) params.append('release_year', releaseYear);

    return await simulateHttpRequest(
      `${API_BASE_URL}/insights/models/?${params}`,
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
    if (type) params.append('type', type);
    if (releaseYear) params.append('release_year', releaseYear);

    const response = await apiRequest(`${API_BASE_URL}/insights/models/?${params}`, {
      method: 'GET',
    });
    return await response.json();
  } catch (error) {
    console.error('Get car models error:', error);
    throw error;
  }
};

export const getCarModelDetail = async (carModelId) => {
  const carModel = mockCarModels.find(model => model.car_model_id === carModelId);
  if (!carModel) {
    throw new Error('차량 모델을 찾을 수 없습니다.');
  }

  const materials = mockDesignMaterials.filter(mat => mat.car_model_id === carModelId);
  const specs = mockEngineeringSpecs.filter(spec => spec.car_model_id === carModelId);
  const sales = mockSalesStats.filter(sale => sale.car_model_id === carModelId);
  const reviews = mockUserReviews.filter(review => review.car_model_id === carModelId);

  const mockData = {
    ...carModel,
    design_materials: materials,
    engineering_specs: specs,
    sales_stats: sales,
    user_reviews: reviews
  };

  if (USE_MOCK_DATA) {
    return await simulateHttpRequest(
      `${API_BASE_URL}/insights/models/${carModelId}/`,
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
    const response = await apiRequest(`${API_BASE_URL}/insights/models/${carModelId}/`, {
      method: 'GET',
    });
    return await response.json();
  } catch (error) {
    console.error('Get car model detail error:', error);
    throw error;
  }
};

// 디자인 재질 관련 API
export const getDesignMaterials = async (carModelId, materialType = '', usageArea = '') => {
  let filteredMaterials = mockDesignMaterials.filter(mat => mat.car_model_id === carModelId);
  
  if (materialType) {
    filteredMaterials = filteredMaterials.filter(mat => mat.material_type === materialType);
  }
  if (usageArea) {
    filteredMaterials = filteredMaterials.filter(mat => mat.usage_area === usageArea);
  }
  
  const mockData = {
    count: filteredMaterials.length,
    results: filteredMaterials
  };

  if (USE_MOCK_DATA) {
    const params = new URLSearchParams();
    if (materialType) params.append('material_type', materialType);
    if (usageArea) params.append('usage_area', usageArea);

    return await simulateHttpRequest(
      `${API_BASE_URL}/insights/models/${carModelId}/materials/?${params}`,
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
    const params = new URLSearchParams();
    if (materialType) params.append('material_type', materialType);
    if (usageArea) params.append('usage_area', usageArea);

    const response = await apiRequest(`${API_BASE_URL}/insights/models/${carModelId}/materials/?${params}`, {
      method: 'GET',
    });
    return await response.json();
  } catch (error) {
    console.error('Get design materials error:', error);
    throw error;
  }
};

// 공학적 스펙 관련 API
export const getEngineeringSpecs = async (carModelId) => {
  const specs = mockEngineeringSpecs.filter(spec => spec.car_model_id === carModelId);
  const mockData = {
    count: specs.length,
    results: specs
  };

  if (USE_MOCK_DATA) {
    return await simulateHttpRequest(
      `${API_BASE_URL}/insights/models/${carModelId}/specs/`,
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
    const response = await apiRequest(`${API_BASE_URL}/insights/models/${carModelId}/specs/`, {
      method: 'GET',
    });
    return await response.json();
  } catch (error) {
    console.error('Get engineering specs error:', error);
    throw error;
  }
};

// 판매 통계 관련 API
export const getSalesStats = async (carModelId, year = '', month = '', page = 1, pageSize = 12) => {
  let filteredSales = mockSalesStats.filter(sale => sale.car_model_id === carModelId);
  
  if (year) {
    filteredSales = filteredSales.filter(sale => sale.year === parseInt(year));
  }
  if (month) {
    filteredSales = filteredSales.filter(sale => sale.month === parseInt(month));
  }
  
  const mockData = {
    count: filteredSales.length,
    results: filteredSales
  };

  if (USE_MOCK_DATA) {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString()
    });
    if (year) params.append('year', year);
    if (month) params.append('month', month);

    return await simulateHttpRequest(
      `${API_BASE_URL}/insights/models/${carModelId}/sales/?${params}`,
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
    if (year) params.append('year', year);
    if (month) params.append('month', month);

    const response = await apiRequest(`${API_BASE_URL}/insights/models/${carModelId}/sales/?${params}`, {
      method: 'GET',
    });
    return await response.json();
  } catch (error) {
    console.error('Get sales stats error:', error);
    throw error;
  }
};

// 사용자 리뷰 관련 API
export const getUserReviews = async (carModelId, sentimentScoreMin = '', sentimentScoreMax = '', page = 1, pageSize = 10) => {
  let filteredReviews = mockUserReviews.filter(review => review.car_model_id === carModelId);
  
  if (sentimentScoreMin) {
    filteredReviews = filteredReviews.filter(review => review.sentiment_score >= parseFloat(sentimentScoreMin));
  }
  if (sentimentScoreMax) {
    filteredReviews = filteredReviews.filter(review => review.sentiment_score <= parseFloat(sentimentScoreMax));
  }
  
  const mockData = {
    count: filteredReviews.length,
    results: filteredReviews
  };

  if (USE_MOCK_DATA) {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString()
    });
    if (sentimentScoreMin) params.append('sentiment_score_min', sentimentScoreMin);
    if (sentimentScoreMax) params.append('sentiment_score_max', sentimentScoreMax);

    return await simulateHttpRequest(
      `${API_BASE_URL}/insights/models/${carModelId}/reviews/?${params}`,
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
    if (sentimentScoreMin) params.append('sentiment_score_min', sentimentScoreMin);
    if (sentimentScoreMax) params.append('sentiment_score_max', sentimentScoreMax);

    const response = await apiRequest(`${API_BASE_URL}/insights/models/${carModelId}/reviews/?${params}`, {
      method: 'GET',
    });
    return await response.json();
  } catch (error) {
    console.error('Get user reviews error:', error);
    throw error;
  }
};

export default {
  getCarModels,
  getCarModelDetail,
  getDesignMaterials,
  getEngineeringSpecs,
  getSalesStats,
  getUserReviews
};
