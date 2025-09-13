import React, { useState, useEffect } from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { getAssets, uploadAsset, getComments, createComment, toggleAssetLike, toggleCommentLike } from '../services/libraryService';

// Import images
import designBook1 from '../assets/design_book1.jpg';
import designBook2 from '../assets/design_book2.jpg';
import designBook3 from '../assets/design_book3.jpeg';
import hyundaiDoc1 from '../assets/hyundai_document1.jpg';
import hyundaiDoc2 from '../assets/hyundai_document2.jpg';
import hyundaiDoc3 from '../assets/hyundai_document3.jpg';
import hyundaiDoc4 from '../assets/hyundai_document4.jpg';
import hyundaiDoc5 from '../assets/hyundai_document5.jpg';
import hyundaiDoc6 from '../assets/hyundai_document6.jpg';



// 카테고리 필터
const categoryFilters = [
  { id: 'all', name: 'All', active: true },
  { id: 'design', name: 'Design' },
  { id: 'engineering', name: 'Engineering' },
  { id: 'philosophy', name: 'Philosophy' },
  { id: 'business', name: 'Business' },
  { id: 'education', name: 'Education' }
];

// 추천 문서 데이터
const recommendedDocs = [
  {
    id: 1,
    title: "현대자동차 디자인 철학",
    author: "by 현대자동차 디자인팀",
    image: hyundaiDoc1,
    category: "디자인 철학"
  },
  {
    id: 2,
    title: "자동차 공기역학 연구",
    author: "by 공학 연구소",
    image: hyundaiDoc2,
    category: "공기역학"
  },
  {
    id: 3,
    title: "디자인 원리 가이드",
    author: "by 디자인 전문가",
    image: designBook1,
    category: "디자인 원리"
  },
  {
    id: 4,
    title: "인간공학적 접근",
    author: "by UX 연구팀",
    image: hyundaiDoc3,
    category: "인간공학"
  }
];

// 카테고리별 문서 데이터
const categoryDocs = [
  {
    id: 1,
    title: "현대자동차 디자인 철학",
    author: "by 현대자동차 디자인팀",
    image: hyundaiDoc1,
    category: "디자인 철학",
    rating: 4.5
  },
  {
    id: 2,
    title: "자동차 공기역학 연구",
    author: "by 공학 연구소",
    image: hyundaiDoc2,
    category: "공기역학",
    rating: 4.3
  },
  {
    id: 3,
    title: "디자인 원리 가이드",
    author: "by 디자인 전문가",
    image: designBook1,
    category: "디자인 원리",
    rating: 4.8
  },
  {
    id: 4,
    title: "인간공학적 접근",
    author: "by UX 연구팀",
    image: hyundaiDoc3,
    category: "인간공학",
    rating: 4.2
  },
  {
    id: 5,
    title: "모터스튜디오 디자인",
    author: "by 모터스튜디오",
    image: hyundaiDoc4,
    category: "모터스튜디오",
    rating: 4.6
  },
  {
    id: 6,
    title: "색상 디자인 전략",
    author: "by 컬러 전문가",
    image: designBook2,
    category: "색상 디자인",
    rating: 4.4
  },
  {
    id: 7,
    title: "전기차 디자인 트렌드",
    author: "by 미래 모빌리티팀",
    image: hyundaiDoc5,
    category: "전기차 디자인",
    rating: 4.7
  },
  {
    id: 8,
    title: "브랜드 아이덴티티",
    author: "by 브랜딩팀",
    image: designBook3,
    category: "브랜드 아이덴티티",
    rating: 4.1
  },
  {
    id: 9,
    title: "재료 공학 연구",
    author: "by 재료 연구소",
    image: hyundaiDoc6,
    category: "재료 공학",
    rating: 4.0
  }
];

