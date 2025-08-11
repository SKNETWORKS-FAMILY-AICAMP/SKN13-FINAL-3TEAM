import React, { useState, useEffect } from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { 
  getGeneratedResults, 
  createGeneratedResult 
} from '../services/chatService';

function PrototypeLab() {
  const [prompt, setPrompt] = useState('');
  const [resultType, setResultType] = useState('text');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedResults, setGeneratedResults] = useState([]);
  const [selectedPromptId, setSelectedPromptId] = useState(null);
  const [showResults, setShowResults] = useState(false);

  // 목업 데이터
  const mockResults = [
    {
      result_id: 'result-1',
      prompt_id: 'prompt-1',
      result_type: 'text',
      result_path: '/results/text-1.txt',
      result: '현대차 디자인 분석 결과: 아이오닉 시리즈는 미래지향적 디자인과 친환경 기술의 조화를 보여줍니다.'
    },
    {
      result_id: 'result-2',
      prompt_id: 'prompt-1',
      result_type: 'image',
      result_path: '/results/image-1.jpg',
      result: '생성된 이미지 URL'
    },
    {
      result_id: 'result-3',
      prompt_id: 'prompt-2',
      result_type: '3d',
      result_path: '/results/3d-1.obj',
      result: '3D 모델 파일 경로'
    }
  ];

  useEffect(() => {
    // 초기 결과 로드
    setGeneratedResults(mockResults);
  }, []);

  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setIsGenerating(true);
    
    try {
      // 실제로는 AI 서비스와 연동하여 결과 생성
      const mockPromptId = `prompt-${Date.now()}`;
      const mockResult = {
        result_id: `result-${Date.now()}`,
        prompt_id: mockPromptId,
        result_type: resultType,
        result_path: `/results/${resultType}-${Date.now()}.${getFileExtension(resultType)}`,
        result: generateMockResult(prompt, resultType)
      };

      // 결과 저장
      await createGeneratedResult(mockPromptId, resultType, mockResult.result_path, mockResult.result);
      
      // 결과 목록에 추가
      setGeneratedResults(prev => [mockResult, ...prev]);
      setSelectedPromptId(mockPromptId);
      setShowResults(true);
      setPrompt('');
    } catch (error) {
      console.error('생성 실패:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const generateMockResult = (prompt, type) => {
    switch (type) {
      case 'text':
        return `프롬프트 "${prompt}"에 대한 분석 결과입니다. 현대차 디자인 트렌드와 사용자 선호도를 종합적으로 분석한 결과입니다.`;
      case 'image':
        return 'https://via.placeholder.com/400x300/4F46E5/FFFFFF?text=Generated+Image';
      case '3d':
        return '3D 모델링 파일이 생성되었습니다. 다운로드하여 3D 뷰어에서 확인하세요.';
      case '4d':
        return '4D 시뮬레이션 결과입니다. 시간에 따른 변화를 포함한 동적 모델입니다.';
      default:
        return '결과가 생성되었습니다.';
    }
  };

  const getFileExtension = (type) => {
    switch (type) {
      case 'text':
        return 'txt';
      case 'image':
        return 'jpg';
      case '3d':
        return 'obj';
      case '4d':
        return 'mp4';
      default:
        return 'txt';
    }
  };

  const getResultIcon = (type) => {
    switch (type) {
      case 'text':
        return '📄';
      case 'image':
        return '🖼️';
      case '3d':
        return '🎲';
      case '4d':
        return '🎬';
      default:
        return '📄';
    }
  };

  const getResultTypeLabel = (type) => {
    switch (type) {
      case 'text':
        return '텍스트';
      case 'image':
        return '이미지';
      case '3d':
        return '3D 모델';
      case '4d':
        return '4D 시뮬레이션';
      default:
        return '텍스트';
    }
  };

  return (
    <div className="min-h-screen" style={{backgroundColor: '#353745'}}>
      <Header />
      
      <div className="flex">
        {/* Left Sidebar */}
        <div className="w-80 bg-gray-800 min-h-screen p-6 border-r border-gray-700">
          <h2 className="text-white text-xl font-semibold mb-6">생성 결과</h2>
          
          <div className="space-y-4">
            {generatedResults.map((result) => (
              <div 
                key={result.result_id}
                onClick={() => {
                  setSelectedPromptId(result.prompt_id);
                  setShowResults(true);
                }}
                className="bg-gray-700 rounded-lg p-4 cursor-pointer hover:bg-gray-600 transition-colors"
              >
                <div className="flex items-center space-x-2 mb-2">
                  <span className="text-lg">{getResultIcon(result.result_type)}</span>
                  <span className="text-white text-sm font-medium">
                    {getResultTypeLabel(result.result_type)} 결과
                  </span>
                </div>
                <p className="text-gray-400 text-xs">
                  {new Date().toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1">
          <div className="max-w-6xl mx-auto px-8 py-12">
            {/* Hero Section */}
            <div className="text-center mb-16">
              <h1 className="text-6xl font-bold text-white mb-6">Prototype Lab</h1>
              <p className="text-gray-300 text-xl mb-8">
                Turn your ideas into images — with just one prompt.
              </p>
              <p className="text-gray-400 max-w-3xl mx-auto">
                다양한 조건을 프롬프트로 입력하면, AI가 text-to-image 및 image-to-image 기술로 다채로운 시각적 프로토타입을 생성해줍니다.
              </p>
            </div>

            {/* Background Graphic */}
            <div className="relative mb-16">
              <div className="absolute inset-0 bg-gradient-to-b from-transparent to-gray-800 opacity-30"></div>
              <div className="relative z-10 h-32 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-lg"></div>
            </div>

            {/* Generation Form */}
            <div className="max-w-4xl mx-auto mb-16">
              <div className="bg-gray-800 rounded-lg p-8 border border-gray-700">
                <h3 className="text-white text-xl font-semibold mb-6">프로토타입 생성</h3>
                
                {/* Result Type Selection */}
                <div className="mb-6">
                  <label className="block text-white text-sm font-medium mb-3">결과 타입</label>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {[
                      { type: 'text', label: '텍스트', icon: '📄' },
                      { type: 'image', label: '이미지', icon: '🖼️' },
                      { type: '3d', label: '3D 모델', icon: '🎲' },
                      { type: '4d', label: '4D 시뮬레이션', icon: '🎬' }
                    ].map((option) => (
                      <button
                        key={option.type}
                        onClick={() => setResultType(option.type)}
                        className={`p-4 rounded-lg border transition-colors ${
                          resultType === option.type
                            ? 'bg-blue-600 border-blue-500 text-white'
                            : 'bg-gray-700 border-gray-600 text-gray-300 hover:bg-gray-600'
                        }`}
                      >
                        <div className="text-2xl mb-2">{option.icon}</div>
                        <div className="text-sm font-medium">{option.label}</div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Prompt Input */}
                <form onSubmit={handleGenerate} className="space-y-4">
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">
                      프롬프트 입력
                    </label>
                    <textarea
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                      placeholder="생성하고 싶은 프로토타입에 대해 자세히 설명해주세요..."
                      className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 resize-none"
                      rows={4}
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={!prompt.trim() || isGenerating}
                    className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isGenerating ? '생성 중...' : '프로토타입 생성'}
                  </button>
                </form>
              </div>
            </div>

            {/* Results Display */}
            {showResults && selectedPromptId && (
              <div className="max-w-4xl mx-auto">
                <div className="bg-gray-800 rounded-lg p-8 border border-gray-700">
                  <h3 className="text-white text-xl font-semibold mb-6">생성 결과</h3>
                  
                  <div className="space-y-4">
                    {generatedResults
                      .filter(result => result.prompt_id === selectedPromptId)
                      .map((result) => (
                        <div key={result.result_id} className="bg-gray-700 rounded-lg p-6">
                          <div className="flex items-center space-x-3 mb-4">
                            <span className="text-2xl">{getResultIcon(result.result_type)}</span>
                            <span className="text-white font-medium">
                              {getResultTypeLabel(result.result_type)} 결과
                            </span>
                          </div>
                          
                          {result.result_type === 'text' && (
                            <div className="bg-gray-600 rounded-lg p-4">
                              <p className="text-white">{result.result}</p>
                            </div>
                          )}
                          
                          {result.result_type === 'image' && (
                            <div className="text-center">
                              <img 
                                src={result.result} 
                                alt="Generated" 
                                className="max-w-full h-auto rounded-lg"
                                onError={(e) => {
                                  e.target.style.display = 'none';
                                  e.target.nextSibling.style.display = 'block';
                                }}
                              />
                              <div className="hidden bg-gray-600 rounded-lg p-8 text-gray-400">
                                이미지 로드 실패
                              </div>
                            </div>
                          )}
                          
                          {result.result_type === '3d' && (
                            <div className="bg-gray-600 rounded-lg p-4 text-center">
                              <div className="text-4xl mb-2">🎲</div>
                              <p className="text-white">{result.result}</p>
                              <button className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                                3D 모델 다운로드
                              </button>
                            </div>
                          )}
                          
                          {result.result_type === '4d' && (
                            <div className="bg-gray-600 rounded-lg p-4 text-center">
                              <div className="text-4xl mb-2">🎬</div>
                              <p className="text-white">{result.result}</p>
                              <button className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                                4D 시뮬레이션 재생
                              </button>
                            </div>
                          )}
                          
                          <div className="mt-4 text-gray-400 text-sm">
                            생성 시간: {new Date().toLocaleString()}
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
}

export default PrototypeLab; 