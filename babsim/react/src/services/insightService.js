import { createMockResponse } from './mockData';
import { apiRequest } from './authService';

const API_BASE_URL = '/api';
const USE_MOCK_DATA = false;

// 기본 차량 모델 정보는 loadCarSpecs()에서 동적으로 생성

// HTTP 요청 시뮬레이션 함수
const simulateHttpRequest = async (url, options, mockData) => {
  console.log('🌐 HTTP 요청 시뮬레이션:', {
    url,
    method: options.method,
    headers: options.headers,
    body: options.body
  });

  // 목업 모드에서는 실제 HTTP 요청을 보내지 않음
  if (USE_MOCK_DATA) {
    console.log('🔄 목업 모드: 실제 HTTP 요청 건너뛰기');
    const mockResponse = await createMockResponse(mockData);
    console.log('✅ 목업 응답 반환:', mockData);
    return mockResponse;
  }

  // 실제 fetch 요청을 보내지만 목업 응답을 반환 (USE_MOCK_DATA가 false일 때만)
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

// CSV 파일을 파싱하는 유틸리티 함수
const parseCSV = (csvText) => {
  const lines = csvText.split('\n');
  if (lines.length < 2) return null;
  
  const headers = lines[0].split(',').map(h => h.trim());
  const data = [];
  
  for (let i = 1; i < lines.length; i++) {
    if (lines[i].trim()) {
      const values = lines[i].split(',').map(v => v.trim().replace(/"/g, ''));
      const row = {};
      headers.forEach((header, index) => {
        row[header] = values[index] || '';
      });
      data.push(row);
    }
  }
  
  return { headers, data };
};

// 3D 모델 경로를 반환하는 함수
const get3DModelPath = (carName) => {
  const modelMapping = {
    '2026 캐스퍼 일렉트릭': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/2026%20%EC%BA%90%EC%8A%A4%ED%8D%BC%20%EC%9D%BC%EB%A0%89%ED%8A%B8%EB%A6%AD.glb',
    '2026 캐스퍼': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/2026%20%EC%BA%90%EC%8A%A4%ED%8D%BC.glb',
    '그랜저 택시': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EA%B7%B8%EB%9E%9C%EC%A0%80%20%ED%83%9D%EC%8B%9C.glb',
    '그랜저 Hybrid': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EA%B7%B8%EB%9E%9C%EC%A0%80%20Hybrid.glb',
    '그랜저': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EA%B7%B8%EB%9E%9C%EC%A0%80.glb',
    '뉴 슈퍼에어로시티': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EB%89%B4%20%EC%8A%88%ED%8D%BC%EC%97%90%EC%96%B4%EB%A1%9C%EC%8B%9C%ED%8B%B0.glb',
    '뉴파워트럭': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EB%89%B4%ED%8C%8C%EB%B2%84%ED%8A%B8%EB%9F%AD.glb',
    '더 뉴 마이티': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EB%8D%94%20%EB%89%B4%20%EB%A7%88%EC%9D%B4%ED%8B%B0.glb',
    '더 뉴 아이오닉 6': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EB%8D%94%20%EB%89%B4%20%EC%95%84%EC%9D%B4%EC%98%A4%EB%8B%89%206.glb',
    '더 뉴 엑시언트': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EB%8D%94%20%EB%89%B4%20%EC%97%91%EC%8B%9C%EC%97%B8%ED%8A%B8.glb',
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
    '싼타페 Hybrid': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%8B%B8%EB%83%88%ED%8C%A8%20Hybrid.glb',
    '싼타페': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%8B%B8%EB%83%88%ED%8C%A8.glb',
    '쏘나타 디 엣지 Hybrid': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%8F%98%EB%82%98%ED%83%80%20%EB%94%94%20%EC%97%A3%EC%A7%80%20Hybrid.glb',
    '쏘나타 디 엣지': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%8F%98%EB%82%98%ED%83%80%20%EB%94%94%20%EC%97%A3%EC%A7%80.glb',
    '쏘나타 택시': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%8F%98%EB%82%98%ED%83%80%20%ED%83%9D%EC%8B%9C.glb',
    '쏠라티': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%8F%98%EB%9D%BC%ED%8B%B0.glb',
    '아반떼 Hybrid': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%95%84%EB%B0%98%EB%96%BC%20Hybrid.glb',
    '아반떼 N': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%95%84%EB%B0%98%EB%96%BC%20N.glb',
    '아반떼': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%95%84%EB%B0%98%EB%96%BC.glb',
    '아이오닉 5 N': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%95%84%EC%9D%B4%EC%98%A4%EB%8B%89%205%20N.glb',
    '아이오닉 5': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%95%84%EC%9D%B4%EC%98%A4%EB%8B%89%205.glb',
    '아이오닉 9': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%95%84%EC%9D%B4%EC%98%A4%EB%8B%89%209.glb',
    '엑시언트 수소전기트럭': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%EC%97%91%EC%8B%9C%EC%97%B8%ED%8A%B8%20%EC%88%98%EC%86%8C%EC%A0%84%EA%B8%B0%ED%8A%B8%EB%9F%AD.glb',
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
    '투싼 Hybrid': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%ED%88%AC%EC%8B%B8%ED%8C%AC%20Hybrid.glb',
    '투싼': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%ED%88%AC%EC%8B%B8%ED%8C%AC.glb',
    '포터 II 특장차': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%ED%8F%AC%ED%84%B0%20II%20%ED%8A%B9%EC%9E%A5%EC%B0%A8.glb',
    '포터 II Electric 특장차': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%ED%8F%AC%ED%84%B0%20II%20Electric%20%ED%8A%B9%EC%9E%A5%EC%B0%A8.glb',
    '포터 II Electric': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%ED%8F%AC%ED%84%B0%20II%20Electric.glb',
    '포터 II': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/%ED%8F%AC%ED%84%B0%20II.glb',
    'ST1': 'https://babsim-media.s3.ap-southeast-2.amazonaws.com/models/ST1.glb',
  };
  
  return modelMapping[carName] || null;
};

// Insight & Trends 서비스
import carSpecsData from '../assets/insight_trends/car_specs';
import carReviewsData from '../assets/insight_trends/hyundai_car_reviews.json';

// 차량 스펙 데이터 로드
export const loadCarSpecs = async () => {
  try {
    // CSV 파일들을 동적으로 import하여 데이터 로드
    const specs = [];
    
    // 차량 스펙 데이터 처리
    for (const [carName, specData] of Object.entries(carSpecsData)) {
      if (specData && typeof specData === 'object') {
        specs.push({
          car_name: carName,
          ...specData
        });
      }
    }
    
    return specs;
  } catch (error) {
    console.error('차량 스펙 로드 실패:', error);
    return [];
  }
};

// 차량 리뷰 데이터 로드
export const loadCarReviews = async () => {
  try {
    return carReviewsData || [];
  } catch (error) {
    console.error('차량 리뷰 로드 실패:', error);
    return [];
  }
};

// 차량 통계 생성
export const generateCarStats = (carSpecs, carReviews) => {
  try {
    // 인기도 통계 (차량별 언급 횟수)
    const popularityStats = [];
    const carMentions = {};
    
    carReviews.forEach(review => {
      const carName = review.car_name;
      if (carName) {
        carMentions[carName] = (carMentions[carName] || 0) + 1;
      }
    });
    
    Object.entries(carMentions)
      .sort(([,a], [,b]) => b - a)
      .forEach(([carName, count]) => {
        popularityStats.push([carName, count]);
      });

    // 카테고리별 통계
    const categoryStats = {};
    carSpecs.forEach(spec => {
      if (spec.category) {
        categoryStats[spec.category] = (categoryStats[spec.category] || 0) + 1;
      }
    });

    // 태그별 통계
    const tagStats = {};
    carReviews.forEach(review => {
      if (review.tags) {
        Object.entries(review.tags).forEach(([category, value]) => {
          if (!tagStats[category]) tagStats[category] = {};
          if (!tagStats[category][value]) tagStats[category][value] = 0;
          tagStats[category][value]++;
        });
      }
    });

    return {
      popularityStats,
      categoryStats,
      tagStats,
      totalCars: carSpecs.length,
      totalReviews: carReviews.length
    };
  } catch (error) {
    console.error('통계 생성 실패:', error);
    return {
      popularityStats: [],
      categoryStats: {},
      tagStats: {},
      totalCars: 0,
      totalReviews: 0
    };
  }
};

// 차량별 상세 통계
export const getCarDetailStats = (carName, carSpecs, carReviews) => {
  try {
    const carSpec = carSpecs.find(spec => 
      spec.car_name.includes(carName) || carName.includes(spec.car_name.split(' ')[0])
    );
    
    const carReviews = carReviews.filter(review => 
      review.car_name.includes(carName) || carName.includes(review.car_name.split(' ')[0])
    );

    return {
      spec: carSpec,
      reviews: carReviews,
      reviewCount: carReviews.length,
      averageRating: carReviews.length > 0 
        ? carReviews.reduce((sum, review) => sum + (review.rating || 0), 0) / carReviews.length 
        : 0
    };
  } catch (error) {
    console.error('차량 상세 통계 생성 실패:', error);
    return null;
  }
};

// 트렌드 키워드 분석
export const analyzeTrends = (carReviews) => {
  try {
    const keywordCounts = {};
    const sentimentTrends = {};
    
    carReviews.forEach(review => {
      // 키워드 카운트
      if (review.tags) {
        Object.entries(review.tags).forEach(([category, value]) => {
          const key = `${category}:${value}`;
          keywordCounts[key] = (keywordCounts[key] || 0) + 1;
        });
      }
      
      // 감성 트렌드
      if (review.rating) {
        const year = new Date().getFullYear(); // 임시로 현재 연도 사용
        if (!sentimentTrends[year]) sentimentTrends[year] = [];
        sentimentTrends[year].push(review.rating);
      }
    });

    // 상위 키워드 정렬
    const topKeywords = Object.entries(keywordCounts)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 10)
      .map(([key, count]) => {
        const [category, value] = key.split(':');
        return { category, value, count };
      });

    // 연도별 평균 평점
    const yearlySentiment = Object.entries(sentimentTrends).map(([year, ratings]) => ({
      year: parseInt(year),
      averageRating: ratings.reduce((sum, rating) => sum + rating, 0) / ratings.length
    }));

    return {
      topKeywords,
      yearlySentiment,
      totalKeywords: Object.keys(keywordCounts).length
    };
  } catch (error) {
    console.error('트렌드 분석 실패:', error);
    return {
      topKeywords: [],
      yearlySentiment: [],
      totalKeywords: 0
    };
  }
};

// 디자인 인사이트 생성
export const generateDesignInsights = (carSpecs, carReviews) => {
  try {
    const insights = {
      popularFeatures: [],
      designTrends: [],
      materialPreferences: [],
      colorTrends: []
    };

    // 인기 기능 분석
    const featureCounts = {};
    carReviews.forEach(review => {
      if (review.tags && review.tags.features) {
        const features = Array.isArray(review.tags.features) 
          ? review.tags.features 
          : [review.tags.features];
        
        features.forEach(feature => {
          featureCounts[feature] = (featureCounts[feature] || 0) + 1;
        });
      }
    });

    insights.popularFeatures = Object.entries(featureCounts)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 5)
      .map(([feature, count]) => ({ feature, count }));

    // 디자인 트렌드 분석
    const designCounts = {};
    carReviews.forEach(review => {
      if (review.tags && review.tags.design) {
        designCounts[review.tags.design] = (designCounts[review.tags.design] || 0) + 1;
      }
    });

    insights.designTrends = Object.entries(designCounts)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 3)
      .map(([design, count]) => ({ design, count }));

    return insights;
  } catch (error) {
    console.error('디자인 인사이트 생성 실패:', error);
    return {
      popularFeatures: [],
      designTrends: [],
      materialPreferences: [],
      colorTrends: []
    };
  }
};