function AssetLibrary() {
  const [activeMenu, setActiveMenu] = useState('discover');
  const [activeCategory, setActiveCategory] = useState('all');
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadForm, setUploadForm] = useState({
    documents: null,
    title: '',
    summary: '',
    category: '',
    coverPhoto: null
  });
  const [isUploading, setIsUploading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [showErrorModal, setShowErrorModal] = useState(false);

  // 사이드바 메뉴 클릭 핸들러
  const handleMenuClick = (menuId) => {
    setActiveMenu(menuId);
  };

  // 카테고리 필터 클릭 핸들러
  const handleCategoryClick = (categoryId) => {
    setActiveCategory(categoryId);
  };

  const handleAssetClick = async (asset) => {
    // 이미 모달이 열려있으면 무시
    if (selectedAsset) return;
    
    setSelectedAsset(asset);
    try {
      const response = await getComments(asset.lib_id);
      setComments(response.results || []);
    } catch (error) {
      console.error('댓글 로드 실패:', error);
    }
  };

  const handleCommentSubmit = async (e) => {
    e.preventDefault();
    if (!newComment.trim() || !selectedAsset) return;

    try {
      await createComment(selectedAsset.lib_id, newComment);
      setNewComment('');
      // 댓글 목록 새로고침
      const response = await getComments(selectedAsset.lib_id);
      setComments(response.results || []);
      // 자산 정보도 새로고침 (댓글 수 업데이트)
      loadAssets();
    } catch (error) {
      console.error('댓글 작성 실패:', error);
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    setUploadForm(prev => ({ ...prev, documents: file }));
  };

  const handleCoverPhotoUpload = (e) => {
    const file = e.target.files[0];
    setUploadForm(prev => ({ ...prev, coverPhoto: file }));
  };

  const clearCoverPhoto = () => {
    setUploadForm(prev => ({ ...prev, coverPhoto: null }));
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!uploadForm.documents || !uploadForm.title || !uploadForm.summary || !uploadForm.category) return;

    setIsUploading(true);
    try {
      await uploadAsset(uploadForm.documents, uploadForm.title, uploadForm.summary, uploadForm.category, uploadForm.coverPhoto);
      setShowUploadModal(false);
      setUploadForm({ documents: null, title: '', summary: '', category: '', coverPhoto: null });
      loadAssets();
    } catch (error) {
      console.error('업로드 실패:', error);
      
      // 파일 검증 오류 처리
      if (error.response?.data) {
        const { documents, cover_photo } = error.response.data;
        let errorMsg = '';
        
        if (documents && documents.length > 0) {
          errorMsg += `PDF 파일 오류: ${documents[0]}\n`;
        }
        if (cover_photo && cover_photo.length > 0) {
          errorMsg += `이미지 파일 오류: ${cover_photo[0]}\n`;
        }
        
        if (errorMsg) {
          setErrorMessage(errorMsg.trim());
          setShowErrorModal(true);
          // 오류가 있으면 업로드 화면 유지 (폼 리셋하지 않음)
          return;
        }
      }
      
      // 기타 오류
      setErrorMessage('업로드 중 오류가 발생했습니다. 다시 시도해주세요.');
      setShowErrorModal(true);
    } finally {
      setIsUploading(false);
    }
  };

  const handleAssetLike = async (assetId, e) => {
    if (e) e.stopPropagation();
    try {
      const response = await toggleAssetLike(assetId);
      
      // 자산 목록에서 해당 자산의 좋아요 수만 업데이트 (깜빡임 방지)
      setAssets(prevAssets => 
        prevAssets.map(asset => 
          asset.lib_id === assetId 
            ? { ...asset, likes: response.likes }
            : asset
        )
      );
      
      // 세부 화면이 열려있다면 해당 자산 정보도 업데이트
      if (selectedAsset && selectedAsset.lib_id === assetId) {
        setSelectedAsset(prev => ({ ...prev, likes: response.likes }));
      }
    } catch (error) {
      console.error('좋아요 처리 실패:', error);
    }
  };

  const handleCommentLike = async (commentId) => {
    try {
      const response = await toggleCommentLike(commentId);
      
      // 댓글 목록에서 해당 댓글의 좋아요 수만 업데이트 (깜빡임 방지)
      setComments(prevComments => 
        prevComments.map(comment => 
          comment.comment_id === commentId 
            ? { ...comment, likes: response.likes }
            : comment
        )
      );
    } catch (error) {
      console.error('댓글 좋아요 처리 실패:', error);
    }
  };

  const openPDF = (pdfPath) => {
    window.open(pdfPath, '_blank');
  };


  return (
    <div className="min-h-screen bg-gray-50">
      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slideUp {
          from { 
            opacity: 0;
            transform: translateY(20px);
          }
          to { 
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
      
      <Header isAssetLibrary={true} />

      <div className="flex pt-20">
        {/* Left Sidebar - Original Filtering Elements */}
        <div className="w-64 bg-white border-r border-gray-200 min-h-screen p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-6">자산 카테고리</h3>
            <div className="space-y-4">
            {[
              { name: '디자인 원리', subItems: ['디자인 철학', '브랜드 아이덴티티', '컨셉카'] },
              { name: '공학적 요소', subItems: ['공기역학', '인간공학', '재료 공학'] },
              { name: '차량 유형', subItems: ['전기차 디자인', 'SUV 디자인', '세단 디자인'] },
              { name: '디자인 요소', subItems: ['색상 디자인', '인테리어 디자인', '조명 디자인', '휠 디자인'] },
              { name: '사용자 중심', subItems: ['사용자 경험', '모터스튜디오'] }
            ].map((category, index) => (
              <div key={index} className="border-b border-gray-200 pb-3 last:border-b-0">
                  <div className="flex items-center justify-between mb-2">
                  <h4 className="text-lg font-semibold cursor-pointer transition-colors text-blue-600 hover:text-blue-700">
                      {category.name}
                    </h4>
                  </div>
                  {category.subItems.length > 0 && (
                    <div className="ml-4 space-y-1">
                      {category.subItems.map((item, itemIndex) => (
                        <div 
                          key={itemIndex} 
                        className="text-sm cursor-pointer transition-colors py-1 px-2 rounded text-gray-600 hover:text-gray-900 hover:bg-gray-100"
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

        {/* Main Content - Wider Layout */}
        <div className="flex-1 p-8">
          {/* Search and Upload Section */}
          <div className="bg-white border border-gray-200 rounded-lg p-6 mb-8">
            <div className="flex items-center justify-between">
              <div className="flex-1 max-w-md">
                <form onSubmit={(e) => e.preventDefault()} className="flex">
                  <input
                    type="text"
                    placeholder="Search any documents..."
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-l-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button 
                    type="submit"
                    className="px-6 py-2 bg-blue-600 text-white rounded-r-lg hover:bg-blue-700 transition-colors"
                  >
                    Search
                  </button>
                </form>
              </div>
              <button
                onClick={() => setShowUploadModal(true)}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
              >
                + 자산 업로드
              </button>
            </div>
          </div>

          {/* Recommended Section */}
          <div className="mb-12">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Recommended</h2>
              <button className="text-blue-600 hover:text-blue-700 font-medium">
                See All &gt;
              </button>
                  </div>
                  
            <div className="flex space-x-6 overflow-x-auto pb-4">
              {recommendedDocs.map((doc) => (
                <div key={doc.id} className="flex-shrink-0 w-48">
                  <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
                    <div className="h-32 bg-gray-200">
                      <img 
                        src={doc.image} 
                        alt={doc.title}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <div className="p-4">
                      <h3 className="font-semibold text-gray-900 text-sm mb-1 line-clamp-2">
                        {doc.title}
                      </h3>
                      <p className="text-gray-600 text-xs">{doc.author}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Categories Section - Wider Grid */}
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Categories</h2>
              <div className="flex items-center space-x-2">
                <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                </svg>
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
        </div>
            
            {/* Category Filters */}
            <div className="flex space-x-3 mb-6 overflow-x-auto pb-2">
              {categoryFilters.map((filter) => (
                <button 
                  key={filter.id}
                  onClick={() => handleCategoryClick(filter.id)}
                  className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
                    filter.active || activeCategory === filter.id
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {filter.name}
                    </button>
                  ))}
            </div>
            
            {/* Documents Grid - 3x3 Layout with Taller Cards */}
            <div className="grid grid-cols-3 gap-6">
              {categoryDocs.slice(0, 9).map((doc) => (
                <div key={doc.id} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
                  <div className="h-64 bg-gray-200 relative">
                    <img 
                      src={doc.image} 
                      alt={doc.title}
                      className="w-full h-full object-cover"
                    />
                    {doc.rating && (
                      <div className="absolute top-2 right-2 bg-yellow-400 text-yellow-900 px-2 py-1 rounded-full text-xs font-medium flex items-center">
                        <span className="mr-1">★</span>
                        {doc.rating}
                      </div>
                    )}
                  </div>
                  <div className="p-4">
                    <h3 className="font-semibold text-gray-900 text-sm mb-2 line-clamp-2">
                      {doc.title}
                    </h3>
                    <p className="text-gray-600 text-xs">{doc.author}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>


      {/* Asset Detail Modal */}
      {selectedAsset && (
        <div 
          className="fixed inset-0 flex items-center justify-center z-50"
          style={{
            animation: 'fadeIn 0.3s ease-out'
          }}
          onClick={() => setSelectedAsset(null)}
        >
          {/* 어두운 배경 오버레이 */}
          <div 
            className="absolute inset-0 bg-black" 
            style={{ opacity: 0.5 }}
          ></div>
          
          <div 
            className="relative bg-white rounded-2xl p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto shadow-2xl border border-gray-200"
            style={{
              animation: 'slideUp 0.3s ease-out'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-start mb-6">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                    {selectedAsset.category}
                  </span>
                  <span className="text-gray-500 text-sm">
                    {selectedAsset.upload_date}
                  </span>
                </div>
                <h2 className="text-gray-900 text-2xl font-semibold mb-3">
                  {selectedAsset.title}
                </h2>
                <p className="text-gray-600 text-base mb-4">
                  {selectedAsset.summary}
                </p>
                {/* Asset Like Button */}
                <div className="flex items-center space-x-4">
                  <button
                    onClick={() => handleAssetLike(selectedAsset.lib_id)}
                    className="flex items-center space-x-2 text-gray-500 hover:text-red-500 transition-colors"
                  >
                    <span className="text-xl">❤️</span>
                    <span className="text-sm">{selectedAsset.likes}</span>
                  </button>
                  <div className="flex items-center space-x-2 text-gray-500">
                    <span className="text-lg">💬</span>
                    <span className="text-sm">{selectedAsset.comment_count}</span>
                  </div>
                </div>
              </div>
              <button
                onClick={() => setSelectedAsset(null)}
                className="text-gray-500 hover:text-gray-700 text-2xl ml-4"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              {selectedAsset.img_path && (
                <div>
                  <h3 className="text-gray-900 text-lg font-semibold mb-3">대표 이미지</h3>
                  <img 
                    src={selectedAsset.img_path} 
                    alt="Asset" 
                    className="w-full rounded-lg"
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                  />
                </div>
              )}
              
              <div>
                <h3 className="text-gray-900 text-lg font-semibold mb-3">문서 정보</h3>
                <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <p className="text-gray-700 mb-2">
                    <span className="font-medium">파일명:</span> {selectedAsset.lib_name}
                  </p>
                  <button
                    onClick={() => openPDF(selectedAsset.pdf_path)}
                    className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    📄 PDF 열기
                  </button>
                </div>
              </div>
            </div>

            {/* Comments Section */}
            <div className="mt-6">
              <h3 className="text-gray-900 text-lg font-semibold mb-4">
                댓글 ({comments.length})
              </h3>
              
              {/* Comments List */}
              <div className="space-y-3 mb-4 max-h-60 overflow-y-auto custom-scrollbar">
                {comments.map((comment) => (
                  <div key={comment.comment_id} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="text-gray-900 font-medium">{comment.username}</span>
                        <span className="text-gray-500 text-xs">
                          {new Date(comment.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <button
                        onClick={() => handleCommentLike(comment.comment_id)}
                        className={`flex items-center space-x-1 text-sm transition-colors ${
                          comment.user_liked ? 'text-red-500' : 'text-gray-500 hover:text-red-500'
                        }`}
                      >
                        <span>❤️</span>
                        <span>{comment.likes}</span>
                      </button>
                    </div>
                    <p className="text-gray-700 text-sm">{comment.comments}</p>
                  </div>
                ))}
              </div>

              {/* Add Comment */}
              <form onSubmit={handleCommentSubmit} className="flex space-x-2">
                <input
                  type="text"
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  placeholder="댓글을 입력하세요..."
                  className="flex-1 px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:border-blue-500"
                />
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  작성
                </button>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-gray-900 text-xl font-semibold">자산 업로드</h2>
              <button
                onClick={() => setShowUploadModal(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleUpload} className="space-y-4">
              <div>
                <label className="block text-gray-700 text-sm font-medium mb-2">
                  문서 파일 *
                </label>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handleFileUpload}
                  className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:border-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-gray-700 text-sm font-medium mb-2">
                  커버 사진 (선택사항)
                </label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleCoverPhotoUpload}
                  className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:border-blue-500"
                />
                <p className="text-gray-500 text-xs mt-1">
                  커버 사진을 업로드하지 않으면 제목을 기반으로 자동으로 이미지를 생성합니다.
                </p>
                {!uploadForm.coverPhoto && (
                  <div className="mt-2 p-2 bg-blue-50 rounded border border-blue-200">
                    <p className="text-blue-600 text-xs">
                      💡 커버 사진을 업로드하지 않으면 제목을 기반으로 Unsplash에서 관련 이미지를 자동으로 검색합니다.
                    </p>
                  </div>
                )}
                {uploadForm.coverPhoto && (
                  <div className="mt-2">
                    <p className="text-green-600 text-xs mb-2">선택된 커버 사진:</p>
                    <div className="flex items-center space-x-2">
                      <img 
                        src={URL.createObjectURL(uploadForm.coverPhoto)} 
                        alt="Cover preview" 
                        className="w-20 h-20 object-cover rounded border border-gray-300"
                      />
                      <button
                        type="button"
                        onClick={clearCoverPhoto}
                        className="px-2 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700 transition-colors"
                      >
                        제거
                      </button>
                    </div>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-gray-700 text-sm font-medium mb-2">
                  제목 *
                </label>
                <input
                  type="text"
                  value={uploadForm.title}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, title: e.target.value }))}
                  placeholder="문서 제목을 입력하세요"
                  className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:border-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-gray-700 text-sm font-medium mb-2">
                  요약 *
                </label>
                <textarea
                  value={uploadForm.summary}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, summary: e.target.value }))}
                  placeholder="문서 내용을 요약해주세요"
                  rows="3"
                  className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:border-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-gray-700 text-sm font-medium mb-2">
                  카테고리 *
                </label>
                <select
                  value={uploadForm.category}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, category: e.target.value }))}
                  className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:border-blue-500"
                  required
                >
                  <option value="">카테고리를 선택하세요</option>
                  <option value="디자인 철학">디자인 철학</option>
                  <option value="모터스튜디오">모터스튜디오</option>
                  <option value="공기역학">공기역학</option>
                  <option value="인간공학">인간공학</option>
                  <option value="색상 디자인">색상 디자인</option>
                  <option value="재료 공학">재료 공학</option>
                  <option value="사용자 경험">사용자 경험</option>
                  <option value="전기차 디자인">전기차 디자인</option>
                  <option value="SUV 디자인">SUV 디자인</option>
                  <option value="세단 디자인">세단 디자인</option>
                  <option value="컨셉카">컨셉카</option>
                  <option value="브랜드 아이덴티티">브랜드 아이덴티티</option>
                  <option value="인테리어 디자인">인테리어 디자인</option>
                  <option value="조명 디자인">조명 디자인</option>
                  <option value="휠 디자인">휠 디자인</option>
                </select>
              </div>

              <div className="flex space-x-2">
                <button
                  type="submit"
                  disabled={isUploading}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isUploading ? '업로드 중...' : '업로드'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  disabled={isUploading}
                  className="flex-1 px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  취소
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 오류 모달 */}
      {showErrorModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center mb-4">
              <div className="flex-shrink-0">
                <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-lg font-medium text-gray-900">업로드 오류</h3>
              </div>
            </div>
            <div className="mb-4">
              <p className="text-sm text-gray-600 whitespace-pre-line">{errorMessage}</p>
            </div>
            <div className="flex justify-end">
              <button
                onClick={() => {
                  setShowErrorModal(false);
                  setErrorMessage('');
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                확인
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Footer with custom styling for Asset Library */}
      <Footer isAssetLibrary={true} />
    </div>
  );
}

export default AssetLibrary; 