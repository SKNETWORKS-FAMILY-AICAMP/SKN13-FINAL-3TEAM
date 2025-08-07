import { createMockResponse } from './mockData';

const API_BASE_URL = 'http://localhost:8000/api/v1';
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

// 차량 모델 관련 API
export const getCarModels = async (type = '', releaseYear = '', page = 1, pageSize = 10) => {
  if (USE_MOCK_DATA) {
    let filteredModels = mockCarModels;
    
    if (type) {
      filteredModels = filteredModels.filter(model => model.type === type);
    }
    if (releaseYear) {
      filteredModels = filteredModels.filter(model => model.release_year === parseInt(releaseYear));
    }
    
    const mockResponse = await createMockResponse({
      count: filteredModels.length,
      next: null,
      previous: null,
      results: filteredModels
    });
    return await mockResponse.json();
  }

  try {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString()
    });
    if (type) params.append('type', type);
    if (releaseYear) params.append('release_year', releaseYear);

    const response = await fetch(`${API_BASE_URL}/insights/models/?${params}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    return await response.json();
  } catch (error) {
    console.error('Get car models error:', error);
    throw error;
  }
};

export const getCarModelDetail = async (carModelId) => {
  if (USE_MOCK_DATA) {
    const carModel = mockCarModels.find(model => model.car_model_id === carModelId);
    if (!carModel) {
      throw new Error('차량 모델을 찾을 수 없습니다.');
    }

    const materials = mockDesignMaterials.filter(mat => mat.car_model_id === carModelId);
    const specs = mockEngineeringSpecs.filter(spec => spec.car_model_id === carModelId);
    const sales = mockSalesStats.filter(sale => sale.car_model_id === carModelId);
    const reviews = mockUserReviews.filter(review => review.car_model_id === carModelId);

    const mockResponse = await createMockResponse({
      ...carModel,
      design_materials: materials,
      engineering_specs: specs,
      sales_stats: sales,
      user_reviews: reviews
    });
    return await mockResponse.json();
  }

  try {
    const response = await fetch(`${API_BASE_URL}/insights/models/${carModelId}/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    return await response.json();
  } catch (error) {
    console.error('Get car model detail error:', error);
    throw error;
  }
};

// 디자인 재질 관련 API
export const getDesignMaterials = async (carModelId, materialType = '', usageArea = '') => {
  if (USE_MOCK_DATA) {
    let filteredMaterials = mockDesignMaterials.filter(mat => mat.car_model_id === carModelId);
    
    if (materialType) {
      filteredMaterials = filteredMaterials.filter(mat => mat.material_type === materialType);
    }
    if (usageArea) {
      filteredMaterials = filteredMaterials.filter(mat => mat.usage_area === usageArea);
    }
    
    const mockResponse = await createMockResponse({
      count: filteredMaterials.length,
      results: filteredMaterials
    });
    return await mockResponse.json();
  }

  try {
    const params = new URLSearchParams();
    if (materialType) params.append('material_type', materialType);
    if (usageArea) params.append('usage_area', usageArea);

    const response = await fetch(`${API_BASE_URL}/insights/models/${carModelId}/materials/?${params}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    return await response.json();
  } catch (error) {
    console.error('Get design materials error:', error);
    throw error;
  }
};

// 공학적 스펙 관련 API
export const getEngineeringSpecs = async (carModelId) => {
  if (USE_MOCK_DATA) {
    const specs = mockEngineeringSpecs.filter(spec => spec.car_model_id === carModelId);
    const mockResponse = await createMockResponse({
      count: specs.length,
      results: specs
    });
    return await mockResponse.json();
  }

  try {
    const response = await fetch(`${API_BASE_URL}/insights/models/${carModelId}/specs/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    return await response.json();
  } catch (error) {
    console.error('Get engineering specs error:', error);
    throw error;
  }
};

// 판매 통계 관련 API
export const getSalesStats = async (carModelId, year = '', month = '', page = 1, pageSize = 12) => {
  if (USE_MOCK_DATA) {
    let filteredSales = mockSalesStats.filter(sale => sale.car_model_id === carModelId);
    
    if (year) {
      filteredSales = filteredSales.filter(sale => sale.year === parseInt(year));
    }
    if (month) {
      filteredSales = filteredSales.filter(sale => sale.month === parseInt(month));
    }
    
    const mockResponse = await createMockResponse({
      count: filteredSales.length,
      results: filteredSales
    });
    return await mockResponse.json();
  }

  try {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString()
    });
    if (year) params.append('year', year);
    if (month) params.append('month', month);

    const response = await fetch(`${API_BASE_URL}/insights/models/${carModelId}/sales/?${params}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    return await response.json();
  } catch (error) {
    console.error('Get sales stats error:', error);
    throw error;
  }
};

// 사용자 리뷰 관련 API
export const getUserReviews = async (carModelId, sentimentScoreMin = '', sentimentScoreMax = '', page = 1, pageSize = 10) => {
  if (USE_MOCK_DATA) {
    let filteredReviews = mockUserReviews.filter(review => review.car_model_id === carModelId);
    
    if (sentimentScoreMin) {
      filteredReviews = filteredReviews.filter(review => review.sentiment_score >= parseFloat(sentimentScoreMin));
    }
    if (sentimentScoreMax) {
      filteredReviews = filteredReviews.filter(review => review.sentiment_score <= parseFloat(sentimentScoreMax));
    }
    
    const mockResponse = await createMockResponse({
      count: filteredReviews.length,
      results: filteredReviews
    });
    return await mockResponse.json();
  }

  try {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString()
    });
    if (sentimentScoreMin) params.append('sentiment_score_min', sentimentScoreMin);
    if (sentimentScoreMax) params.append('sentiment_score_max', sentimentScoreMax);

    const response = await fetch(`${API_BASE_URL}/insights/models/${carModelId}/reviews/?${params}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
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
