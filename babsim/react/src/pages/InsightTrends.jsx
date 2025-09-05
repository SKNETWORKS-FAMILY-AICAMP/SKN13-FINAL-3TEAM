import React, { useState, useEffect } from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import ThreeDViewer from '../components/ThreeDViewer';
import backgroundImage from '../assets/PrototypeLab_background.png';
import { getCarModels, getCarModelDetail } from '../services/insightService';

// 사용자가 제공한 원래의 카테고리 구조를 그대로 복원
const hardcodedCategories = [
    {
      name: '수소 / 전기차',
      subItems: [
        '더 뉴 아이오닉 6',
        '디 올 뉴 넥쏘',
        '아이오닉 5',
        '코나 Electric',
        '아이오닉 9',
        'ST1',
        '포터 II Electric',
        '포터 II Electric 특장차',
        '2026 캐스퍼 일렉트릭'
      ]
    },
    {
      name: 'N',
      subItems: [
        '아반떼 N',
        '아이오닉 5 N'
      ]
    },
    {
      name: '승용',
      subItems: [
        '그랜저',
        '그랜저 Hybrid',
        '아반떼',
        '아반떼 Hybrid',
        '쏘나타 디 엣지',
        '쏘나타 디 엣지 Hybrid'
      ]
    },
    {
      name: 'SUV',
      subItems: [
        '싼타페',
        '싼타페 Hybrid',
        '투싼',
        '투싼 Hybrid',
        '코나',
        '코나 Hybrid',
        '베뉴',
        '디 올 뉴 팰리세이드',
        '디 올 뉴 팰리세이드 Hybrid',
        '2026 캐스퍼'
      ]
    },
    {
      name: 'MPV',
      subItems: [
        '스타리아 라운지',
        '스타리아 라운지 Hybrid',
        '스타리아',
        '스타리아 Hybrid',
        '스타리아 킨더',
        '스타리아 라운지 캠퍼',
        '스타리아 라운지 캠퍼 Hybrid',
        '스타리아 라운지 리무진',
        '스타리아 라운지 리무진 Hybrid'
      ]
    },
    {
      name: '소형트럭&택시',
      subItems: [
        '그랜저 택시',
        '쏘나타 택시',
        '스타리아 라운지 모빌리티',
        '스타리아 라운지 모빌리티 Hybrid',
        '포터 II',
        '포터 II 특장차'
      ]
    },
    {
      name: '트럭',
      subItems: [
        '더 뉴 마이티',
        '더 뉴 파비스',
        '뉴파워트럭',
        '더 뉴 엑시언트',
        '엑시언트 수소전기트럭'
      ]
    },
    {
      name: '버스',
      subItems: [
        '쏠라티',
        '카운티',
        '카운티 일렉트릭',
        '일렉시티 타운',
        '뉴 슈퍼에어로시티',
        '일렉시티',
        '일렉시티 수소전기버스',
        '일렉시티 이층버스',
        '유니버스',
        '유니버스 수소전기버스',
        '유니버스 모바일 오피스'
      ]
    },
    {
      name: 'GENESIS',
      subItems: []
    },
    {
      name: 'CASPER',
      subItems: []
    }
  ];

