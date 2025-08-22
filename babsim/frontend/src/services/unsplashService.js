// Unsplash API 서비스
const UNSPLASH_ACCESS_KEY = import.meta.env.VITE_UNSPLASH_ACCESS_KEY || 'YOUR_UNSPLASH_ACCESS_KEY';
const UNSPLASH_API_URL = 'https://api.unsplash.com';

// 개발용 목업 이미지 (실제 Unsplash API 키가 없을 때 사용)
const mockImages = {
  'automotive': 'https://images.unsplash.com/photo-1544636331-e26879cd4d9b?w=400&h=300&fit=crop',
  'design': 'https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=400&h=300&fit=crop',
  'car': 'https://images.unsplash.com/photo-1581833971358-2c8b550f87b3?w=400&h=300&fit=crop',
  'engineering': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop',
  'technology': 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=300&fit=crop',
  'research': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=300&fit=crop',
  'hyundai': 'https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=400&h=300&fit=crop',
  'motor': 'https://images.unsplash.com/photo-1544636331-e26879cd4d9b?w=400&h=300&fit=crop',
  'studio': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop',
  'electric': 'https://images.unsplash.com/photo-1593941707882-a5bac6861d1c?w=400&h=300&fit=crop',
  'suv': 'https://images.unsplash.com/photo-1552519507-da3b142c6e3d?w=400&h=300&fit=crop',
  'sedan': 'https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=400&h=300&fit=crop',
  'concept': 'https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=400&h=300&fit=crop',
  'interior': 'https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=400&h=300&fit=crop',
  'lighting': 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=300&fit=crop',
  'wheel': 'https://images.unsplash.com/photo-1544636331-e26879cd4d9b?w=400&h=300&fit=crop',
  'color': 'https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=400&h=300&fit=crop',
  'material': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop',
  'ux': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=300&fit=crop',
  'default': 'https://images.unsplash.com/photo-1581833971358-2c8b550f87b3?w=400&h=300&fit=crop'
};

// 키워드 매핑 (한국어 -> 영어)
const keywordMapping = {
  '자동차': 'automotive car vehicle',
  '디자인': 'design creative art',
  '개발': 'development engineering technology',
  '인간공학': 'ergonomics human engineering',
  '공기역학': 'aerodynamics automotive engineering',
  '차체': 'car body automotive design',
  '형태': 'form design shape',
  '성능': 'performance engineering technology',
  '현대': 'hyundai modern automotive',
  '모터스튜디오': 'motor studio automotive design',
  '철학': 'philosophy design thinking',
  '미의식': 'aesthetics design beauty',
  '신경학': 'neuroscience brain science',
  '전기차': 'electric car ev vehicle',
  'SUV': 'suv crossover vehicle',
  '세단': 'sedan car vehicle',
  '컨셉카': 'concept car automotive design',
  '브랜드': 'brand identity design',
  '아이덴티티': 'identity design brand',
  '인테리어': 'car interior automotive design',
  '조명': 'lighting design automotive',
  '휠': 'wheel rim automotive design',
  '색상': 'color design automotive',
  '재료': 'material engineering automotive',
  '사용자': 'user experience design',
  '경험': 'experience design ux'
};

// 문서 제목에서 키워드 추출 (한국어 -> 영어 매핑 + 제목 직접 사용)
const extractKeywords = (title) => {
  if (!title || typeof title !== 'string') return 'automotive design';
  
  const titleLower = title.toLowerCase();
  let keywords = '';
  
  // 한국어 키워드 매핑
  for (const [korean, english] of Object.entries(keywordMapping)) {
    if (titleLower.includes(korean.toLowerCase())) {
      keywords += english + ' ';
    }
  }
  
  // 영어 키워드가 있으면 그대로 사용
  if (titleLower.match(/[a-zA-Z]/)) {
    const englishWords = titleLower.match(/[a-zA-Z]+/g);
    if (englishWords) {
      keywords += englishWords.join(' ') + ' ';
    }
  }
  
  // 키워드가 없으면 제목을 직접 사용 (한국어 포함)
  if (!keywords.trim()) {
    // 제목에서 특수문자 제거하고 공백으로 연결
    keywords = title.replace(/[^\w\s가-힣]/g, ' ').trim();
    if (!keywords) {
      keywords = 'automotive design';
    }
  }
  
  return keywords.trim();
};

