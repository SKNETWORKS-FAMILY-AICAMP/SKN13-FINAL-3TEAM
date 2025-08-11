import React, { useState, useEffect } from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { getAssets, uploadAsset, getComments, createComment } from '../services/libraryService';

function AssetLibrary() {
  const [assets, setAssets] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadForm, setUploadForm] = useState({
    documents: null,
    imgPath: ''
  });

  useEffect(() => {
    loadAssets();
  }, [currentPage, searchTerm]);

  const loadAssets = async () => {
    setIsLoading(true);
    try {
      const response = await getAssets(currentPage, 10, searchTerm);
      setAssets(response.results || []);
      setTotalPages(Math.ceil(response.count / 10));
    } catch (error) {
      console.error('자산 로드 실패:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setCurrentPage(1);
    loadAssets();
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
    } catch (error) {
      console.error('댓글 작성 실패:', error);
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    setUploadForm(prev => ({ ...prev, documents: file }));
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!uploadForm.documents && !uploadForm.imgPath) return;

    try {
      await uploadAsset(uploadForm.documents, uploadForm.imgPath);
      setShowUploadModal(false);
      setUploadForm({ documents: null, imgPath: '' });
      loadAssets();
    } catch (error) {
      console.error('업로드 실패:', error);
    }
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
              background: 'radial-gradient(circle, rgba(59, 130, 246, 0.3) 0%, rgba(139, 92, 246, 0.2) 50%, transparent 100%)',
              filter: 'blur(60px)'
            }}></div>
          </div>
          
          {/* Content */}
          <div className="relative z-10">
            <h1 className="text-6xl font-bold text-white mb-6">Asset Library</h1>
            <p className="text-gray-300 text-xl mb-8">
              A starting point of inspiration that sparks a designer's imagination.
            </p>
            <div className="text-gray-400 space-y-2 mb-8">
              <p>디자인 리소스를 한눈에 모아보고 조합하세요.</p>
              <p>자동차 디자인에 필요한 이미지, 컬러 팔레트, 파츠 요소 등을 태그 기반으로 쉽게 탐색할 수 있습니다.</p>
            </div>
            
            {/* Search Bar */}
            <form onSubmit={handleSearch} className="flex max-w-md mx-auto">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="검색어를 입력해주세요"
                className="flex-1 px-4 py-3 bg-white border border-gray-300 rounded-l-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:border-blue-500"
              />
              <button 
                type="submit"
                className="px-6 py-3 bg-blue-600 text-white rounded-r-lg hover:bg-blue-700 transition-colors"
              >
                Search
              </button>
            </form>

            {/* Upload Button */}
            <button
              onClick={() => setShowUploadModal(true)}
              className="mt-4 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              + 자산 업로드
            </button>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <section className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Assets Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
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
                  <h3 className="text-white text-xl font-semibold mb-4">
                    {asset.documents || '제목 없음'}
                  </h3>
                  {asset.img_path && (
                    <div className="bg-gray-700 rounded-lg p-4 mb-4 h-32 flex items-center justify-center">
                      <img 
                        src={asset.img_path} 
                        alt="Asset preview" 
                        className="max-w-full max-h-full object-contain"
                        onError={(e) => {
                          e.target.style.display = 'none';
                        }}
                      />
                    </div>
                  )}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-4 bg-blue-500 rounded-full"></div>
                      <span className="text-gray-400 text-sm">디자인 자산</span>
                    </div>
                    <span className="text-gray-400 text-sm">
                      {new Date().toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-12 flex items-center justify-center space-x-4">
              <button 
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                className="text-gray-400 hover:text-white transition-colors disabled:opacity-50"
              >
                ← Previous
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
                Next →
              </button>
            </div>
          )}
        </div>
      </section>

      {/* Asset Detail Modal */}
      {selectedAsset && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-white text-2xl font-semibold">
                {selectedAsset.documents || '제목 없음'}
              </h2>
              <button
                onClick={() => setSelectedAsset(null)}
                className="text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            {selectedAsset.img_path && (
              <div className="mb-4">
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

            {/* Comments Section */}
            <div className="mt-6">
              <h3 className="text-white text-lg font-semibold mb-4">댓글</h3>
              
              {/* Comments List */}
              <div className="space-y-3 mb-4">
                {comments.map((comment) => (
                  <div key={comment.comment_id} className="bg-gray-700 rounded-lg p-3">
                    <p className="text-white text-sm">{comment.comments}</p>
                    <p className="text-gray-400 text-xs mt-1">
                      {new Date().toLocaleDateString()}
                    </p>
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
                  문서 파일
                </label>
                <input
                  type="file"
                  onChange={handleFileUpload}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                />
              </div>

              <div>
                <label className="block text-white text-sm font-medium mb-2">
                  이미지 경로
                </label>
                <input
                  type="text"
                  value={uploadForm.imgPath}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, imgPath: e.target.value }))}
                  placeholder="이미지 URL을 입력하세요"
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="flex space-x-2">
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  업로드
                </button>
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
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