const InsightTrends = () => {
  const [selectedCar, setSelectedCar] = useState(null); // 전체 차량 객체 저장
  const [carMap, setCarMap] = useState(new Map()); // 차량 이름을 key로 전체 객체를 저장하는 Map
  const [carSpecs, setCarSpecs] = useState(null);
  const [reviewAnalysis, setReviewAnalysis] = useState({
    recentReviews: [],
    reviewCategories: { design: { phrase: 'No Data', percentage: 0 }, performance: { phrase: 'No Data', percentage: 0 }, comfort: { phrase: 'No Data', percentage: 0 }, space: { phrase: 'No Data', percentage: 0 } },
    overallRating: { score: 0, level: '', stars: 0 }
  });
  const [carHistory, setCarHistory] = useState([]);
  const [scrollY, setScrollY] = useState(0);
  const [expandedArticles, setExpandedArticles] = useState({});
  const [expandedReviews, setExpandedReviews] = useState({});

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // 1. 페이지 로드 시 모든 차량 데이터를 가져와 Map으로 만듦
  useEffect(() => {
    const fetchAndMapCars = async () => {
      try {
        const models = await getCarModels(); // 페이지네이션 없이 모든 차량을 가져옴
        const newCarMap = new Map(models.map(car => [car.car_name, car]));
        setCarMap(newCarMap);

        // 기본 선택 차량 설정 (카테고리 목록의 첫번째 차량)
        const firstCarName = hardcodedCategories[0]?.subItems[0];
        if (firstCarName && newCarMap.has(firstCarName)) {
          setSelectedCar(newCarMap.get(firstCarName));
        }
      } catch (error) {
        console.error("Failed to fetch car list:", error);
      }
    };
    fetchAndMapCars();
  }, []);

  // 2. selectedCar가 변경되면 (객체가 통째로) 상세 정보를 가져옴
  useEffect(() => {
    if (selectedCar && selectedCar.car_model_id) {
      const fetchCarDetails = async () => {
        try {
          const details = await getCarModelDetail(selectedCar.car_model_id);
          const specObj = Array.isArray(details.engineering_specs) ? (details.engineering_specs[0] || null) : (details.engineering_specs || null);
          setCarSpecs(specObj);
          analyzeReviews(details.user_reviews || []);
          setCarHistory(details.recent_articles || []);
          setExpandedArticles({});
        } catch (error) {
          console.error("Failed to fetch car details:", error);
          setCarSpecs(null);
          setCarHistory([]);
        }
      };
      fetchCarDetails();
    }
  }, [selectedCar]);

  // 3. 카테고리에서 차량 이름(string)을 클릭했을 때 처리
  const handleCarSelect = (carName) => {
    if (carMap.has(carName)) {
      setSelectedCar(carMap.get(carName)); // Map에서 전체 차량 객체를 찾아 상태 업데이트
    }
  };

  const analyzeReviews = (carReviews) => {
    try {
      if (!carReviews || carReviews.length === 0) {
        setReviewAnalysis({ recentReviews: [], reviewCategories: { design: { phrase: 'No Data', percentage: 0 }, performance: { phrase: 'No Data', percentage: 0 }, comfort: { phrase: 'No Data', percentage: 0 }, space: { phrase: 'No Data', percentage: 0 } }, overallRating: { score: 0, level: 'No Data', stars: 0 } });
        return;
      }
      const randomReviews = getRandomReviews(carReviews, 2);
      const categoryAnalysis = analyzeReviewCategories(carReviews);
      const randomRating = generateRandomRating();
      setReviewAnalysis({ recentReviews: randomReviews, reviewCategories: categoryAnalysis, overallRating: randomRating });
    } catch (error) {
      console.error('Error analyzing reviews:', error);
    }
  };

  const getRandomReviews = (reviews, count) => {
    const shuffled = [...reviews].sort(() => 0.5 - Math.random());
    return shuffled.slice(0, count).map(review => ({
      id: review.review_id,
      review: review.review,
      rating: review.rating || Math.floor(Math.random() * 2) + 4
    }));
  };

  const analyzeReviewCategories = (reviews) => {
    const categories = { design: {}, performance: {}, comfort: {}, space: {} };
    reviews.forEach(review => {
      if (review.tags && typeof review.tags === 'object') {
        Object.entries(review.tags).forEach(([key, value]) => {
          if (categories[key]) {
            categories[key][value] = (categories[key][value] || 0) + 1;
          }
        });
      }
    });
    const result = {};
    Object.keys(categories).forEach(category => {
      const phrases = categories[category];
      if (Object.keys(phrases).length > 0) {
        const totalInCategory = Object.values(phrases).reduce((sum, count) => sum + count, 0);
        const maxPhrase = Object.keys(phrases).reduce((a, b) => phrases[a] > phrases[b] ? a : b);
        const percentage = Math.round((phrases[maxPhrase] / totalInCategory) * 100);
        result[category] = { phrase: maxPhrase, percentage: percentage };
      } else {
        result[category] = { phrase: 'No Data', percentage: 0 };
      }
    });
    return result;
  };

  const generateRandomRating = () => {
    const score = Math.random() * 2 + 3;
    const roundedScore = Math.round(score * 10) / 10;
    let level = '';
    if (roundedScore >= 4.5) level = 'Excellent';
    else if (roundedScore >= 4.0) level = 'Very Good';
    else if (roundedScore >= 3.5) level = 'Good';
    else if (roundedScore >= 3.0) level = 'Fair';
    else level = 'Poor';
    return { score: roundedScore, level: level, stars: Math.round(roundedScore) };
  };

  const toggleArticleExpansion = (index) => {
    setExpandedArticles(prev => ({ ...prev, [index]: !prev[index] }));
  };

  const toggleReviewExpansion = (index) => {
    setExpandedReviews(prev => ({ ...prev, [index]: !prev[index] }));
  };

  return (
    <div className="min-h-screen bg-gray-900">
      <Header />
      
      <section className="relative py-24 lg:py-32" style={{ backgroundImage: `url(${backgroundImage})`, backgroundSize: 'cover', backgroundPosition: 'center', backgroundRepeat: 'no-repeat', minHeight: '60vh' }}>
        <div className="absolute inset-0 bg-black/50"></div>
        <div className="w-full px-6 lg:px-8 text-center relative z-10">
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-96 h-96 rounded-full" style={{ background: 'radial-gradient(circle, rgba(139, 92, 246, 0.4) 0%, rgba(16, 185, 129, 0.2) 50%, transparent 100%)', filter: 'blur(60px)' }}></div>
          </div>
          <div className="relative z-20">
            <h1 className="text-5xl lg:text-6xl font-bold text-white mb-6">Insight & Trends</h1>
            <p className="text-gray-300 text-xl mb-8">Design with data, not just intuition.</p>
            <div className="text-gray-400 space-y-2">
              <p>시장과 사용자의 데이터를 분석해 인사이트를 도출합니다.</p>
              <p>차종별 리뷰, 트렌드 키워드, 감성 분석 데이터를 시각화하여 현재 소비자가 원하는 디자인 방향을 제시합니다.</p>
            </div>
          </div>
        </div>
      </section>

      <div className="fixed left-2 z-50 w-60 max-h-[80vh]" style={{ top: `${Math.max(24, window.innerHeight / 2 - 350 - Math.min(scrollY * 0.4, 80) + Math.min(scrollY * 0.4, 80))}px`, transform: 'none', transition: 'top 0.1s ease-out' }}>
        <div className="bg-gray-900/90 backdrop-blur-md rounded-2xl border border-gray-700 shadow-2xl">
          <div className="p-6 border-b border-gray-700">
            <h3 className="text-xl font-bold text-white text-center">차량 카테고리</h3>
          </div>
          <div className="p-6 max-h-[calc(80vh-80px)] overflow-y-auto">
            <div className="space-y-4">
              {hardcodedCategories.map((category, index) => (
                <div key={index} className="border-b border-gray-700 pb-3 last:border-b-0">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-lg font-semibold text-blue-400 cursor-pointer hover:text-blue-300 transition-colors">{category.name}</h4>
                    {category.subItems.length > 0 && <span className="text-xs text-gray-400 bg-gray-800 px-2 py-1 rounded-full">{category.subItems.length}</span>}
                  </div>
                  {category.subItems.length > 0 && (
                    <div className="ml-4 space-y-1">
                      {category.subItems.map((item, itemIndex) => (
                        <div key={itemIndex} className="text-sm text-gray-300 hover:text-white cursor-pointer transition-colors py-1 px-2 rounded hover:bg-gray-800/50" onClick={() => handleCarSelect(item)}>
                          {item}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <section className="py-8 px-6 lg:px-8">
        <div className="w-full max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-12" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
            <div className="bg-gray-900/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700 shadow-xl">
              <h3 className="text-xl font-bold text-white mb-4">Recent Reviews</h3>
              {reviewAnalysis?.recentReviews && reviewAnalysis.recentReviews.length > 0 ? (
                <div className="space-y-4">
                  {reviewAnalysis.recentReviews.map((review, index) => (
                    <div key={review.id || index} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                      <div className="flex items-center mb-2">
                        <div className="flex text-yellow-400">
                          {[...Array(5)].map((_, i) => <span key={i} className={i < review.rating ? 'text-yellow-400' : 'text-gray-600'}>★</span>)}
                        </div>
                        <span className="ml-2 text-sm text-gray-400">{review.rating}/5</span>
                      </div>
                      <p className="text-gray-300 text-sm leading-relaxed">
                        {expandedReviews[index] ? review.review : review.review && review.review.length > 150 ? review.review.substring(0, 150) + '...' : review.review}
                      </p>
                      {review.review && review.review.length > 150 && (
                        <button onClick={() => toggleReviewExpansion(index)} className="mt-2 text-blue-400 hover:text-blue-300 text-sm font-medium transition-colors">
                          {expandedReviews[index] ? '접기' : '더보기'}
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8"><p className="text-gray-400">No reviews found for this vehicle</p></div>
              )}
            </div>

            <div className="bg-gray-900/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700 shadow-xl">
              <h3 className="text-xl font-bold text-white mb-4">Review Categories</h3>
              <div className="space-y-3">
                <div className="bg-gray-800/50 rounded-lg p-3">
                  <div className="flex justify-between items-center mb-1"><span className="text-gray-300">Design</span><span className="text-green-400 font-semibold">{reviewAnalysis?.reviewCategories?.design?.percentage || 0}%</span></div>
                  <p className="text-xs text-gray-400">{reviewAnalysis?.reviewCategories?.design?.phrase || 'No Data'}</p>
                </div>
                <div className="bg-gray-800/50 rounded-lg p-3">
                  <div className="flex justify-between items-center mb-1"><span className="text-gray-300">Performance</span><span className="text-blue-400 font-semibold">{reviewAnalysis?.reviewCategories?.performance?.percentage || 0}%</span></div>
                  <p className="text-xs text-gray-400">{reviewAnalysis?.reviewCategories?.performance?.phrase || 'No Data'}</p>
                </div>
                <div className="bg-gray-800/50 rounded-lg p-3">
                  <div className="flex justify-between items-center mb-1"><span className="text-gray-300">Comfort</span><span className="text-purple-400 font-semibold">{reviewAnalysis?.reviewCategories?.comfort?.percentage || 0}%</span></div>
                  <p className="text-xs text-gray-400">{reviewAnalysis?.reviewCategories?.comfort?.phrase || 'No Data'}</p>
                </div>
                <div className="bg-gray-800/50 rounded-lg p-3">
                  <div className="flex justify-between items-center mb-1"><span className="text-gray-300">Space</span><span className="text-yellow-400 font-semibold">{reviewAnalysis?.reviewCategories?.space?.percentage || 0}%</span></div>
                  <p className="text-xs text-gray-400">{reviewAnalysis?.reviewCategories?.space?.phrase || 'No Data'}</p>
                </div>
              </div>
            </div>

            <div className="bg-gray-900/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700 shadow-xl">
              <h3 className="text-xl font-bold text-white mb-4">Overall Rating</h3>
              <div className="text-center">
                <div className="text-4xl font-bold text-yellow-400 mb-2">{reviewAnalysis?.overallRating?.score || 0}</div>
                <div className="text-gray-400 text-sm">{reviewAnalysis?.overallRating?.level || 'No Data'}</div>
                <div className="flex justify-center mt-2">
                  {[...Array(5)].map((_, i) => <svg key={i} className={`w-5 h-5 ${i < (reviewAnalysis?.overallRating?.stars || 0) ? 'text-yellow-400' : 'text-gray-600'}`} fill="currentColor" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" /></svg>)}
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-5 gap-6" style={{display: 'grid', gridTemplateColumns: '1fr', gap: '24px'}}>
            <div className="xl:col-span-3" style={{gridColumn: 'span 3'}}>
              <div className="text-white text-lg font-medium mb-2 text-left ml-8">3D Viewer</div>
              <div className="flex gap-6">
                <div className="flex-1 ml-8">
                  <div className="bg-gray-700 rounded-lg h-96 overflow-hidden"><ThreeDViewer carName={selectedCar?.car_name} /></div>
                </div>
                <div className="w-80">
                  <div className="bg-gray-800/90 backdrop-blur-md rounded-xl border border-gray-700 shadow-xl p-6">
                    <h3 className="text-xl font-bold text-white mb-4">Specifications</h3>
                    <div className="space-y-3">
                      {carSpecs ? (
                        (() => {
                          const spec = Array.isArray(carSpecs) ? (carSpecs[0] || null) : carSpecs;
                          if (!spec) return (
                            <div className="text-center py-8"><p className="text-gray-400">Specifications not available for {selectedCar?.car_name}</p></div>
                          );

                          const numberFormatter = new Intl.NumberFormat('en-US');
                          const withUnit = (field, raw) => {
                            if (raw === null || raw === undefined || raw === '') return 'N/A';
                            const asString = String(raw).trim();
                            const onlyDigits = asString.replace(/\D/g, '');
                            const formatted = onlyDigits ? numberFormatter.format(Number(onlyDigits)) : asString;
                            if (field === 'seating_capacity') return `${formatted} 명`;
                            if (['length','width','height','wheelbase'].includes(field)) return `${formatted} mm`;
                            if (field === 'weight') return `${formatted} kg`;
                            return formatted;
                          };

                          const targetSpecs = [
                            { label: '전장', field: 'length' },
                            { label: '전폭', field: 'width' },
                            { label: '전고', field: 'height' },
                            { label: '축거', field: 'wheelbase' },
                            { label: '승차정원', field: 'seating_capacity' },
                            { label: '공차중량', field: 'weight' },
                          ];
                          return targetSpecs.map(({ label, field }) => (
                            <div key={field} className="flex justify-between items-center py-2 border-b border-gray-700/50 last:border-b-0">
                              <span className="text-gray-300 text-sm font-medium">{label}</span>
                              <span className="text-white text-sm font-semibold">{withUnit(field, spec?.[field])}</span>
                            </div>
                          ));
                        })()
                      ) : (
                        <div className="text-center py-8"><p className="text-gray-400">Specifications not available for {selectedCar?.car_name}</p></div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="xl:col-span-2">
              <div className="bg-gray-900/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700 shadow-xl">
                <h3 className="text-2xl font-bold text-white mb-6">Recent Articles</h3>
                {carHistory && carHistory.length > 0 ? (
                  <div className="space-y-4">
                    {carHistory.map((history, index) => (
                      <div key={history.article_id || index} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                        <h4 className="text-lg font-semibold text-blue-400 mb-2">{history.title || history.car_name || 'Article'}</h4>
                        <p className="text-sm text-gray-400 mb-3">{(() => {
                          const dateStr = history.published_date || (history.year ? `${history.year}-01-01` : null);
                          try { return dateStr ? new Date(dateStr).toLocaleDateString() : ''; } catch { return ''; }
                        })()}</p>
                        {(history.content || history.explain) && (
                          <>
                            <p className="text-gray-300 text-sm leading-relaxed">
                              {(() => {
                                const body = history.content || history.explain || '';
                                if (expandedArticles[index]) return body;
                                return body.length > 200 ? body.substring(0, 200) + '...' : body;
                              })()}
                            </p>
                            {(() => { const body = history.content || history.explain || ''; return body.length > 200; })() && (
                              <button onClick={() => toggleArticleExpansion(index)} className="mt-2 text-blue-400 hover:text-blue-300 text-sm font-medium transition-colors">
                                {expandedArticles[index] ? '접기' : '더보기'}
                              </button>
                            )}
                          </>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8"><p className="text-gray-400">No history found for this vehicle</p></div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>
      
      <Footer />
    </div>
  );
};

export default InsightTrends;
