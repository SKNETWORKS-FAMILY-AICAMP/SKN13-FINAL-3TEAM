import React, { useState, useEffect } from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { getAssets, uploadAsset, getComments, createComment, toggleAssetLike, toggleCommentLike } from '../services/libraryService';
import backgroundImage from '../assets/AssetLibrary_background.png';

// 자산 카테고리 대분류 구조
const assetCategories = [
  {
    name: '디자인 원리',
    subItems: [
      '디자인 철학',
      '브랜드 아이덴티티',
      '컨셉카'
    ]
  },
  {
    name: '공학적 요소',
    subItems: [
      '공기역학',
      '인간공학',
      '재료 공학'
    ]
  },
  {
    name: '차량 유형',
    subItems: [
      '전기차 디자인',
      'SUV 디자인',
      '세단 디자인'
    ]
  },
  {
    name: '디자인 요소',
    subItems: [
      '색상 디자인',
      '인테리어 디자인',
      '조명 디자인',
      '휠 디자인'
    ]
  },
  {
    name: '사용자 중심',
    subItems: [
      '사용자 경험',
      '모터스튜디오'
    ]
  }
];

function AssetLibrary() {
  const [assets, setAssets] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchType, setSearchType] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
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
  const [selectedCategories, setSelectedCategories] = useState(new Set());
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    loadAssets();
  }, [currentPage, selectedCategories]);

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const loadAssets = async () => {
    setIsLoading(true);
    try {
      // 선택된 카테고리가 있으면 필터링 적용
      const categoryFilter = selectedCategories.size > 0 ? Array.from(selectedCategories).join(',') : '';
      const response = await getAssets(currentPage, 6, searchTerm, searchType, categoryFilter);
      setAssets(response.results || []);
      setTotalPages(Math.ceil(response.count / 6));
    } catch (error) {
      console.error('자산 로드 실패:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const searchValue = formData.get('search') || '';
    setSearchTerm(searchValue);
    setCurrentPage(1);
    // 검색어가 변경된 후 loadAssets 호출
    setTimeout(() => {
      loadAssets();
    }, 0);
  };

  // 카테고리 선택/해제 핸들러
  const handleCategorySelect = (category) => {
    setSelectedCategories(prev => {
      const newSet = new Set(prev);
      if (newSet.has(category)) {
        newSet.delete(category);
      } else {
        newSet.add(category);
      }
      return newSet;
    });
    setCurrentPage(1);
  };

  // 대분류 클릭 핸들러 (하위 모든 소분류 선택/해제)
  const handleMainCategorySelect = (mainCategory) => {
    const category = assetCategories.find(cat => cat.name === mainCategory);
    if (!category) return;

    const allSubItemsSelected = category.subItems.every(item => selectedCategories.has(item));
    
    setSelectedCategories(prev => {
      const newSet = new Set(prev);
      if (allSubItemsSelected) {
        // 모든 하위 항목이 선택되어 있으면 모두 해제
        category.subItems.forEach(item => newSet.delete(item));
      } else {
        // 일부만 선택되어 있으면 모두 선택
        category.subItems.forEach(item => newSet.add(item));
      }
      return newSet;
    });
    setCurrentPage(1);
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
    <div className="min-h-screen" style={{backgroundColor: '#353745'}}>
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
      <Header />
      
      {/* Hero Section */}
      <section className="relative py-24 lg:py-32" style={{
        backgroundImage: `url(${backgroundImage})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        minHeight: '60vh',
        opacity: selectedAsset ? 0.8 : 1,
        transition: 'opacity 0.3s ease-out'
      }}>
        {/* Dark overlay for better text readability */}
        <div className="absolute inset-0 bg-black/50"></div>
        
        {/* Content */}
        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-6xl font-bold text-white mb-6">Asset Library</h1>
          <p className="text-gray-300 text-xl mb-8">
            A starting point of inspiration that sparks a designer's imagination.
          </p>
          <div className="text-gray-400 space-y-2 mb-8">
            <p>디자인 리소스를 한눈에 모아보고 조합하세요.</p>
            <p>자동차 디자인에 필요한 이미지, 컬러 팔레트, 파츠 요소 등을 태그 기반으로 쉽게 탐색할 수 있습니다.</p>
          </div>
          
          {/* Search Bar */}
          <form onSubmit={handleSearch} className="flex flex-col max-w-md mx-auto space-y-3">
            <div className="flex space-x-2">
              <select
                value={searchType}
                onChange={(e) => setSearchType(e.target.value)}
                className="px-3 py-3 bg-white border border-gray-300 rounded-l-lg text-gray-900 focus:outline-none focus:border-blue-500"
              >
                <option value="all">전체 검색</option>
                <option value="title">제목만</option>
                <option value="summary">요약만</option>
              </select>
                      <input
        type="text"
        name="search"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        placeholder="검색어를 입력하세요"
        className="flex-1 px-4 py-3 bg-white border border-gray-300 text-gray-900 placeholder-gray-500 focus:outline-none focus:border-blue-500"
      />
              <button 
                type="submit"
                className="px-6 py-3 bg-blue-600 text-white rounded-r-lg hover:bg-blue-700 transition-colors"
              >
                Search
              </button>
            </div>
          </form>

          {/* Upload Button */}
          <button
            onClick={() => setShowUploadModal(true)}
            className="mt-4 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            + 자산 업로드
          </button>
        </div>
      </section>

      {/* 자산 카테고리 박스 */}
      <div className="fixed left-2 z-50 w-60 max-h-[80vh]" style={{ 
        top: `${Math.max(24, window.innerHeight / 2 - 350 - Math.min(scrollY * 0.4, 80) + Math.min(scrollY * 0.4, 80))}px`, 
        transform: 'none', 
        transition: 'top 0.1s ease-out' 
      }}>
        <div className="bg-gray-900/90 backdrop-blur-md rounded-2xl border border-gray-700 shadow-2xl">
          <div className="p-6 border-b border-gray-700">
            <h3 className="text-xl font-bold text-white text-center">자산 카테고리</h3>
          </div>
          <div className="p-6 max-h-[calc(80vh-80px)] overflow-y-auto">
            <div className="space-y-4">
              {assetCategories.map((category, index) => (
                <div key={index} className="border-b border-gray-700 pb-3 last:border-b-0">
                  <div className="flex items-center justify-between mb-2">
                    <h4 
                      className="text-lg font-semibold cursor-pointer transition-colors text-blue-400 hover:text-blue-300"
                      onClick={() => handleMainCategorySelect(category.name)}
                    >
                      {category.name}
                    </h4>
                    {category.subItems.length > 0 && (
                      <span className="text-xs text-gray-400 bg-gray-800 px-2 py-1 rounded-full">
                        {category.subItems.filter(item => selectedCategories.has(item)).length}/{category.subItems.length}
                      </span>
                    )}
                  </div>
                  {category.subItems.length > 0 && (
                    <div className="ml-4 space-y-1">
                      {category.subItems.map((item, itemIndex) => (
                        <div 
                          key={itemIndex} 
                          className={`text-sm cursor-pointer transition-colors py-1 px-2 rounded ${
                            selectedCategories.has(item)
                              ? 'text-white bg-blue-600/50 border border-blue-500/50'
                              : 'text-gray-300 hover:text-white hover:bg-gray-800/50'
                          }`}
                          onClick={() => handleCategorySelect(item)}
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

      {/* Main Content */}
      <section className="py-12" style={{
        opacity: selectedAsset ? 0.5 : 1,
        transition: 'opacity 0.3s ease-out'
      }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Assets Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8" style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '32px'
          }}>
            {isLoading ? (
              <div className="col-span-full text-center text-white">로딩 중...</div>
            ) : assets.length === 0 ? (
              <div className="col-span-full text-center text-gray-400">
                업로드된 자산이 없습니다.
              </div>
            ) : (
              assets.map((asset) => (
                <div 
                  key={asset.lib_id}
                  onClick={() => handleAssetClick(asset)}
                  className="bg-gray-800 rounded-lg p-6 border border-gray-700 cursor-pointer hover:border-blue-500 transition-colors"
                >
                  <div className="flex items-center justify-between mb-3">
                    <span className="px-2 py-1 bg-blue-600 text-white text-xs rounded-full">
                      {asset.category}
                    </span>
                    <span className="text-gray-400 text-xs">
                      {asset.upload_date}
                    </span>
                  </div>
                  
                  <h3 className="text-white text-xl font-semibold mb-3 line-clamp-2">
                    {asset.title}
                  </h3>
                  
                  <p className="text-gray-300 text-sm mb-4 line-clamp-3">
                    {asset.summary}
                  </p>
                  
                  {asset.img_path && (
                    <div className="bg-gray-700 rounded-lg p-4 mb-4 h-32 flex items-center justify-center">
                      <img 
                        src={asset.img_path} 
                        alt="Asset preview" 
                        className="max-w-full max-h-full object-contain rounded"
                        onLoad={() => console.log('✅ 이미지 로드 성공:', asset.img_path)}
                        onError={(e) => {
                          console.log('❌ 이미지 로드 실패:', asset.img_path);
                          e.target.style.display = 'none';
                        }}
                      />
                    </div>
                  )}
                  {!asset.img_path && (
                    <div className="bg-gray-700 rounded-lg p-4 mb-4 h-32 flex items-center justify-center">
                      <p className="text-gray-400 text-sm">이미지 없음 (img_path: {asset.img_path})</p>
                    </div>
                  )}
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <button
                        onClick={(e) => handleAssetLike(asset.lib_id, e)}
                        className="flex items-center space-x-1 text-gray-400 hover:text-red-500 transition-colors"
                      >
                        <span className="text-lg">❤️</span>
                        <span className="text-sm">{asset.likes}</span>
                      </button>
                      <div className="flex items-center space-x-1 text-gray-400">
                        <span className="text-lg">💬</span>
                        <span className="text-sm">{asset.comment_count}</span>
                      </div>
                    </div>
                    <div className="text-gray-400 text-xs">
                      {asset.lib_name}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Pagination */}
          {totalPages >= 1 && (
            <div className="mt-12 flex flex-col items-center space-y-4">
                      <div className="text-gray-400 text-sm">
          한 페이지당 6개씩 표시
        </div>
              <div className="flex items-center justify-center space-x-4">
                <button 
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  disabled={currentPage === 1}
                  className="text-gray-400 hover:text-white transition-colors disabled:opacity-50"
                >
                  ← 이전
                </button>
                <div className="flex space-x-2">
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                    <button
                      key={page}
                      onClick={() => setCurrentPage(page)}
                      className={`w-8 h-8 rounded-full text-sm ${
                        page === currentPage
                          ? 'bg-gray-600 text-white'
                          : 'bg-gray-700 text-gray-400 hover:bg-gray-600 hover:text-white'
                      }`}
                    >
                      {page}
                    </button>
                  ))}
                </div>
                <button 
                  onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                  disabled={currentPage === totalPages}
                  className="text-gray-400 hover:text-white transition-colors disabled:opacity-50"
                >
                  다음 →
                </button>
              </div>
            </div>
          )}
        </div>
      </section>

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
            style={{ opacity: 0.6 }}
          ></div>
          
          <div 
            className="relative bg-gray-800 rounded-2xl p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto shadow-2xl border-2 border-gray-600"
            style={{
              animation: 'slideUp 0.3s ease-out',
              backgroundColor: 'rgba(31, 41, 55, 0.95)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-start mb-6">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <span className="px-3 py-1 bg-blue-600 text-white text-sm rounded-full">
                    {selectedAsset.category}
                  </span>
                  <span className="text-gray-400 text-sm">
                    {selectedAsset.upload_date}
                  </span>
                </div>
                <h2 className="text-white text-2xl font-semibold mb-3">
                  {selectedAsset.title}
                </h2>
                <p className="text-gray-300 text-base mb-4">
                  {selectedAsset.summary}
                </p>
                {/* Asset Like Button */}
                <div className="flex items-center space-x-4">
                  <button
                    onClick={() => handleAssetLike(selectedAsset.lib_id)}
                    className="flex items-center space-x-2 text-gray-400 hover:text-red-500 transition-colors"
                  >
                    <span className="text-xl">❤️</span>
                    <span className="text-sm">{selectedAsset.likes}</span>
                  </button>
                  <div className="flex items-center space-x-2 text-gray-400">
                    <span className="text-lg">💬</span>
                    <span className="text-sm">{selectedAsset.comment_count}</span>
                  </div>
                </div>
              </div>
              <button
                onClick={() => setSelectedAsset(null)}
                className="text-gray-400 hover:text-white text-2xl ml-4"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              {selectedAsset.img_path && (
                <div>
                  <h3 className="text-white text-lg font-semibold mb-3">대표 이미지</h3>
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
                <h3 className="text-white text-lg font-semibold mb-3">문서 정보</h3>
                <div className="bg-gray-700 rounded-lg p-4">
                  <p className="text-gray-300 mb-2">
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
              <h3 className="text-white text-lg font-semibold mb-4">
                댓글 ({comments.length})
              </h3>
              
              {/* Comments List */}
              <div className="space-y-3 mb-4 max-h-60 overflow-y-auto custom-scrollbar">
                {comments.map((comment) => (
                  <div key={comment.comment_id} className="bg-gray-700 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="text-white font-medium">{comment.username}</span>
                        <span className="text-gray-400 text-xs">
                          {new Date(comment.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <button
                        onClick={() => handleCommentLike(comment.comment_id)}
                        className={`flex items-center space-x-1 text-sm transition-colors ${
                          comment.user_liked ? 'text-red-500' : 'text-gray-400 hover:text-red-500'
                        }`}
                      >
                        <span>❤️</span>
                        <span>{comment.likes}</span>
                      </button>
                    </div>
                    <p className="text-white text-sm">{comment.comments}</p>
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
                  className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
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
          <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-white text-xl font-semibold">자산 업로드</h2>
              <button
                onClick={() => setShowUploadModal(false)}
                className="text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleUpload} className="space-y-4">
              <div>
                <label className="block text-white text-sm font-medium mb-2">
                  문서 파일 *
                </label>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handleFileUpload}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                  required
                />
              </div>

              <div>
                <label className="block text-white text-sm font-medium mb-2">
                  커버 사진 (선택사항)
                </label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleCoverPhotoUpload}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                />
                <p className="text-gray-400 text-xs mt-1">
                  커버 사진을 업로드하지 않으면 제목을 기반으로 자동으로 이미지를 생성합니다.
                </p>
                {!uploadForm.coverPhoto && (
                  <div className="mt-2 p-2 bg-gray-700 rounded border border-gray-600">
                    <p className="text-blue-400 text-xs">
                      💡 커버 사진을 업로드하지 않으면 제목을 기반으로 Unsplash에서 관련 이미지를 자동으로 검색합니다.
                    </p>
                  </div>
                )}
                {uploadForm.coverPhoto && (
                  <div className="mt-2">
                    <p className="text-green-400 text-xs mb-2">선택된 커버 사진:</p>
                    <div className="flex items-center space-x-2">
                      <img 
                        src={URL.createObjectURL(uploadForm.coverPhoto)} 
                        alt="Cover preview" 
                        className="w-20 h-20 object-cover rounded border border-gray-600"
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
                <label className="block text-white text-sm font-medium mb-2">
                  제목 *
                </label>
                <input
                  type="text"
                  value={uploadForm.title}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, title: e.target.value }))}
                  placeholder="문서 제목을 입력하세요"
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-white text-sm font-medium mb-2">
                  요약 *
                </label>
                <textarea
                  value={uploadForm.summary}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, summary: e.target.value }))}
                  placeholder="문서 내용을 요약해주세요"
                  rows="3"
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-white text-sm font-medium mb-2">
                  카테고리 *
                </label>
                <select
                  value={uploadForm.category}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, category: e.target.value }))}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
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
                  className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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
      
      <Footer />
    </div>
  );
}

export default AssetLibrary; 