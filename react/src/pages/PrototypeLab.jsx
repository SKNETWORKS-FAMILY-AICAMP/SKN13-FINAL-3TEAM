import React, { useState, useEffect, useRef } from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { 
  getChatSessions, 
  createChatSession, 
  getPromptLogs,
  sendChatMessage 
} from '../services/chatService';
import backgroundImage from '../assets/PrototypeLab_background.png';

function PrototypeLab() {
  const [chatSessions, setChatSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);
  const [scrollY, setScrollY] = useState(0);
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  // 컴포넌트 마운트 시 채팅 세션 로드
  useEffect(() => {
    loadChatSessions();
  }, []);

  // 현재 세션이 변경될 때마다 메시지 로드
  useEffect(() => {
    if (currentSession) {
      loadMessages(currentSession.session_id);
    }
  }, [currentSession]);

  // 메시지가 추가될 때마다 자동 스크롤 (사용자가 스크롤을 조작하지 않았을 때만)
  useEffect(() => {
    if (shouldAutoScroll) {
      scrollToBottom();
    }
  }, [messages, shouldAutoScroll]);

  // 전체 스크롤 감지
  useEffect(() => {
    const handleWindowScroll = () => {
      setScrollY(window.scrollY);
      const nearBottom =
        window.innerHeight + window.scrollY >= document.body.scrollHeight - 50;
      setShouldAutoScroll(nearBottom);
    };
    window.addEventListener("scroll", handleWindowScroll);
    return () => window.removeEventListener("scroll", handleWindowScroll);
  }, []);

  // 채팅창 스크롤 감지
  useEffect(() => {
    const chatEl = chatContainerRef.current;
    if (!chatEl) return;

    const handleChatScroll = () => {
      const nearBottom =
        chatEl.scrollTop + chatEl.clientHeight >= chatEl.scrollHeight - 150;
      setShouldAutoScroll(nearBottom);
    };

    chatEl.addEventListener("scroll", handleChatScroll);
    return () => chatEl.removeEventListener("scroll", handleChatScroll);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // 채팅 세션 목록 로드
  const loadChatSessions = async () => {
    try {
      const response = await getChatSessions();
      setChatSessions(response.results || []);
      
      // 첫 번째 세션이 있으면 자동 선택
      if (response.results && response.results.length > 0) {
        setCurrentSession(response.results[0]);
      }
    } catch (error) {
      console.error('채팅 세션 로드 실패:', error);
    }
  };

  // 새 대화 시작
  const startNewConversation = async () => {
    try {
      const newSession = await createChatSession();
      // 기존 세션을 모두 제거하고 새 세션만 설정
      setChatSessions([newSession]);
      setCurrentSession(newSession);
      setMessages([]);
      // 새 대화 시작 시 자동 스크롤 활성화
      setShouldAutoScroll(true);
    } catch (error) {
      console.error('새 대화 시작 실패:', error);
    }
  };

  // 메시지 로드
  const loadMessages = async (sessionId) => {
    try {
      const response = await getPromptLogs(sessionId);
      const sessionMessages = (response.results || []).map(log => ({
        id: `user-${log.prompt_id}`,
        type: 'user',
        content: log.user_prompt,
        timestamp: log.created_at
      })).concat((response.results || []).map(log => ({
        id: `ai-${log.prompt_id}`,
        type: 'ai',
        content: log.ai_response,
        timestamp: log.created_at
      })));
      
      setMessages(sessionMessages);
    } catch (error) {
      console.error('메시지 로드 실패:', error);
    }
  };

  // 메시지 전송
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || !currentSession) return;

    const userMessage = {
      id: `user-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    // 사용자 메시지 즉시 추가
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    
    // 메시지 전송 후 자동 스크롤 활성화
    setShouldAutoScroll(true);

    try {
      // Django 서버로 메시지 전송
      const response = await sendChatMessage(currentSession.session_id, inputMessage);
      
      if (response.success) {
        // AI 응답 추가
        const aiMessage = {
          id: `ai-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          type: 'ai',
          content: response.response,
          timestamp: new Date().toISOString()
        };
        
        setMessages(prev => [...prev, aiMessage]);
        
        // 생성된 결과가 있으면 추가
        if (response.generatedResults) {
          response.generatedResults.forEach(result => {
            const resultMessage = {
              id: `result-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
              type: 'result',
              resultType: result.result_type,
              content: result.result,
              filePath: result.result_path,
              timestamp: new Date().toISOString()
            };
            setMessages(prev => [...prev, resultMessage]);
          });
        }
      }
    } catch (error) {
      console.error('메시지 전송 실패:', error);
      
      // 에러 메시지 표시
      const errorMessage = {
        id: `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        type: 'error',
        content: '메시지 전송에 실패했습니다. 다시 시도해주세요.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // 메시지 타입별 렌더링
  const renderMessage = (message) => {
    switch (message.type) {
      case 'user':
        return (
          <div key={message.id} className="flex justify-end mb-4">
            <div className="bg-blue-600 text-white rounded-lg px-4 py-2 max-w-xs lg:max-w-md">
              <p className="text-sm">{message.content}</p>
              <p className="text-xs text-blue-200 mt-1">
                {new Date(message.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>
        );
      
      case 'ai':
        return (
          <div key={message.id} className="flex justify-start mb-4">
            <div className="bg-gray-700 text-white rounded-lg px-4 py-2 max-w-xs lg:max-w-md">
              <p className="text-sm">{message.content}</p>
              <p className="text-xs text-gray-400 mt-1">
                {new Date(message.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>
        );
      
      case 'result':
        return (
          <div key={message.id} className="flex justify-start mb-4">
            <div className="bg-gray-700 text-white rounded-lg px-4 py-2 max-w-xs lg:max-w-md">
              <div className="flex items-center space-x-2 mb-2">
                <span className="text-lg">
                  {message.resultType === 'image' ? '🖼️' : 
                   message.resultType === '3d' ? '🎲' : 
                   message.resultType === '4d' ? '🎬' : '📄'}
                </span>
                <span className="text-sm font-medium">
                  {message.resultType === 'image' ? '생성된 이미지' :
                   message.resultType === '3d' ? '3D 모델' :
                   message.resultType === '4d' ? '4D 시뮬레이션' : '텍스트 결과'}
                </span>
              </div>
              
              {message.resultType === 'image' && (
                <div>
                  <img 
                    src={message.filePath || message.content} 
                    alt="Generated" 
                    className="w-full h-auto rounded-lg mb-2"
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.nextSibling.style.display = 'block';
                    }}
                  />
                  <div className="hidden bg-gray-600 rounded-lg p-8 text-gray-400 text-center">
                    <p className="text-sm mb-2">이미지 로드 실패</p>
                    <p className="text-xs">경로: {message.filePath || message.content}</p>
                  </div>
                </div>
              )}
              
                             {message.resultType === '3d' && (
                 <div className="text-center py-4">
                   <div className="text-4xl mb-2">🎲</div>
                   <p className="text-sm mb-2">3D 모델이 생성되었습니다</p>
                   
                   {/* 실제 비디오 플레이어 */}
                   <video 
                     className="w-full max-w-md mx-auto rounded-lg mb-3"
                     controls
                     preload="metadata"
                   >
                     <source src={message.filePath || "/src/assets/prototype_lab/Ionic6_3D.mp4"} type="video/mp4" />
                     브라우저가 비디오를 지원하지 않습니다.
                   </video>
                   
                   <div className="bg-gray-600 rounded-lg p-3 mb-2">
                     <p className="text-xs text-gray-300 mb-1">파일명: Ionic6_3D.mp4</p>
                     <p className="text-xs text-gray-300 mb-1">형식: MP4 (3D 모델)</p>
                     <p className="text-xs text-gray-300">상태: 재생 가능</p>
                   </div>
                   
                   <div className="flex justify-center">
                     <button 
                       onClick={() => {
                         const link = document.createElement('a');
                         link.href = message.filePath || '/src/assets/prototype_lab/Ionic6_3D.mp4';
                         link.download = 'Ionic6_3D.mp4';
                         link.click();
                       }}
                       className="px-3 py-1 bg-green-600 text-white rounded text-xs hover:bg-green-700 transition-colors"
                     >
                       다운로드
                     </button>
                   </div>
                 </div>
               )}
              
                             {message.resultType === '4d' && (
                 <div className="text-center py-4">
                   <div className="text-4xl mb-2">🎬</div>
                   <p className="text-sm mb-2">4D 시뮬레이션이 생성되었습니다</p>
                   
                   {/* 실제 비디오 플레이어 */}
                   <video 
                     className="w-full max-w-md mx-auto rounded-lg mb-3"
                     controls
                     preload="metadata"
                   >
                     <source src={message.filePath || "/src/assets/prototype_lab/Ionic6_4D.mp4"} type="video/mp4" />
                     브라우저가 비디오를 지원하지 않습니다.
                   </video>
                   
                   <div className="bg-gray-600 rounded-lg p-3 mb-2">
                     <p className="text-xs text-gray-300 mb-1">파일명: Ionic6_4D.mp4</p>
                     <p className="text-xs text-gray-300 mb-1">형식: MP4 (4D 시뮬레이션)</p>
                     <p className="text-xs text-gray-300">상태: 재생 가능</p>
                   </div>
                   
                   <div className="flex justify-center">
                     <button 
                       onClick={() => {
                         const link = document.createElement('a');
                         link.href = message.filePath || '/src/assets/prototype_lab/Ionic6_4D.mp4';
                         link.download = 'Ionic6_4D.mp4';
                         link.click();
                       }}
                       className="px-3 py-1 bg-green-600 text-white rounded text-xs hover:bg-green-700 transition-colors"
                     >
                       다운로드
                     </button>
                   </div>
                 </div>
               )}
              
              <p className="text-xs text-gray-400">
                {new Date(message.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>
        );
      
      case 'error':
        return (
          <div key={message.id} className="flex justify-center mb-4">
            <div className="bg-red-600 text-white rounded-lg px-4 py-2">
              <p className="text-sm">{message.content}</p>
            </div>
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-900" style={{
      backgroundImage: `url(${backgroundImage})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      backgroundRepeat: 'no-repeat',
      backgroundAttachment: 'fixed'
    }}>
      <Header />
      
      <div className="flex min-h-screen pt-16">
        {/* Left Sidebar - 대화 세션 이력 */}
        <div 
          className="fixed left-2 z-50 w-60"
          style={{
            top: `${Math.max(24, window.innerHeight / 2 - 350 - Math.min(scrollY * 0.4, 80) + Math.min(scrollY * 0.4, 80))}px`,
            transform: 'none',
            transition: 'top 0.1s ease-out'
          }}
        >
          <div className="bg-gray-900/90 backdrop-blur-md rounded-2xl border border-gray-700 shadow-2xl min-h-[70vh]">
            {/* Fixed Header */}
            <div className="p-6 border-b border-gray-700">
              <h3 className="text-xl font-bold text-white text-center">내 대화</h3>
              <button
                onClick={startNewConversation}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center space-x-2 mt-4"
              >
                <span className="text-lg">+</span>
                <span>새로운 대화</span>
              </button>
            </div>
            
            {/* Scrollable Content */}
            <div className="p-6 flex-1 min-h-[calc(70vh-120px)] overflow-y-auto">
              <div className="space-y-4">
                {chatSessions.map((session) => (
                  <div
                    key={session.session_id}
                    onClick={() => setCurrentSession(session)}
                    className={`p-3 rounded-lg cursor-pointer transition-colors ${
                      currentSession?.session_id === session.session_id
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-800/50 hover:bg-gray-800/70 text-gray-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm font-medium truncate">
                        {session.title || `대화 ${session.session_id.slice(-4)}`}
                      </p>
                    </div>
                    <p className="text-xs text-gray-400">
                      {new Date(session.started_at).toLocaleDateString()} {new Date(session.started_at).toLocaleTimeString()}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col relative min-h-screen">
          {/* Content Overlay */}
          <div className="relative z-10 flex-1 flex flex-col">
            {/* Hero Section */}
            <section className="relative py-24 lg:py-32">
              {/* Dark overlay for better text readability */}
              <div className="absolute inset-0 bg-black/30"></div>
              
              <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                <h1 className="text-6xl font-bold text-white mb-6">Prototype Lab</h1>
                <p className="text-gray-300 text-xl mb-8">
                  Turn your ideas into images — with just one prompt.
                </p>
                <div className="text-gray-400 space-y-2 mb-8">
                  <p>다양한 조건을 프롬프트로 입력하면, AI가 text-to-image 및 image-to-image 기술로 다채로운 시각적 프로토타입을 생성해줍니다.</p>
                </div>
              </div>
            </section>

            {/* Chat Container - 메시지와 입력창을 하나로 통합 */}
            <div className="flex-1 px-4 pb-4">
              <div className="max-w-4xl mx-auto h-full">
                <div className="bg-gray-800/90 backdrop-blur-sm rounded-lg overflow-hidden border border-gray-700/50" ref={chatContainerRef}>
                  {/* Chat Messages - 채팅 메시지 표시 영역 */}
                  <div className="flex-1 p-4 overflow-y-auto max-h-[60vh]">
                    {messages.length === 0 ? (
                      <div className="text-center text-gray-400 py-8">
                        <div className="text-4xl mb-4">💬</div>
                        <p className="text-lg mb-2">새로운 대화를 시작해보세요!</p>
                        <p className="text-sm">현대차 디자인과 관련된 질문을 해보세요.</p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {messages.map((message) => renderMessage(message))}
                        {isLoading && (
                          <div className="flex justify-start mb-4">
                            <div className="bg-gray-700 text-white rounded-lg px-4 py-2">
                              <div className="flex items-center space-x-2">
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                                <span className="text-sm">AI가 응답을 생성하고 있습니다...</span>
                              </div>
                            </div>
                          </div>
                        )}
                        <div ref={messagesEndRef} />
                      </div>
                    )}
                  </div>
                  
                  {/* Chat Input - 채팅창 내부에 통합 */}
                  <div className="border-t border-gray-700/50 p-4 bg-gray-700/80 backdrop-blur-sm">
                    <form onSubmit={handleSendMessage} className="flex space-x-4">
                      <input
                        type="text"
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        placeholder="무엇이든 물어보세요"
                        className="flex-1 bg-gray-600/90 backdrop-blur-sm border border-gray-500/50 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                        disabled={!currentSession || isLoading}
                      />
                      <button
                        type="submit"
                        disabled={!inputMessage.trim() || !currentSession || isLoading}
                        className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded-lg px-6 py-3 transition-colors disabled:cursor-not-allowed flex items-center space-x-2"
                      >
                        <span>전송</span>
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                        </svg>
                      </button>
                    </form>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PrototypeLab; 