// Mock 이미지 선택 (실제 API 대신)
const getMockImageForKeywords = (keywords) => {
  const keywordLower = keywords.toLowerCase();
  
  // 키워드에 따른 이미지 선택
  if (keywordLower.includes('automotive') || keywordLower.includes('car')) {
    return mockImages.automotive;
  } else if (keywordLower.includes('design')) {
    return mockImages.design;
  } else if (keywordLower.includes('engineering')) {
    return mockImages.engineering;
  } else if (keywordLower.includes('technology')) {
    return mockImages.technology;
  } else if (keywordLower.includes('research')) {
    return mockImages.research;
  } else if (keywordLower.includes('hyundai')) {
    return mockImages.hyundai;
  } else if (keywordLower.includes('motor')) {
    return mockImages.motor;
  } else if (keywordLower.includes('studio')) {
    return mockImages.studio;
  } else if (keywordLower.includes('electric') || keywordLower.includes('ev')) {
    return mockImages.electric;
  } else if (keywordLower.includes('suv') || keywordLower.includes('crossover')) {
    return mockImages.suv;
  } else if (keywordLower.includes('sedan')) {
    return mockImages.sedan;
  } else if (keywordLower.includes('concept')) {
    return mockImages.concept;
  } else if (keywordLower.includes('interior')) {
    return mockImages.interior;
  } else if (keywordLower.includes('lighting')) {
    return mockImages.lighting;
  } else if (keywordLower.includes('wheel') || keywordLower.includes('rim')) {
    return mockImages.wheel;
  } else if (keywordLower.includes('color')) {
    return mockImages.color;
  } else if (keywordLower.includes('material')) {
    return mockImages.material;
  } else if (keywordLower.includes('ux') || keywordLower.includes('experience')) {
    return mockImages.ux;
  }
  
  return mockImages.default;
};

// Unsplash API로 이미지 검색 (실제 구현)
export const searchImageByTitle = async (title) => {
  try {
    const keywords = extractKeywords(title);
    console.log(`🔍 이미지 검색 키워드: "${keywords}" (원본: "${title}")`);
    
    // 실제 Unsplash API 키가 있는 경우
    if (UNSPLASH_ACCESS_KEY && UNSPLASH_ACCESS_KEY !== 'YOUR_UNSPLASH_ACCESS_KEY') {
      const response = await fetch(
        `${UNSPLASH_API_URL}/search/photos?query=${encodeURIComponent(keywords)}&per_page=1&orientation=landscape`,
        {
          headers: {
            'Authorization': `Client-ID ${UNSPLASH_ACCESS_KEY}`
          }
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        if (data.results && data.results.length > 0) {
          const imageUrl = `${data.results[0].urls.regular}?w=400&h=300&fit=crop`;
          console.log(`✅ Unsplash API에서 이미지 찾음: ${imageUrl}`);
          return imageUrl;
        }
      }
    }
    
    // API 키가 없거나 실패한 경우 목업 이미지 사용
    const mockImage = getMockImageForKeywords(keywords);
    console.log(`📸 목업 이미지 사용: ${mockImage}`);
    return mockImage;
    
  } catch (error) {
    console.error('이미지 검색 실패:', error);
    return mockImages.default;
  }
};

// 여러 키워드로 이미지 검색 (배치 처리)
export const searchMultipleImages = async (titles) => {
  const promises = titles.map(title => searchImageByTitle(title));
  return await Promise.all(promises);
};

// 제목과 컨텍스트(요약)를 사용한 고급 이미지 검색
export const searchImageWithContext = async (title, context = '') => {
  try {
    let keywords = extractKeywords(title);
    
    // 컨텍스트가 있으면 추가 키워드 추출
    if (context && context.trim()) {
      const contextKeywords = extractKeywords(context);
      keywords = `${keywords} ${contextKeywords}`;
    }
    
    console.log(`🔍 컨텍스트 기반 이미지 검색 키워드: "${keywords}" (제목: "${title}", 컨텍스트: "${context}")`);
    
    // 실제 Unsplash API 키가 있는 경우
    if (UNSPLASH_ACCESS_KEY && UNSPLASH_ACCESS_KEY !== 'YOUR_UNSPLASH_ACCESS_KEY') {
      const response = await fetch(
        `${UNSPLASH_API_URL}/search/photos?query=${encodeURIComponent(keywords)}&per_page=1&orientation=landscape`,
        {
          headers: {
            'Authorization': `Client-ID ${UNSPLASH_ACCESS_KEY}`
          }
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        if (data.results && data.results.length > 0) {
          const imageUrl = `${data.results[0].urls.regular}?w=400&h=300&fit=crop`;
          console.log(`✅ Unsplash API에서 컨텍스트 기반 이미지 찾음: ${imageUrl}`);
          return imageUrl;
        }
      }
    }
    
    // API 키가 없거나 실패한 경우 목업 이미지 사용
    const mockImage = getMockImageForKeywords(keywords);
    console.log(`📸 목업 이미지 사용 (컨텍스트 기반): ${mockImage}`);
    return mockImage;
    
  } catch (error) {
    console.error('컨텍스트 기반 이미지 검색 실패:', error);
    return mockImages.default;
  }
};

export default {
  searchImageByTitle,
  searchImageWithContext,
  searchMultipleImages
};
