import React, { useState, useEffect } from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';
<<<<<<< HEAD
import ThreeDViewer from '../components/ThreeDViewer';
import { 
  loadCarSpecs, 
  loadCarReviews, 
  generateCarStats,
  getCarDetailStats
} from '../services/insightService';

function InsightTrends() {
  const [carSpecs, setCarSpecs] = useState([]);
  const [carReviews, setCarReviews] = useState([]);
  const [carStats, setCarStats] = useState({});
  const [selectedCar, setSelectedCar] = useState(null);
  const [activeTab, setActiveTab] = useState('3D view');
  const [isLoading, setIsLoading] = useState(true);

  // hyundai_car_3D에 있는 차량들 (3D 모델이 있는 차량들)
  const available3DCars = [
    '포터2',
    '쏘나타 디 엣지', 
    '산타페',
    '코나',
    '아이오닉 5'
  ];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [specs, reviews] = await Promise.all([
        loadCarSpecs(),
        loadCarReviews()
      ]);
      
      setCarSpecs(specs);
      setCarReviews(reviews);
      setCarStats(generateCarStats(specs, reviews));
      
      // 기본 선택 차량 설정 (3D 모델이 있는 차량 중 첫 번째)
      const first3DCar = specs.find(spec => available3DCars.includes(spec.car_name));
      if (first3DCar) {
        setSelectedCar(first3DCar);
      }
    } catch (error) {
      console.error('데이터 로드 실패:', error);
=======
import { 
  getCarModels, 
  getCarModelDetail, 
  getDesignMaterials, 
  getEngineeringSpecs, 
  getSalesStats, 
  getUserReviews 
} from '../services/insightService';

function InsightTrends() {
  const [carModels, setCarModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [modelDetail, setModelDetail] = useState(null);
  const [filterType, setFilterType] = useState('');
  const [filterYear, setFilterYear] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadCarModels();
  }, [currentPage, filterType, filterYear]);

  useEffect(() => {
    if (selectedModel) {
      loadModelDetail(selectedModel.car_model_id);
    }
  }, [selectedModel]);

  const loadCarModels = async () => {
    setIsLoading(true);
    try {
      const response = await getCarModels(filterType, filterYear, currentPage, 10);
      setCarModels(response.results || []);
    } catch (error) {
      console.error('차량 모델 로드 실패:', error);
>>>>>>> beb203adba0342a9db39c2d614aaa6f4b671d6fe
    } finally {
      setIsLoading(false);
    }
  };

<<<<<<< HEAD
  // 차량별 리뷰 통계 계산
  const getCarReviewStats = (carName) => {
    const reviews = carReviews.filter(review => 
      review.car_name.includes(carName) || carName.includes(review.car_name.split(' ')[0])
    );
    
    if (reviews.length === 0) return null;

    const tagCounts = {};
    reviews.forEach(review => {
      Object.entries(review.tags).forEach(([category, value]) => {
        if (!tagCounts[category]) tagCounts[category] = {};
        if (!tagCounts[category][value]) tagCounts[category][value] = 0;
        tagCounts[category][value]++;
      });
    });

    return {
      totalReviews: reviews.length,
      tagCounts,
      averageSentiment: 4.2 // 임시 값
    };
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
=======
  const loadModelDetail = async (modelId) => {
    try {
      const response = await getCarModelDetail(modelId);
      setModelDetail(response);
    } catch (error) {
      console.error('모델 상세 정보 로드 실패:', error);
    }
  };

  const handleModelSelect = (model) => {
    setSelectedModel(model);
    setActiveTab('overview');
  };

  const handleFilterChange = () => {
    setCurrentPage(1);
    loadCarModels();
  };

  return (
    <div className="min-h-screen" style={{backgroundColor: '#353745'}}>
>>>>>>> beb203adba0342a9db39c2d614aaa6f4b671d6fe
      <Header />
      
      {/* Hero Section */}
      <section className="relative py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          {/* Background Glow Effect */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-96 h-96 rounded-full" style={{
              background: 'radial-gradient(circle, rgba(139, 92, 246, 0.4) 0%, rgba(16, 185, 129, 0.2) 50%, transparent 100%)',
              filter: 'blur(60px)'
            }}></div>
          </div>
          
          {/* Content */}
          <div className="relative z-10">
            <h1 className="text-6xl font-bold text-white mb-6">Insight & Trends</h1>
            <p className="text-gray-300 text-xl mb-8">
              Design with data, not just intuition.
            </p>
            <div className="text-gray-400 space-y-2">
              <p>시장과 사용자의 데이터를 분석해 인사이트를 도출합니다.</p>
              <p>차종별 리뷰, 트렌드 키워드, 감성 분석 데이터를 시각화하여 현재 소비자가 원하는 디자인 방향을 제시합니다.</p>
            </div>
          </div>
        </div>
      </section>

<<<<<<< HEAD
      {/* Car Selection & Analysis Section */}
      <section className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            {/* Left Sidebar - Car Selection */}
            <div className="lg:col-span-1">
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <h3 className="text-white text-xl font-semibold mb-4">차량 선택</h3>
                <p className="text-gray-400 text-sm mb-4">3D 모델이 있는 차량만 표시됩니다</p>
                
                <div className="space-y-2">
                  {carSpecs
                    .filter(spec => available3DCars.includes(spec.car_name))
                    .map((car) => (
                      <div
                        key={car.car_name}
                        onClick={() => setSelectedCar(car)}
                        className={`p-3 rounded-lg cursor-pointer transition-colors ${
                          selectedCar?.car_name === car.car_name
=======
      {/* Main Content */}
      <section className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
            
            {/* Left Sidebar - Car Models */}
            <div className="lg:col-span-1">
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <h3 className="text-white text-xl font-semibold mb-4">차량 모델</h3>
                
                {/* Filters */}
                <div className="space-y-4 mb-6">
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">차종</label>
                    <select
                      value={filterType}
                      onChange={(e) => {
                        setFilterType(e.target.value);
                        handleFilterChange();
                      }}
                      className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                    >
                      <option value="">전체</option>
                      <option value="SUV">SUV</option>
                      <option value="세단">세단</option>
                      <option value="해치백">해치백</option>
                      <option value="왜건">왜건</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">출시 연도</label>
                    <select
                      value={filterYear}
                      onChange={(e) => {
                        setFilterYear(e.target.value);
                        handleFilterChange();
                      }}
                      className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                    >
                      <option value="">전체</option>
                      <option value="2024">2024</option>
                      <option value="2023">2023</option>
                      <option value="2022">2022</option>
                      <option value="2021">2021</option>
                    </select>
                  </div>
                </div>

                {/* Car Models List */}
                <div className="space-y-2">
                  {isLoading ? (
                    <div className="text-center text-gray-400">로딩 중...</div>
                  ) : carModels.length === 0 ? (
                    <div className="text-center text-gray-400">차량 모델이 없습니다.</div>
                  ) : (
                    carModels.map((model) => (
                      <div
                        key={model.car_model_id}
                        onClick={() => handleModelSelect(model)}
                        className={`p-3 rounded-lg cursor-pointer transition-colors ${
                          selectedModel?.car_model_id === model.car_model_id
>>>>>>> beb203adba0342a9db39c2d614aaa6f4b671d6fe
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-700 text-white hover:bg-gray-600'
                        }`}
                      >
<<<<<<< HEAD
                        <h4 className="font-semibold">{car.car_name}</h4>
                        <p className="text-sm opacity-70">{car.category} • {car.release_year}</p>
                        {available3DCars.includes(car.car_name) && (
                          <span className="inline-block bg-green-500 text-white text-xs px-2 py-1 rounded mt-1">
                            3D 모델 있음
                          </span>
                        )}
                      </div>
                    ))}
=======
                        <h4 className="font-semibold">{model.car_name}</h4>
                        <p className="text-sm opacity-70">{model.type} • {model.release_year}</p>
                      </div>
                    ))
                  )}
>>>>>>> beb203adba0342a9db39c2d614aaa6f4b671d6fe
                </div>
              </div>
            </div>

<<<<<<< HEAD
            {/* Right Content - Car Analysis */}
            <div className="lg:col-span-2">
              {selectedCar ? (
                <div className="space-y-6">
                  {/* Car Header */}
                  <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                    <div className="flex items-center space-x-4 mb-4">
                      <div className="w-20 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                        <span className="text-white font-bold text-lg">3D</span>
                      </div>
                      <div>
                        <h2 className="text-white text-2xl font-semibold">{selectedCar.car_name}</h2>
                        <p className="text-gray-400">{selectedCar.category} • {selectedCar.release_year} 출시</p>
                        {available3DCars.includes(selectedCar.car_name) && (
                          <span className="inline-block bg-green-500 text-white text-xs px-2 py-1 rounded mt-1">
                            3D 모델 사용 가능
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Tabs */}
                  <div className="bg-gray-800 rounded-lg border border-gray-700">
                    <div className="flex border-b border-gray-700">
                      {[
                        { id: '3D view', label: '3D View' },
                        { id: 'specs', label: '제원 정보' },
                        { id: 'reviews', label: '리뷰 분석' },
                        { id: 'trends', label: '트렌드' }
                      ].map((tab) => (
                        <button
                          key={tab.id}
                          onClick={() => setActiveTab(tab.id)}
                          className={`px-6 py-3 text-sm font-medium transition-colors ${
                            activeTab === tab.id
                              ? 'text-blue-400 border-b-2 border-blue-400'
                              : 'text-gray-400 hover:text-white'
                          }`}
                        >
                          {tab.label}
                        </button>
                      ))}
                    </div>

                    {/* Tab Content */}
                    <div className="p-6">
                      {activeTab === '3D view' && selectedCar && (
                        <div className="space-y-6">
                          {/* 3D Model Viewer */}
                          <div className="bg-gray-700 rounded-lg h-96">
                            <ThreeDViewer 
                              carName={selectedCar.car_name} 
                              className="w-full h-full"
                            />
                          </div>
                          
                          {/* Rotation Control Info */}
                          <div className="text-center">
                            <p className="text-gray-400 text-sm mb-2">
                              마우스로 드래그하여 차량을 회전시킬 수 있습니다
                            </p>
                            <p className="text-gray-500 text-xs">
                              휠로 확대/축소, 우클릭으로 이동
                            </p>
                          </div>
                        </div>
                      )}

                      {activeTab === '3D view' && !selectedCar && (
                        <div className="text-center text-gray-400 py-8">
                          차량을 선택해주세요.
                        </div>
                      )}

                      {activeTab === 'specs' && (
                        <div className="space-y-6">
                          <h3 className="text-white text-lg font-semibold">차량 제원</h3>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {Object.entries(selectedCar.specs || {}).map(([key, value]) => (
                              <div key={key} className="bg-gray-700 rounded-lg p-4">
                                <div className="text-center">
                                  <div className="text-2xl font-bold text-white mb-1">{value}</div>
                                  <div className="text-gray-400 text-sm">{key}</div>
                                </div>
=======
            {/* Right Content - Model Details */}
            <div className="lg:col-span-3">
              {selectedModel ? (
                <div className="bg-gray-800 rounded-lg border border-gray-700">
                  {/* Model Header */}
                  <div className="p-6 border-b border-gray-700">
                    <h2 className="text-white text-2xl font-semibold">{selectedModel.car_name}</h2>
                    <p className="text-gray-400">{selectedModel.type} • {selectedModel.release_year} 출시</p>
                  </div>

                  {/* Tabs */}
                  <div className="flex border-b border-gray-700">
                    {[
                      { id: 'overview', label: '개요' },
                      { id: 'materials', label: '디자인 재질' },
                      { id: 'specs', label: '공학적 스펙' },
                      { id: 'sales', label: '판매 통계' },
                      { id: 'reviews', label: '사용자 리뷰' }
                    ].map((tab) => (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`px-6 py-3 text-sm font-medium transition-colors ${
                          activeTab === tab.id
                            ? 'text-blue-400 border-b-2 border-blue-400'
                            : 'text-gray-400 hover:text-white'
                        }`}
                      >
                        {tab.label}
                      </button>
                    ))}
                  </div>

                  {/* Tab Content */}
                  <div className="p-6">
                    {activeTab === 'overview' && modelDetail && (
                      <div className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <div className="bg-gray-700 rounded-lg p-4">
                            <h4 className="text-white font-semibold mb-3">디자인 재질</h4>
                            <div className="space-y-2">
                              {modelDetail.design_materials?.slice(0, 3).map((material) => (
                                <div key={material.material_id} className="flex justify-between">
                                  <span className="text-gray-300">{material.material_type}</span>
                                  <span className="text-gray-400">{material.usage_area}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                          
                          <div className="bg-gray-700 rounded-lg p-4">
                            <h4 className="text-white font-semibold mb-3">공학적 스펙</h4>
                            {modelDetail.engineering_specs?.[0] && (
                              <div className="space-y-2">
                                <div className="flex justify-between">
                                  <span className="text-gray-300">CD 값</span>
                                  <span className="text-gray-400">{modelDetail.engineering_specs[0].cd_value}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-300">중량</span>
                                  <span className="text-gray-400">{modelDetail.engineering_specs[0].weight}kg</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-300">알루미늄 비율</span>
                                  <span className="text-gray-400">{modelDetail.engineering_specs[0].material_al_ratio * 100}%</span>
                                </div>
                              </div>
                            )}
                          </div>
                        </div>

                        <div className="bg-gray-700 rounded-lg p-4">
                          <h4 className="text-white font-semibold mb-3">사용자 리뷰 요약</h4>
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            {modelDetail.user_reviews?.slice(0, 3).map((review) => (
                              <div key={review.review_id} className="text-center">
                                <div className="text-2xl font-bold text-white">{review.sentiment_score}</div>
                                <div className="text-gray-400 text-sm">평점</div>
                                <div className="text-gray-300 text-xs mt-1">{review.mentioned_features}</div>
>>>>>>> beb203adba0342a9db39c2d614aaa6f4b671d6fe
                              </div>
                            ))}
                          </div>
                        </div>
<<<<<<< HEAD
                      )}

                      {activeTab === 'reviews' && (
                        <div className="space-y-6">
                          <h3 className="text-white text-lg font-semibold">리뷰 분석</h3>
                          {(() => {
                            const reviewStats = getCarReviewStats(selectedCar.car_name);
                            if (!reviewStats) {
                              return (
                                <div className="text-center text-gray-400 py-8">
                                  이 차량에 대한 리뷰가 없습니다.
                                </div>
                              );
                            }
                            return (
                              <div className="space-y-4">
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                  <div className="bg-gray-700 rounded-lg p-4 text-center">
                                    <div className="text-2xl font-bold text-white">{reviewStats.totalReviews}</div>
                                    <div className="text-gray-400 text-sm">총 리뷰 수</div>
                                  </div>
                                  <div className="bg-gray-700 rounded-lg p-4 text-center">
                                    <div className="text-2xl font-bold text-white">{reviewStats.averageSentiment}</div>
                                    <div className="text-gray-400 text-sm">평균 평점</div>
                                  </div>
                                  <div className="bg-gray-700 rounded-lg p-4 text-center">
                                    <div className="text-2xl font-bold text-white">{Object.keys(reviewStats.tagCounts).length}</div>
                                    <div className="text-gray-400 text-sm">분석 카테고리</div>
                                  </div>
                                </div>
                                
                                <div className="bg-gray-700 rounded-lg p-4">
                                  <h4 className="text-white font-medium mb-3">태그별 분포</h4>
                                  <div className="space-y-2">
                                    {Object.entries(reviewStats.tagCounts).map(([category, values]) => (
                                      <div key={category} className="mb-3">
                                        <div className="text-gray-300 text-sm mb-1">{category}</div>
                                        <div className="space-y-1">
                                          {Object.entries(values).slice(0, 3).map(([value, count]) => (
                                            <div key={value} className="flex justify-between items-center">
                                              <span className="text-gray-400 text-sm">{value}</span>
                                              <span className="text-white text-sm">{count}</span>
                                            </div>
                                          ))}
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              </div>
                            );
                          })()}
                        </div>
                      )}

                      {activeTab === 'trends' && (
                        <div className="space-y-6">
                          <h3 className="text-white text-lg font-semibold">트렌드 분석</h3>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="bg-gray-700 rounded-lg p-4">
                              <h4 className="text-white font-medium mb-3">시장 인기도</h4>
                              <div className="space-y-3">
                                {carStats.popularityStats?.slice(0, 5).map(([carName, count], index) => (
                                  <div key={index} className="flex items-center justify-between">
                                    <span className="text-gray-300 text-sm">{carName}</span>
                                    <div className="flex items-center space-x-2">
                                      <div className="w-20 bg-gray-600 rounded-full h-2">
                                        <div 
                                          className="bg-blue-500 h-2 rounded-full" 
                                          style={{width: `${(count / Math.max(...carStats.popularityStats.map(([,c]) => c))) * 100}%`}}
                                        ></div>
                                      </div>
                                      <span className="text-white text-sm w-8 text-right">{count}</span>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                            
                            <div className="bg-gray-700 rounded-lg p-4">
                              <h4 className="text-white font-medium mb-3">차종별 분포</h4>
                              <div className="space-y-3">
                                {Object.entries(carStats.categoryStats || {}).map(([category, count]) => (
                                  <div key={category} className="flex items-center justify-between">
                                    <span className="text-gray-300 text-sm">{category}</span>
                                    <div className="flex items-center space-x-2">
                                      <div className="w-20 bg-gray-600 rounded-full h-2">
                                        <div 
                                          className="bg-green-500 h-2 rounded-full" 
                                          style={{width: `${(count / Math.max(...Object.values(carStats.categoryStats || {}))) * 100}%`}}
                                        ></div>
                                      </div>
                                      <span className="text-white text-sm w-8 text-right">{count}</span>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
=======
                      </div>
                    )}

                    {activeTab === 'materials' && (
                      <div className="space-y-4">
                        <h3 className="text-white text-lg font-semibold">디자인 재질 정보</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {modelDetail?.design_materials?.map((material) => (
                            <div key={material.material_id} className="bg-gray-700 rounded-lg p-4">
                              <div className="flex justify-between items-center mb-2">
                                <span className="text-white font-medium">{material.material_type}</span>
                                <span className="text-blue-400 text-sm">{material.usage_area}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {activeTab === 'specs' && (
                      <div className="space-y-4">
                        <h3 className="text-white text-lg font-semibold">공학적 스펙</h3>
                        {modelDetail?.engineering_specs?.[0] && (
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="bg-gray-700 rounded-lg p-4">
                              <div className="text-center">
                                <div className="text-2xl font-bold text-white">{modelDetail.engineering_specs[0].cd_value}</div>
                                <div className="text-gray-400">CD 값</div>
                              </div>
                            </div>
                            <div className="bg-gray-700 rounded-lg p-4">
                              <div className="text-center">
                                <div className="text-2xl font-bold text-white">{modelDetail.engineering_specs[0].weight}kg</div>
                                <div className="text-gray-400">중량</div>
                              </div>
                            </div>
                            <div className="bg-gray-700 rounded-lg p-4">
                              <div className="text-center">
                                <div className="text-2xl font-bold text-white">{modelDetail.engineering_specs[0].material_al_ratio * 100}%</div>
                                <div className="text-gray-400">알루미늄 비율</div>
                              </div>
                            </div>
                            <div className="bg-gray-700 rounded-lg p-4">
                              <div className="text-center">
                                <div className="text-2xl font-bold text-white">{modelDetail.engineering_specs[0].pedestrian_safety_score}</div>
                                <div className="text-gray-400">보행자 안전 점수</div>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {activeTab === 'sales' && (
                      <div className="space-y-4">
                        <h3 className="text-white text-lg font-semibold">판매 통계</h3>
                        <div className="bg-gray-700 rounded-lg p-4">
                          <div className="flex items-end justify-between h-32">
                            {modelDetail?.sales_stats?.map((sale) => (
                              <div key={`${sale.year}-${sale.month}`} className="flex flex-col items-center">
                                <div 
                                  className="w-8 bg-blue-500 rounded-t" 
                                  style={{height: `${(sale.units_sold / 2000) * 100}px`}}
                                ></div>
                                <div className="text-gray-400 text-xs mt-1">{sale.month}월</div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}

                    {activeTab === 'reviews' && (
                      <div className="space-y-4">
                        <h3 className="text-white text-lg font-semibold">사용자 리뷰</h3>
                        <div className="space-y-3">
                          {modelDetail?.user_reviews?.map((review) => (
                            <div key={review.review_id} className="bg-gray-700 rounded-lg p-4">
                              <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center space-x-2">
                                  <div className="text-yellow-400">★</div>
                                  <span className="text-white font-medium">{review.sentiment_score}</span>
                                </div>
                              </div>
                              <p className="text-gray-300 text-sm">{review.mentioned_features}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
>>>>>>> beb203adba0342a9db39c2d614aaa6f4b671d6fe
                  </div>
                </div>
              ) : (
                <div className="bg-gray-800 rounded-lg p-8 border border-gray-700 text-center">
<<<<<<< HEAD
                  <p className="text-gray-400">왼쪽에서 차량을 선택해주세요.</p>
=======
                  <p className="text-gray-400">차량 모델을 선택해주세요.</p>
>>>>>>> beb203adba0342a9db39c2d614aaa6f4b671d6fe
                </div>
              )}
            </div>
          </div>
        </div>
      </section>
<<<<<<< HEAD

      {/* Dashboard Summary Widgets */}
      <section className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-white mb-8 text-center">전체 시장 현황</h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Total Cars Widget */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <div className="text-center">
                <div className="text-3xl font-bold text-white mb-2">{carStats.totalCars || 0}</div>
                <div className="text-gray-400">총 차량 모델</div>
                <div className="text-blue-400 text-sm mt-2">3D 모델: {available3DCars.length}개</div>
              </div>
            </div>

            {/* Total Reviews Widget */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <div className="text-center">
                <div className="text-3xl font-bold text-white mb-2">{carStats.totalReviews || 0}</div>
                <div className="text-gray-400">총 리뷰 수</div>
                <div className="text-green-400 text-sm mt-2">사용자 피드백</div>
              </div>
            </div>

            {/* Popular Category Widget */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <div className="text-center">
                <div className="text-3xl font-bold text-white mb-2">
                  {Object.entries(carStats.categoryStats || {}).sort(([,a], [,b]) => b - a)[0]?.[0] || 'N/A'}
                </div>
                <div className="text-gray-400">가장 인기 차종</div>
                <div className="text-purple-400 text-sm mt-2">시장 트렌드</div>
              </div>
            </div>
          </div>
        </div>
      </section>
=======
>>>>>>> beb203adba0342a9db39c2d614aaa6f4b671d6fe
      
      <Footer />
    </div>
  );
}

export default InsightTrends; 