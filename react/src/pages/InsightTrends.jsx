import React, { useState, useEffect } from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import ThreeDViewer from '../components/ThreeDViewer';
import backgroundImage from '../assets/Insight&Trends_background.png';
import carReviewsData from '../assets/insight_trends/hyundai_car_reviews.json';
import carHistoryData from '../assets/insight_trends/hyundai_car_history.json';
import carSpecsData from '../assets/insight_trends/car_specs/index.js';

const InsightTrends = () => {
  const [selectedCar, setSelectedCar] = useState({
    name: '쏘나타 디 엣지',
    display_name: '쏘나타 디 엣지',
    category: '승용',
    year: '2024'
  });

  const [reviewAnalysis, setReviewAnalysis] = useState({
    recentReviews: [],
    reviewCategories: {
      design: { phrase: 'No Data', percentage: 0 },
      performance: { phrase: 'No Data', percentage: 0 },
      comfort: { phrase: 'No Data', percentage: 0 },
      space: { phrase: 'No Data', percentage: 0 }
    },
    overallRating: {
      score: 0,
      level: '',
      stars: 0
    }
  });

  const [carHistory, setCarHistory] = useState([]); // Changed from null to empty array

  const [scrollY, setScrollY] = useState(0);

  // Add new state for expanded articles and reviews
  const [expandedArticles, setExpandedArticles] = useState({});
  const [expandedReviews, setExpandedReviews] = useState({});

  // 스크롤 이벤트 핸들러
  useEffect(() => {
    const handleScroll = () => {
      setScrollY(window.scrollY);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // CSV 파일들을 동적으로 import (Vite 호환 방식)
  const csvFiles = {
    "더 뉴 아이오닉 6": `항목,이-라이트 2WD (A/T),이-라이트 AWD (A/T),익스클루시브 2WD (A/T),익스클루시브 AWD (A/T),N라인 (익스클루시브) 2WD (A/T),N라인 (익스클루시브) AWD (A/T),프레스티지 2WD (A/T),프레스티지 AWD (A/T),N 라인 (프레스티지) 2WD (A/T),N 라인 (프레스티지) AWD (A/T)
전장,"4,925 mm","4,925 mm","4,925 mm","4,925 mm","4,935 mm","4,935 mm","4,925 mm","4,925 mm","4,935 mm","4,935 mm"
전폭,"1,880 mm","1,880 mm","1,880 mm","1,880 mm","1,880 mm","1,880 mm","1,880 mm","1,880 mm","1,880 mm","1,880 mm"
전고,"1,495 mm","1,495 mm","1,495 mm","1,495 mm","1,495 mm","1,495 mm","1,495 mm","1,495 mm","1,495 mm","1,495 mm"
축거,"2,950 mm","2,950 mm","2,950 mm","2,950 mm","2,950 mm","2,950 mm","2,950 mm","2,950 mm","2,950 mm","2,950 mm"
윤거 (전),"1,635 mm","1,635 mm","1,635 mm","1,635 mm","1,630 mm","1,630 mm","1,635 mm","1,635 mm","1,630 mm","1,630 mm"
윤거 (후),"1,644 mm","1,644 mm","1,644 mm","1,644 mm","1,639 mm","1,639 mm","1,644 mm","1,644 mm","1,639 mm","1,639 mm"
승차정원,5,5,5,5,5,5,5,5,5,5
공차중량,"1,925 kg","2,035 kg","1,925 kg","2,035 kg","1,970 kg","2,080 kg","1,925 kg","2,035 kg","1,970 kg","2,080 kg"`,
    
    "디 올 뉴 넥쏘": `항목,이-라이트 2WD (A/T),이-라이트 AWD (A/T),익스클루시브 2WD (A/T),익스클루시브 AWD (A/T),프레스티지 2WD (A/T),프레스티지 AWD (A/T)
전장,"4,630 mm","4,630 mm","4,630 mm","4,630 mm","4,630 mm","4,630 mm"
전폭,"1,865 mm","1,865 mm","1,865 mm","1,865 mm","1,865 mm","1,865 mm"
전고,"1,665 mm","1,665 mm","1,665 mm","1,665 mm","1,665 mm","1,665 mm"
축거,"2,755 mm","2,755 mm","2,755 mm","2,755 mm","2,755 mm","2,755 mm"
윤거 (전),"1,620 mm","1,620 mm","1,620 mm","1,620 mm","1,620 mm","1,620 mm"
윤거 (후),"1,627 mm","1,627 mm","1,627 mm","1,627 mm","1,627 mm","1,627 mm"
승차정원,5,5,5,5,5,5
공차중량,"1,625 kg","1,725 kg","1,625 kg","1,725 kg","1,625 kg","1,725 kg"`,
    
    "아이오닉 5": `항목,이-라이트 2WD (A/T),이-라이트 AWD (A/T),익스클루시브 2WD (A/T),익스클루시브 AWD (A/T),프레스티지 2WD (A/T),프레스티지 AWD (A/T)
전장,"4,635 mm","4,635 mm","4,635 mm","4,635 mm","4,635 mm","4,635 mm"
전폭,"1,890 mm","1,890 mm","1,890 mm","1,890 mm","1,890 mm","1,890 mm"
전고,"1,605 mm","1,605 mm","1,605 mm","1,605 mm","1,605 mm","1,605 mm"
축거,"3,000 mm","3,000 mm","3,000 mm","3,000 mm","3,000 mm","3,000 mm"
윤거 (전),"1,638 mm","1,638 mm","1,638 mm","1,638 mm","1,638 mm","1,638 mm"
윤거 (후),"1,647 mm","1,647 mm","1,647 mm","1,647 mm","1,647 mm","1,647 mm"
승차정원,5,5,5,5,5,5
공차중량,"2,015 kg","2,125 kg","2,015 kg","2,125 kg","2,015 kg","2,125 kg"`,
    
    "쏘나타 디 엣지": `항목,프리미엄 (A/T),익스클루시브 (A/T),인스퍼레이션 (A/T)
전장,"4,910 mm","4,910 mm","4,910 mm"
전폭,"1,860 mm","1,860 mm","1,860 mm"
전고,"1,445 mm","1,445 mm","1,445 mm"
축거,"2,840 mm","2,840 mm","2,840 mm"
윤거 (전),"1,633 mm","1,623 mm","1,618 mm"
윤거 (후),"1,640 mm","1,630 mm","1,625 mm"
승차정원,5,5,5
공차중량,"1,550 kg","1,570 kg","1,585 kg"
연료탱크,50 ℓ,50 ℓ,50 ℓ
트렁크 (후) 용량,480 ℓ,480 ℓ,480 ℓ`,
    
    "산타페": `항목,이-라이트 2WD (A/T),이-라이트 AWD (A/T),익스클루시브 2WD (A/T),익스클루시브 AWD (A/T),프레스티지 2WD (A/T),프레스티지 AWD (A/T)
전장,"4,930 mm","4,930 mm","4,930 mm","4,930 mm","4,930 mm","4,930 mm"
전폭,"1,915 mm","1,915 mm","1,915 mm","1,915 mm","1,915 mm","1,915 mm"
전고,"1,720 mm","1,720 mm","1,720 mm","1,720 mm","1,720 mm","1,720 mm"
축거,"2,900 mm","2,900 mm","2,900 mm","2,900 mm","2,900 mm","2,900 mm"
윤거 (전),"1,680 mm","1,680 mm","1,680 mm","1,680 mm","1,680 mm","1,680 mm"
윤거 (후),"1,680 mm","1,680 mm","1,680 mm","1,680 mm","1,680 mm","1,680 mm"
승차정원,7,7,7,7,7,7
공차중량,"2,050 kg","2,150 kg","2,050 kg","2,150 kg","2,050 kg","2,150 kg"`,
    
    "투싼": `항목,이-라이트 2WD (A/T),이-라이트 AWD (A/T),익스클루시브 2WD (A/T),익스클루시브 AWD (A/T),프레스티지 2WD (A/T),프레스티지 AWD (A/T)
전장,"4,640 mm","4,640 mm","4,640 mm","4,640 mm","4,640 mm","4,640 mm"
전폭,"1,865 mm","1,865 mm","1,865 mm","1,865 mm","1,865 mm","1,865 mm"
전고,"1,665 mm","1,665 mm","1,665 mm","1,665 mm","1,665 mm","1,665 mm"
축거,"2,755 mm","2,755 mm","2,755 mm","2,755 mm","2,755 mm","2,755 mm"
윤거 (전),"1,620 mm","1,620 mm","1,620 mm","1,620 mm","1,620 mm","1,620 mm"
윤거 (후),"1,627 mm","1,627 mm","1,627 mm","1,627 mm","1,627 mm","1,627 mm"
승차정원,5,5,5,5,5,5
공차중량,"1,625 kg","1,725 kg","1,625 kg","1,725 kg","1,625 kg","1,725 kg"`
  };

  // CSV 데이터를 파싱하는 함수
  const parseCSVData = (csvContent) => {
    try {
      const lines = csvContent.split('\n');
      const headers = lines[0].split(',');
      const specs = {};
      
      // 전장, 전폭, 전고, 축거, 승차정원, 공차중량만 추출
      const targetSpecs = ['전장', '전폭', '전고', '축거', '승차정원', '공차중량'];
      
      targetSpecs.forEach(specName => {
        const rowIndex = lines.findIndex(line => line.startsWith(specName));
        if (rowIndex !== -1) {
          const values = lines[rowIndex].split(',');
          // 첫 번째 값(항목명)을 제외하고 첫 번째 트림의 값을 사용
          if (values.length > 1) {
            specs[specName] = values[1].replace(/"/g, ''); // 따옴표 제거
          }
        }
      });
      
      return specs;
    } catch (error) {
      console.error('Error parsing CSV:', error);
      return {};
    }
  };

  // 차량 제원 데이터를 가져오는 함수
  const getCarSpecs = (carName) => {
    // 사용 가능한 차량 제원 데이터
    const availableCarSpecs = Object.keys(carSpecsData);
    
    // 1단계: 정확한 매칭
    if (carSpecsData[carName]) {
      return carSpecsData[carName];
    }
    
    // 2단계: 부분 매칭
    for (const availableName of availableCarSpecs) {
      if (carName.includes(availableName) || availableName.includes(carName)) {
        return carSpecsData[availableName];
      }
    }
    
    // 3단계: 단어 기반 매칭
    const carWords = carName.split(' ');
    for (const availableName of availableCarSpecs) {
      const availableWords = availableName.split(' ');
      const hasCommonWord = carWords.some(word => 
        availableWords.some(availableWord => 
          availableWord.includes(word) || word.includes(availableWord)
        )
      );
      if (hasCommonWord) {
        return carSpecsData[availableName];
      }
    }
    
    // 4단계: 특수 케이스 매칭
    const specialCases = {
      '더 뉴 아이오닉 6': '아이오닉 6',
      '디 올 뉴 넥쏘': '코나',
      '아이오닉 5 N': '아이오닉 5',
      '아이오닉 9': '아이오닉 6',
      '코나 일렉트릭': '코나',
      '캐스퍼 일렉트릭': '코나',
      '더 뉴 캐스퍼': '코나',
      '아반떼': '쏘나타 디 엣지',
      '아반떼 N': '쏘나타 디 엣지',
      '베뉴': '코나',
      '투싼': '산타페',
      '스타리아': '산타페',
      '디 올 뉴 팰리세이드': '산타페',
      '그랜저': '쏘나타 디 엣지',
      'G70': '쏘나타 디 엣지',
      'G80': '쏘나타 디 엣지',
      'G90': '쏘나타 디 엣지',
      'GV70': '산타페',
      'GV80': '산타페',
      'New GV60': '아이오닉 5',
      'ST1': '아이오닉 5',
      'Electrified G80': '쏘나타 디 엣지',
      'Electrified GV70': '산타페',
      '쏠라티': '산타페',
      '카운티': '포터2',
      '카운티 일렉트릭': '포터2',
      '마이티': '포터2',
      '파비스': '포터2'
    };
    
    if (specialCases[carName]) {
      const fallbackCar = specialCases[carName];
      return carSpecsData[fallbackCar];
    }
    
    return null;
  };

  // 리뷰 데이터 (Revenue/DailyExpenses/Summary 대체)
  const reviewStats = {
    "Revenue": {
      title: "Customer Satisfaction",
      dateRange: "Data from 1-12 Apr, 2024",
      data: {
        "Positive": 78,
        "Neutral": 18,
        "Negative": 4
      },
      colors: ["#10B981", "#6B7280"]
    },
    "DailyExpenses": {
      title: "Review Categories",
      dateRange: "Data from 1-12 Apr, 2024",
      data: {
        "Design": 32,
        "Performance": 28,
        "Space": 25,
        "Technology": 15
      },
      colors: ["#8B5CF6", "#9CA3AF"]
    },
    "Summary": {
      title: "Overall Rating",
      dateRange: "Data from 1-12 Apr, 2024",
      total: "4.7/5.0",
      change: "+0.3",
      percentage: "6.8%",
      breakdown: {
        "Design & Styling": 48,
        "Performance": 32,
        "Technology": 13,
        "Value": 7
      }
    }
  };

  // 카테고리 데이터
  const categories = [
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

  // 차량 히스토리 검색
  const searchCarHistory = (carName) => {
    try {
      const histories = carHistoryData.filter(item => {
        const itemCarName = item.car_name.toLowerCase();
        const searchCarName = carName.toLowerCase();
        
        // 정확한 매칭 또는 부분 매칭
        return itemCarName.includes(searchCarName) || 
               searchCarName.includes(itemCarName) ||
               itemCarName.includes(searchCarName.split(' ')[0]) ||
               itemCarName.includes(searchCarName.split(' ')[1]);
      });

      if (histories.length > 0) {
        // 최대 3개까지만 표시
        setCarHistory(histories.slice(0, 3));
        // Reset expanded state when car changes
        setExpandedArticles({});
      } else {
        setCarHistory([]);
        setExpandedArticles({});
      }
    } catch (error) {
      console.error('Error searching car history:', error);
      setCarHistory([]);
      setExpandedArticles({});
    }
  };

  // 리뷰 분석 파이프라인
  const analyzeReviews = (carName) => {
    try {
      // import된 JSON 데이터에서 해당 차량의 리뷰 검색
      const reviews = carReviewsData;
      
      // 선택된 차량의 리뷰 필터링 (더 정확한 매칭)
      const carReviews = reviews.filter(review => {
        const reviewCarName = review.car_name.toLowerCase();
        const selectedCarName = carName.toLowerCase();
        
        // 정확한 매칭 또는 부분 매칭
        return reviewCarName === selectedCarName || 
               reviewCarName.includes(selectedCarName) || 
               selectedCarName.includes(reviewCarName);
      });

      if (carReviews.length === 0) {
        // 기본값 설정
        setReviewAnalysis({
          recentReviews: [],
          reviewCategories: {
            design: { phrase: 'No Data', percentage: 0 },
            performance: { phrase: 'No Data', percentage: 0 },
            comfort: { phrase: 'No Data', percentage: 0 },
            space: { phrase: 'No Data', percentage: 0 }
          },
          overallRating: {
            score: 0,
            level: 'No Data',
            stars: 0
          }
        });
        return;
      }

      // 1. Recent Reviews - 랜덤으로 3개 선택
      const randomReviews = getRandomReviews(carReviews, 2);
      
      // 2. Review Categories - 태그별 문구 분석
      const categoryAnalysis = analyzeReviewCategories(carReviews);
      
      // 3. Overall Rating - 랜덤값
      const randomRating = generateRandomRating();

      setReviewAnalysis({
        recentReviews: randomReviews,
        reviewCategories: categoryAnalysis,
        overallRating: randomRating
      });

    } catch (error) {
      console.error('Error analyzing reviews:', error);
      // 에러 시 기본값 설정
      setReviewAnalysis({
        recentReviews: [],
        reviewCategories: {
          design: { phrase: 'Error', percentage: 0 },
          performance: { phrase: 'Error', percentage: 0 },
          comfort: { phrase: 'Error', percentage: 0 },
          space: { phrase: 'Error', percentage: 0 }
        },
        overallRating: {
          score: 0,
          level: 'Error',
          stars: 0
        }
      });
    }
  };

  // 랜덤 리뷰 선택
  const getRandomReviews = (reviews, count) => {
    const shuffled = [...reviews].sort(() => 0.5 - Math.random());
    return shuffled.slice(0, count).map(review => ({
      id: review.data_id,
      review: review.review, // Changed from text to review to match JSX
      rating: Math.floor(Math.random() * 2) + 4 // 4-5점 랜덤
    }));
  };

  // 리뷰 카테고리 분석 (태그별 문구 분석)
  const analyzeReviewCategories = (reviews) => {
    const categories = {
      design: {},
      performance: {},
      comfort: {},
      space: {}
    };

    reviews.forEach(review => {
      if (review.tags) {
        // 디자인 태그 분석
        if (review.tags['디자인']) {
          const phrase = review.tags['디자인'];
          categories.design[phrase] = (categories.design[phrase] || 0) + 1;
        }
        
        // 성능 태그 분석
        if (review.tags['성능']) {
          const phrase = review.tags['성능'];
          categories.performance[phrase] = (categories.performance[phrase] || 0) + 1;
        }
        
        // 승차감 태그 분석
        if (review.tags['승차감']) {
          const phrase = review.tags['승차감'];
          categories.comfort[phrase] = (categories.comfort[phrase] || 0) + 1;
        }
        
        // 공간 태그 분석
        if (review.tags['공간']) {
          const phrase = review.tags['공간'];
          categories.space[phrase] = (categories.space[phrase] || 0) + 1;
        }
      }
    });

    // 각 카테고리별로 가장 많이 나온 문구와 퍼센트 계산
    const result = {};
    Object.keys(categories).forEach(category => {
      const phrases = categories[category];
      if (Object.keys(phrases).length > 0) {
        const maxPhrase = Object.keys(phrases).reduce((a, b) => phrases[a] > phrases[b] ? a : b);
        const percentage = Math.round((phrases[maxPhrase] / reviews.length) * 100);
        result[category] = { phrase: maxPhrase, percentage: percentage };
      } else {
        result[category] = { phrase: 'No Data', percentage: 0 };
      }
    });

    return result;
  };

  // 랜덤 평점 생성
  const generateRandomRating = () => {
    const score = Math.random() * 2 + 3; // 3.0 - 5.0
    const roundedScore = Math.round(score * 10) / 10;
    
    let level = '';
    if (roundedScore >= 4.5) level = 'Excellent';
    else if (roundedScore >= 4.0) level = 'Very Good';
    else if (roundedScore >= 3.5) level = 'Good';
    else if (roundedScore >= 3.0) level = 'Fair';
    else level = 'Poor';

    return {
      score: roundedScore,
      level: level,
      stars: Math.round(roundedScore)
    };
  };

  // 차량 선택 시 리뷰 분석 실행
  useEffect(() => {
    if (selectedCar.name) {
      analyzeReviews(selectedCar.name);
      searchCarHistory(selectedCar.name);
    }
  }, [selectedCar.name]);

  // 차량 선택 핸들러
  const handleCarSelect = (carName) => {
    setSelectedCar({
      name: carName,
      display_name: carName,
      category: '승용', // 기본값, 나중에 카테고리별로 설정 가능
      year: '2024'
    });
  };

  // Add toggle functions for expand/collapse
  const toggleArticleExpansion = (index) => {
    setExpandedArticles(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const toggleReviewExpansion = (index) => {
    setExpandedReviews(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  return (
    <div className="min-h-screen bg-gray-900">
      <Header />
      
      {/* Hero Section */}
      <section className="relative py-24 lg:py-32" style={{
        backgroundImage: `url(${backgroundImage})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        minHeight: '60vh'
      }}>
        {/* Dark overlay for better text readability */}
        <div className="absolute inset-0 bg-black/50"></div>
        
        <div className="w-full px-6 lg:px-8 text-center relative z-10">
          {/* Background Glow Effect */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-96 h-96 rounded-full" style={{
              background: 'radial-gradient(circle, rgba(139, 92, 246, 0.4) 0%, rgba(16, 185, 129, 0.2) 50%, transparent 100%)',
              filter: 'blur(60px)'
            }}></div>
          </div>
          
          {/* Content */}
          <div className="relative z-20">
            <h1 className="text-5xl lg:text-6xl font-bold text-white mb-6">Insight & Trends</h1>
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

      {/* Floating Category Box */}
      <div 
        className="fixed left-2 z-50 w-60 max-h-[80vh]" 
        style={{
          top: `${Math.max(24, window.innerHeight / 2 - 350 - Math.min(scrollY * 0.4, 80) + Math.min(scrollY * 0.4, 80))}px`,
          transform: 'none',
          transition: 'top 0.1s ease-out'
        }}
      >
        <div className="bg-gray-900/90 backdrop-blur-md rounded-2xl border border-gray-700 shadow-2xl">
          {/* Fixed Header */}
          <div className="p-6 border-b border-gray-700">
            <h3 className="text-xl font-bold text-white text-center">차량 카테고리</h3>
          </div>
          
          {/* Scrollable Content */}
          <div className="p-6 max-h-[calc(80vh-80px)] overflow-y-auto">
            <div className="space-y-4">
              {categories.map((category, index) => (
                <div key={index} className="border-b border-gray-700 pb-3 last:border-b-0">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-lg font-semibold text-blue-400 cursor-pointer hover:text-blue-300 transition-colors">
                      {category.name}
                    </h4>
                    {category.subItems.length > 0 && (
                      <span className="text-xs text-gray-400 bg-gray-800 px-2 py-1 rounded-full">
                        {category.subItems.length}
                      </span>
                    )}
                  </div>
                  
                  {category.subItems.length > 0 && (
                    <div className="ml-4 space-y-1">
                      {category.subItems.map((item, itemIndex) => (
                        <div 
                          key={itemIndex} 
                          className="text-sm text-gray-300 hover:text-white cursor-pointer transition-colors py-1 px-2 rounded hover:bg-gray-800/50"
                          onClick={() => handleCarSelect(item)}
                        >
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

      {/* Main Content Area */}
      <section className="py-8 px-6 lg:px-8">
        <div className="w-full max-w-7xl mx-auto">
          {/* Data Dashboard Cards */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-12" style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '24px'
          }}>
            {/* Recent Reviews Card */}
            <div className="bg-gray-900/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700 shadow-xl">
              <h3 className="text-xl font-bold text-white mb-4">Recent Reviews</h3>
              {reviewAnalysis?.recentReviews && reviewAnalysis.recentReviews.length > 0 ? (
                <div className="space-y-4">
                  {reviewAnalysis.recentReviews.map((review, index) => (
                    <div key={index} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                      <div className="flex items-center mb-2">
                        <div className="flex text-yellow-400">
                          {[...Array(5)].map((_, i) => (
                            <span key={i} className={i < review.rating ? 'text-yellow-400' : 'text-gray-600'}>
                              ★
                            </span>
                          ))}
                        </div>
                        <span className="ml-2 text-sm text-gray-400">{review.rating}/5</span>
                      </div>
                      <p className="text-gray-300 text-sm leading-relaxed">
                        {expandedReviews[index] 
                          ? review.review 
                          : review.review && review.review.length > 150 
                            ? review.review.substring(0, 150) + '...' 
                            : review.review
                        }
                      </p>
                      {review.review && review.review.length > 150 && (
                        <button
                          onClick={() => toggleReviewExpansion(index)}
                          className="mt-2 text-blue-400 hover:text-blue-300 text-sm font-medium transition-colors"
                        >
                          {expandedReviews[index] ? '접기' : '더보기'}
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-400">No reviews found for this vehicle</p>
                </div>
              )}
            </div>

            {/* Review Categories Card */}
            <div className="bg-gray-900/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700 shadow-xl">
              <h3 className="text-xl font-bold text-white mb-4">Review Categories</h3>
              <div className="space-y-3">
                <div className="bg-gray-800/50 rounded-lg p-3">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-gray-300">Design</span>
                    <span className="text-green-400 font-semibold">{reviewAnalysis?.reviewCategories?.design?.percentage || 0}%</span>
                  </div>
                  <p className="text-xs text-gray-400">{reviewAnalysis?.reviewCategories?.design?.phrase || 'No Data'}</p>
                </div>
                
                <div className="bg-gray-800/50 rounded-lg p-3">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-gray-300">Performance</span>
                    <span className="text-blue-400 font-semibold">{reviewAnalysis?.reviewCategories?.performance?.percentage || 0}%</span>
                  </div>
                  <p className="text-xs text-gray-400">{reviewAnalysis?.reviewCategories?.performance?.phrase || 'No Data'}</p>
                </div>
                
                <div className="bg-gray-800/50 rounded-lg p-3">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-gray-300">Comfort</span>
                    <span className="text-purple-400 font-semibold">{reviewAnalysis?.reviewCategories?.comfort?.percentage || 0}%</span>
                  </div>
                  <p className="text-xs text-gray-400">{reviewAnalysis?.reviewCategories?.comfort?.phrase || 'No Data'}</p>
                </div>
                
                <div className="bg-gray-800/50 rounded-lg p-3">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-gray-300">Space</span>
                    <span className="text-yellow-400 font-semibold">{reviewAnalysis?.reviewCategories?.space?.percentage || 0}%</span>
                  </div>
                  <p className="text-xs text-gray-400">{reviewAnalysis?.reviewCategories?.space?.phrase || 'No Data'}</p>
                </div>
              </div>
            </div>

            {/* Overall Rating Card */}
            <div className="bg-gray-900/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700 shadow-xl">
              <h3 className="text-xl font-bold text-white mb-4">Overall Rating</h3>
              <div className="text-center">
                <div className="text-4xl font-bold text-yellow-400 mb-2">{reviewAnalysis?.overallRating?.score || 0}</div>
                <div className="text-gray-400 text-sm">{reviewAnalysis?.overallRating?.level || 'No Data'}</div>
                <div className="flex justify-center mt-2">
                  {[...Array(5)].map((_, i) => (
                    <svg key={i} className={`w-5 h-5 ${i < (reviewAnalysis?.overallRating?.stars || 0) ? 'text-yellow-400' : 'text-gray-600'}`} fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Row - Car Information Section */}
          <div className="grid grid-cols-1 xl:grid-cols-5 gap-6" style={{display: 'grid', gridTemplateColumns: '1fr', gap: '24px'}}>
            {/* Car 3D View */}
            <div className="xl:col-span-3" style={{gridColumn: 'span 3'}}>
              {/* 3D Viewer Label */}
              <div className="text-white text-lg font-medium mb-2 text-left ml-8">3D Viewer</div>
              
              {/* 3D Model and Specifications Layout */}
              <div className="flex gap-6">
                {/* 3D Viewer - Left Side */}
                <div className="flex-1 ml-8">
                  <div className="bg-gray-700 rounded-lg h-96 overflow-hidden">
                    <ThreeDViewer carName={selectedCar.name} />
                  </div>
                </div>
                
                {/* Specifications Box - Right Side */}
                <div className="w-80">
                  <div className="bg-gray-800/90 backdrop-blur-md rounded-xl border border-gray-700 shadow-xl p-6">
                    <h3 className="text-xl font-bold text-white mb-4">Specifications</h3>
                    <div className="space-y-3">
                      {(() => {
                        // CSV 파일에서 차량 제원 데이터 로드
                        const specs = getCarSpecs(selectedCar.name);
                        
                        if (!specs || !specs.specs) {
                          return (
                            <div className="text-center py-8">
                              <p className="text-gray-400">Specifications not available for {selectedCar.name}</p>
                              <p className="text-gray-500 text-xs mt-2">Available: {Object.keys(carSpecsData).join(', ')}</p>
                            </div>
                          );
                        }
                        
                        const displaySpecs = [
                          { key: "전장", value: specs.specs["전장"] },
                          { key: "전폭", value: specs.specs["전폭"] },
                          { key: "전고", value: specs.specs["전고"] },
                          { key: "축거", value: specs.specs["축거"] },
                          { key: "승차정원", value: specs.specs["승차정원"] },
                          { key: "공차중량", value: specs.specs["공차중량"] }
                        ];
                        
                        return displaySpecs.map(({ key, value }) => (
                          <div key={key} className="flex justify-between items-center py-2 border-b border-gray-700/50 last:border-b-0">
                            <span className="text-gray-300 text-sm font-medium">{key}</span>
                            <span className="text-white text-sm font-semibold">
                              {value || 'N/A'}
                            </span>
                          </div>
                        ));
                      })()}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Articles Card */}
            <div className="xl:col-span-2">
              <div className="bg-gray-900/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700 shadow-xl">
                <h3 className="text-2xl font-bold text-white mb-6">Recent Articles</h3>
                
                {carHistory && carHistory.length > 0 ? (
                  <div className="space-y-4">
                    {carHistory.map((history, index) => (
                      <div key={index} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                        <h4 className="text-lg font-semibold text-blue-400 mb-2">{history.car_name}</h4>
                        <p className="text-sm text-gray-400 mb-3">{history.year}</p>
                        {history.explain && (
                          <>
                            <p className="text-gray-300 text-sm leading-relaxed">
                              {expandedArticles[index] 
                                ? history.explain 
                                : history.explain.length > 200 
                                  ? history.explain.substring(0, 200) + '...' 
                                  : history.explain
                              }
                            </p>
                            {history.explain.length > 200 && (
                              <button
                                onClick={() => toggleArticleExpansion(index)}
                                className="mt-2 text-blue-400 hover:text-blue-300 text-sm font-medium transition-colors"
                              >
                                {expandedArticles[index] ? '접기' : '더보기'}
                              </button>
                            )}
                          </>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-gray-400">No history found for this vehicle</p>
                  </div>
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