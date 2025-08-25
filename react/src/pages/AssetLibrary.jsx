import React, { useState, useEffect } from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { getAssets, uploadAsset, getComments, createComment, toggleAssetLike, toggleCommentLike } from '../services/libraryService';
import backgroundImage from '../assets/AssetLibrary_background.png';

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

  useEffect(() => {
    loadAssets();
  }, [currentPage]);

  const loadAssets = async () => {
    setIsLoading(true);
    try {
              const response = await getAssets(currentPage, 6, searchTerm, searchType);
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

  const handleAssetClick = async (asset) => {
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
    } finally {
      setIsUploading(false);
    }
  };

  const handleAssetLike = async (assetId, e) => {
    if (e) e.stopPropagation();
    try {
      await toggleAssetLike(assetId);
      loadAssets(); // 자산 목록 새로고침
    } catch (error) {
      console.error('좋아요 처리 실패:', error);
    }
  };

  const handleCommentLike = async (commentId) => {
    try {
      await toggleCommentLike(commentId);
      // 댓글 목록 새로고침
      if (selectedAsset) {
        const response = await getComments(selectedAsset.lib_id);
        setComments(response.results || []);
      }
    } catch (error) {
      console.error('댓글 좋아요 처리 실패:', error);
    }
  };

  const openPDF = (pdfPath) => {
    window.open(pdfPath, '_blank');
  };

  return (
    <div className="min-h-screen" style={{backgroundColor: '#353745'}}>
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

      {/* Main Content */}
      <section className="py-12">
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
                        onError={(e) => {
                          e.target.style.display = 'none';
                        }}
                      />
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
                      {asset.documents}
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
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
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
                    <span className="font-medium">파일명:</span> {selectedAsset.documents}
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
      
      <Footer />
    </div>
  );
}

export default AssetLibrary; 