// 차량 검색 기능
export const searchCars = (carSpecs, searchTerm, category) => {
  if (!searchTerm && category === 'all') return carSpecs;
  
  return carSpecs.filter(car => {
    const matchesSearch = !searchTerm || 
      car.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      car.category.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesCategory = category === 'all' || car.category === category;
    
    return matchesSearch && matchesCategory;
  });
};

// 리뷰 검색 기능
export const searchReviews = (carReviews, searchTerm, carName) => {
  if (!searchTerm && !carName) return carReviews;
  
  return carReviews.filter(review => {
    const matchesSearch = !searchTerm || 
      review.review.toLowerCase().includes(searchTerm.toLowerCase()) ||
      review.car_name.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesCar = !carName || 
      review.car_name.toLowerCase().includes(carName.toLowerCase());
    
    return matchesSearch && matchesCar;
  });
};

// 차량 모델 관련 API
export const getCarModels = async (type = '', releaseYear = '', page = 1, pageSize = 10) => {
  // 실제 assets 데이터에서 차량 정보 로드
  const carSpecs = await loadCarSpecs();
  
  // carSpecs 데이터를 기반으로 차량 모델 정보 생성
  let filteredModels = carSpecs.map((spec, index) => ({
    car_model_id: `car-${index + 1}`,
    car_name: spec.car_name,
    type: spec.category || 'SUV', // car_specs의 category 필드 사용
    release_year: spec.year || 2024 // car_specs의 year 필드 사용
  }));
  
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
  // 실제 assets 데이터에서 차량 정보 로드
  const carSpecs = await loadCarSpecs();
  const carReviews = await loadCarReviews();
  
  // carSpecs에서 해당 차량 찾기
  const carSpec = carSpecs[parseInt(carModelId.split('-')[1]) - 1];
  if (!carSpec) {
    throw new Error('차량 모델을 찾을 수 없습니다.');
  }
  
  // 차량 모델 정보 생성
  const carModel = {
    car_model_id: carModelId,
    car_name: carSpec.car_name,
    type: carSpec.category || 'SUV',
    release_year: carSpec.year || 2024
  };
  
  // 차량별 리뷰 정보 (hyundai_car_reviews.json에서)
  const reviews = carReviews.filter(review => review.car_name === carSpec.car_name);
  
  // 차량별 역사 정보 (hyundai_car_history.json에서)
  const articles = carReviews.filter(review => review.car_name === carSpec.car_name);

  // 3D 모델 경로 설정
  const model3dPath = get3DModelPath(carSpec.car_name);

  const mockData = {
    ...carModel,
    engineering_specs: carSpec || {},
    user_reviews: reviews,
    recent_articles: articles,
    model_3d_path: model3dPath
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

// 공학적 스펙 관련 API
export const getEngineeringSpecs = async (carModelId) => {
  // 실제 assets 데이터에서 차량 스펙 정보 로드
  const carSpecs = await loadCarSpecs();
  
  // carSpecs에서 해당 차량 찾기
  const carSpec = carSpecs[parseInt(carModelId.split('-')[1]) - 1];
  if (!carSpec) {
    throw new Error('차량 모델을 찾을 수 없습니다.');
  }
  
  const mockData = {
    count: carSpec ? Object.keys(carSpec).length : 0,
    results: carSpec || {}
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

// 사용자 리뷰 관련 API
export const getUserReviews = async (carModelId, page = 1, pageSize = 10) => {
  // 실제 assets 데이터에서 차량 정보와 리뷰 정보 로드
  const carSpecs = await loadCarSpecs();
  const carReviews = await loadCarReviews();
  
  // carSpecs에서 해당 차량 찾기
  const carSpec = carSpecs[parseInt(carModelId.split('-')[1]) - 1];
  if (!carSpec) {
    throw new Error('차량 모델을 찾을 수 없습니다.');
  }
  
  // 해당 차량의 리뷰 정보 필터링
  const reviews = carReviews.filter(review => review.car_name === carSpec.car_name);
  
  const mockData = {
    count: reviews.length,
    results: reviews
  };

  if (USE_MOCK_DATA) {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString()
    });

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
  getEngineeringSpecs,
  getUserReviews
};
