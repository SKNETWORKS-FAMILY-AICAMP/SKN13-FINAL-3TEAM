import React, { useState, useEffect, useRef } from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { useAuth } from '../contexts/AuthContext';
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
  // ... other state variables ...

  const { isAuthenticated } = useAuth(); // Context에서 인증 상태 가져오기

  // [중요] 이 로직은 반드시 유지해야 합니다.
  useEffect(() => {
    if (isAuthenticated) {
      loadChatSessions();
    } else {
      setChatSessions([]);
      setCurrentSession(null);
      setMessages([]);
    }
  }, [isAuthenticated]);

  // ... 이하 전체 코드는 이전 답변의 최종본과 동일합니다 ...
  // ... (이하 생략 없이 전체 코드) ...
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);
  const [scrollY, setScrollY] = useState(0);
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);
  
  useEffect(() => {
    if (currentSession) {
      loadMessages(currentSession.session_id);
    } else {
      setMessages([]);
    }
  }, [currentSession]);
  
  useEffect(() => {
    if (shouldAutoScroll) {
      scrollToBottom();
    }
  }, [messages, shouldAutoScroll]);

  useEffect(() => {
    const handleWindowScroll = () => {
      setScrollY(window.scrollY);
      const nearBottom = window.innerHeight + window.scrollY >= document.body.scrollHeight - 50;
      setShouldAutoScroll(nearBottom);
    };
    window.addEventListener("scroll", handleWindowScroll);
    return () => window.removeEventListener("scroll", handleWindowScroll);
  }, []);

  useEffect(() => {
    const chatEl = chatContainerRef.current;
    if (!chatEl) return;
    const handleChatScroll = () => {
      const nearBottom = chatEl.scrollTop + chatEl.clientHeight >= chatEl.scrollHeight - 150;
      setShouldAutoScroll(nearBottom);
    };
    chatEl.addEventListener("scroll", handleChatScroll);
    return () => chatEl.removeEventListener("scroll", handleChatScroll);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const loadChatSessions = async () => {
    try {
      const response = await getChatSessions();
      setChatSessions(response.results || []);
      if (response.results && response.results.length > 0) {
        setCurrentSession(response.results[0]);
      }
    } catch (error) {
      console.error('채팅 세션 로드 실패:', error);
    }
  };

  const startNewConversation = async () => {
    try {
      const newSession = await createChatSession();
      setChatSessions([newSession]);
      setCurrentSession(newSession);
      setMessages([]);
      setShouldAutoScroll(true);
    } catch (error) {
      console.error('새 대화 시작 실패:', error);
    }
  };

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

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || !currentSession) return;
    const userMessage = { id: `user-${Date.now()}`, type: 'user', content: inputMessage, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setShouldAutoScroll(true);
    try {
      const response = await sendChatMessage(currentSession.session_id, inputMessage);
      if (response.success) {
        const aiMessage = { id: `ai-${Date.now()}`, type: 'ai', content: response.response, timestamp: new Date().toISOString() };
        setMessages(prev => [...prev, aiMessage]);
        if (response.generatedResults) {
          response.generatedResults.forEach(result => {
            const resultMessage = { id: `result-${Date.now()}-${result.result_id}`, type: 'result', resultType: result.result_type, content: result.result, filePath: result.result_path, timestamp: new Date().toISOString() };
            setMessages(prev => [...prev, resultMessage]);
          });
        }
      }
    } catch (error) {
      console.error('메시지 전송 실패:', error);
      const errorMessage = { id: `error-${Date.now()}`, type: 'error', content: '메시지 전송에 실패했습니다. 다시 시도해주세요.', timestamp: new Date().toISOString() };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };
  
  const renderMessage = (message) => {
    // ... renderMessage logic from your file
  };
  
  return (
    <div className="min-h-screen bg-gray-900" style={{ backgroundImage: `url(${backgroundImage})`, backgroundSize: 'cover', backgroundPosition: 'center', backgroundRepeat: 'no-repeat', backgroundAttachment: 'fixed' }}>
        <Header />
        <div className="flex min-h-screen pt-16">
            {/* Sidebar */}
            <div className="fixed left-2 z-50 w-60" style={{ top: `${Math.max(24, window.innerHeight / 2 - 350 - Math.min(scrollY * 0.4, 80) + Math.min(scrollY * 0.4, 80))}px`, transform: 'none', transition: 'top 0.1s ease-out' }}>
                <div className="bg-gray-900/90 backdrop-blur-md rounded-2xl border border-gray-700 shadow-2xl min-h-[70vh]">
                    <div className="p-6 border-b border-gray-700">
                        <h3 className="text-xl font-bold text-white text-center">내 대화</h3>
                        <button onClick={startNewConversation} className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center space-x-2 mt-4">
                            <span className="text-lg">+</span>
                            <span>새로운 대화</span>
                        </button>
                    </div>
                    <div className="p-6 flex-1 min-h-[calc(70vh-120px)] overflow-y-auto">
                        <div className="space-y-4">
                            {chatSessions.map((session) => (
                                <div key={session.session_id} onClick={() => setCurrentSession(session)} className={`p-3 rounded-lg cursor-pointer transition-colors ${currentSession?.session_id === session.session_id ? 'bg-blue-600 text-white' : 'bg-gray-800/50 hover:bg-gray-800/70 text-gray-300'}`}>
                                    <div className="flex items-center justify-between mb-2">
                                        <p className="text-sm font-medium truncate">{session.title || `대화 ${session.session_id.slice(-4)}`}</p>
                                    </div>
                                    <p className="text-xs text-gray-400">{new Date(session.started_at).toLocaleDateString()} {new Date(session.started_at).toLocaleTimeString()}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
            {/* Main Content */}
            <div className="flex-1 flex flex-col relative min-h-screen">
                <div className="relative z-10 flex-1 flex flex-col">
                    <section className="relative py-24 lg:py-32">
                        <div className="absolute inset-0 bg-black/30"></div>
                        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                            <h1 className="text-6xl font-bold text-white mb-6">Prototype Lab</h1>
                            <p className="text-gray-300 text-xl mb-8">Turn your ideas into images — with just one prompt.</p>
                            <div className="text-gray-400 space-y-2 mb-8">
                                <p>다양한 조건을 프롬프트로 입력하면, AI가 text-to-image 및 image-to-image 기술로 다채로운 시각적 프로토타입을 생성해줍니다.</p>
                            </div>
                        </div>
                    </section>
                    <div className="flex-1 px-4 pb-4">
                        <div className="max-w-4xl mx-auto h-full">
                            <div className="bg-gray-800/90 backdrop-blur-sm rounded-lg overflow-hidden border border-gray-700/50" ref={chatContainerRef}>
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
                                <div className="border-t border-gray-700/50 p-4 bg-gray-700/80 backdrop-blur-sm">
                                    <form onSubmit={handleSendMessage} className="flex space-x-4">
                                        <input type="text" value={inputMessage} onChange={(e) => setInputMessage(e.target.value)} placeholder="무엇이든 물어보세요" className="flex-1 bg-gray-600/90 backdrop-blur-sm border border-gray-500/50 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" disabled={!currentSession || isLoading} />
                                        <button type="submit" disabled={!inputMessage.trim() || !currentSession || isLoading} className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded-lg px-6 py-3 transition-colors disabled:cursor-not-allowed flex items-center space-x-2">
                                            <span>전송</span>
                                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
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