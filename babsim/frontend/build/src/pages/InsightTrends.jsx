import React, { useState, useEffect } from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';
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
    } finally {
      setIsLoading(false);
    }
  };

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
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-700 text-white hover:bg-gray-600'
                        }`}
                      >
                        <h4 className="font-semibold">{model.car_name}</h4>
                        <p className="text-sm opacity-70">{model.type} • {model.release_year}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

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
                              </div>
                            ))}
                          </div>
                        </div>
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
                  </div>
                </div>
              ) : (
                <div className="bg-gray-800 rounded-lg p-8 border border-gray-700 text-center">
                  <p className="text-gray-400">차량 모델을 선택해주세요.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>
      
      <Footer />
    </div>
  );
}

export default InsightTrends; 