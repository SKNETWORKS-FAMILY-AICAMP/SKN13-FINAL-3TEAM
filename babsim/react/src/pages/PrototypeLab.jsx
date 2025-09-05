import React, { useState, useEffect, useRef } from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { useAuth } from '../contexts/AuthContext';
import { 
  getChatSessions, 
  createChatSession, 
  getPromptLogs,
  sendChatMessage,
  generatePrototypeImage
} from '../services/chatService';
import backgroundImage from '../assets/PrototypeLab_background.png';

function PrototypeLab() {
  const [chatSessions, setChatSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { isAuthenticated } = useAuth();
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);
  const [scrollY, setScrollY] = useState(0);
  const [isChecklistExpanded, setIsChecklistExpanded] = useState(false);
  
  // State for checklist values
  const [checklistValues, setChecklistValues] = useState({});
  
  // State for the main image generation button
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationError, setGenerationError] = useState(null);

  const [selectedCategories, setSelectedCategories] = useState({
    viewpoint: false, bodyClassification: false, proportions: false, surfacing: false,
    fascia: false, lighting: false, wheels: false, glass: false, aero: false, color: false
  });
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  // Checklist change handler
  const handleChecklistChange = (category, item, value) => {
    setChecklistValues(prev => {
      const newCategory = { ...(prev[category] || {}) };
      if ((typeof value === 'boolean' && value) || (typeof value === 'string' && value.trim() !== '')) {
        newCategory[item] = value;
      } else {
        delete newCategory[item];
      }
      return { ...prev, [category]: newCategory };
    });
  };

  // Function to build the prompt from checklist values
  const buildPromptFromChecklist = () => {
    let promptParts = [];
    // This order can be adjusted to form more natural sentences
    const categoryOrder = ['color', 'bodyClassification', 'proportions', 'surfacing', 'lighting', 'wheels', 'fascia', 'glass', 'aero', 'viewpoint'];

    for (const category of categoryOrder) {
      if (checklistValues[category]) {
        const items = checklistValues[category];
        for (const item in items) {
          const value = items[item];
          if (typeof value === 'boolean' && value) {
            promptParts.push(item);
          } else if (typeof value === 'string') {
            promptParts.push(`${item} ${value}`);
          }
        }
      }
    }
    
    if (promptParts.length === 0) {
      return 'A modern, futuristic concept car.'; // Default prompt
    }

    return `A photorealistic image of a concept car, ${promptParts.join(', ')}.`;
  };

  // Main image generation handler
  const handleGenerateImage = async () => {
    setIsGenerating(true);
    setGenerationError(null);
    const prompt = buildPromptFromChecklist();
    
    // Add a user message indicating what was requested
    const requestMessage = {
      id: `user-request-${Date.now()}`,
      type: 'user',
      content: `"${prompt}"에 대한 이미지 생성을 요청했습니다.`,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, requestMessage]);

    try {
      const data = await generatePrototypeImage(prompt);
      if (data.s3_url) {
        const resultMessage = {
          id: `result-${Date.now()}`,
          type: 'result',
          resultType: 'image',
          content: data.s3_url,
          filePath: data.s3_url,
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, resultMessage]);
      } else {
        throw new Error(data.error || '이미지 URL을 받지 못했습니다.');
      }
    } catch (err) {
      setGenerationError(err.message);
      const errorMessage = {
        id: `error-${Date.now()}`,
        type: 'error',
        content: `이미지 생성 실패: ${err.message}`,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsGenerating(false);
    }
  };

  // --- Existing useEffect and other functions ---
  useEffect(() => {
    if (isAuthenticated) {
      loadChatSessions();
    } else {
      setChatSessions([]);
      setCurrentSession(null);
      setMessages([]);
    }
  }, [isAuthenticated]);

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
      const defaultTitle = new Date(newSession.started_at).toLocaleString('ko-KR');
      const sessionWithDefaultTitle = { ...newSession, title: defaultTitle };
      setChatSessions([sessionWithDefaultTitle]);
      setCurrentSession(sessionWithDefaultTitle);
      setMessages([]);
      setShouldAutoScroll(true);
    } catch (error) {
      console.error('새 대화 시작 실패:', error);
    }
  };

  const loadMessages = async (sessionId) => {
    try {
      const response = await getPromptLogs(sessionId);
      const rawLogs = response.results || [];
      const combinedMessages = [];
      rawLogs.forEach(log => {
        combinedMessages.push({ id: `user-${log.prompt_id}`, type: 'user', content: log.user_prompt, timestamp: log.created_at });
        combinedMessages.push({ id: `ai-${log.prompt_id}`, type: 'ai', content: log.ai_response, timestamp: log.created_at });
      });
      combinedMessages.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
      setMessages(combinedMessages);
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
    // ... (renderMessage implementation remains the same as before)
    switch (message.type) {
      case 'user':
        return (
          <div key={message.id} className="flex justify-end mb-6">
            <div className="bg-blue-600/90 backdrop-blur-md text-white rounded-2xl px-6 py-3 max-w-xs lg:max-w-md shadow-lg border border-blue-500/30">
              <p className="text-sm font-medium text-left">{message.content}</p>
              <p className="text-xs text-blue-200 mt-2 opacity-80">
                {new Date(message.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>
        );
      
      case 'ai':
        return (
          <div key={message.id} className="flex justify-start mb-6">
            <div className="bg-gray-800/90 backdrop-blur-md text-white rounded-2xl px-6 py-3 max-w-xs lg:max-w-md shadow-lg border border-gray-600/30">
              <p className="text-sm font-medium text-left">{message.content}</p>
              <p className="text-xs text-gray-300 mt-2 opacity-80">
                {new Date(message.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>
        );
      
      case 'result':
        return (
          <div key={message.id} className="flex justify-start mb-6">
            <div className="bg-gray-800/90 backdrop-blur-md text-white rounded-2xl px-6 py-4 max-w-xs lg:max-w-md shadow-lg border border-gray-600/30">
              <div className="flex items-center space-x-2 mb-3">
                <span className="text-lg">🖼️</span>
                <span className="text-sm font-medium">생성된 이미지</span>
              </div>
              <img src={message.filePath || message.content} alt="Generated" className="w-full h-auto rounded-xl mb-3 shadow-lg"/>
              <p className="text-xs text-gray-300 mt-3 opacity-80">
                {new Date(message.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>
        );
      
      case 'error':
        return (
          <div key={message.id} className="flex justify-start mb-6">
            <div className="bg-red-600/90 backdrop-blur-md text-white rounded-2xl px-6 py-3 shadow-lg border border-red-500/30">
              <p className="text-sm font-medium text-left">{message.content}</p>
            </div>
          </div>
        );
      
      default:
        return null;
    }
  };
  
  return (
    <div className="min-h-screen bg-gray-900" style={{ backgroundImage: `url(${backgroundImage})`, backgroundSize: 'cover', backgroundPosition: 'center', backgroundRepeat: 'no-repeat', backgroundAttachment: 'fixed' }}>
      <Header />
      <div className="flex min-h-screen pt-16">
        {/* Left Sidebar */}
        <div className="fixed left-2 z-50 w-60" style={{ top: `${Math.max(24, window.innerHeight / 2 - 350 - Math.min(scrollY * 0.4, 80) + Math.min(scrollY * 0.4, 80))}px`, transform: 'none', transition: 'top 0.1s ease-out' }}>
          <div className="bg-gray-900/90 backdrop-blur-md rounded-2xl border border-gray-700 shadow-2xl min-h-[80vh]">
            <div className="p-6 border-b border-gray-700">
              <h3 className="text-xl font-bold text-white text-center">내 대화</h3>
              <button onClick={startNewConversation} className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center space-x-2 mt-4">
                <span className="text-lg">+</span>
                <span>새로운 대화</span>
              </button>
            </div>
            <div className="p-6 flex-1 min-h-[calc(80vh-120px)] overflow-y-auto">
              <div className="space-y-4">
                {chatSessions.map((session) => (
                  <div key={session.session_id} onClick={() => setCurrentSession(session)} className={`p-3 rounded-lg cursor-pointer transition-colors ${currentSession?.session_id === session.session_id ? 'bg-blue-600 text-white' : 'bg-gray-800/50 hover:bg-gray-800/70 text-gray-300'}`}>
                    <p className="text-sm font-medium truncate">{session.title || `대화 ${session.session_id.slice(-4)}`}</p>
                    <p className="text-xs text-gray-400">{new Date(session.started_at).toLocaleDateString()} {new Date(session.started_at).toLocaleTimeString()}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col relative min-h-screen">
          <div className="relative z-10 flex-1 flex flex-col">
            <section className="relative py-16 lg:py-20">
              <div className="absolute inset-0 bg-black/50"></div>
              <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                <h1 className="text-6xl font-bold text-white mb-6 drop-shadow-2xl">Prototype Lab</h1>
                <p className="text-gray-300 text-xl mb-8 drop-shadow-lg">Turn your ideas into images — with just one prompt.</p>
              </div>
            </section>
            <div className="flex-1 px-8 pb-4 relative">
              <div className="relative z-10 h-full ml-60 mb-40">
                <div className={`space-y-6 px-4 h-[calc(100vh-200px)] overflow-y-auto pb-20`}>
                  {messages.map((message) => renderMessage(message))}
                  {isLoading && <div className="flex justify-start mb-4"><div className="bg-gray-700/90 backdrop-blur-sm text-white rounded-lg px-4 py-2 border border-gray-600/50"><div className="flex items-center space-x-2"><div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div><span className="text-sm">AI가 응답을 생성하고 있습니다...</span></div></div></div>}
                  <div ref={messagesEndRef} />
                </div>
              </div>
              <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2 w-full max-w-4xl px-8 z-20">
                <div className="bg-gray-800/90 backdrop-blur-md rounded-2xl border border-gray-700/50 shadow-2xl p-4">
                  <form onSubmit={handleSendMessage} className="flex space-x-4">
                    <input type="text" value={inputMessage} onChange={(e) => setInputMessage(e.target.value)} placeholder="무엇이든 물어보세요" className="flex-1 bg-gray-700/90 backdrop-blur-sm border border-gray-600/50 rounded-xl px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all" disabled={!currentSession || isLoading} />
                    <button type="submit" disabled={!inputMessage.trim() || !currentSession || isLoading} className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded-xl px-6 py-3 transition-all disabled:cursor-not-allowed flex items-center space-x-2 shadow-lg hover:shadow-xl"><span>전송</span><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg></button>
                  </form>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Sidebar - 체크리스트 */}
        <div className={`fixed right-2 z-50 transition-all duration-500 ease-in-out w-96 mt-5`} style={{ top: `${Math.max(24, window.innerHeight / 2 - 400 - Math.min(scrollY * 0.4, 80) + Math.min(scrollY * 0.4, 80))}px`, transform: 'none', transition: 'top 0.1s ease-out' }}>
          <div className="bg-gray-900/90 backdrop-blur-md rounded-2xl border border-gray-700 shadow-2xl h-[calc(100vh-120px)] flex flex-col">
            <div className="p-6 border-b border-gray-700 flex items-center justify-between">
              <h3 className="text-xl font-bold text-white">🚗 디자인 체크리스트</h3>
            </div>
            <div className="p-6 flex-1 overflow-y-auto">
              <div className="space-y-4">
                {/* Checklist Categories */}
                <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-600/30">
                  <h4 className="text-white font-medium">📐 뷰포인트</h4>
                  <div className="space-y-2 mt-3 pt-3 border-t border-gray-600/30">
                    {['Front view', '3/4 front view', 'Side view', 'Rear view'].map(item => (
                      <label key={item} className="flex items-center space-x-3 cursor-pointer">
                        <input type="checkbox" className="w-4 h-4" onChange={(e) => handleChecklistChange('viewpoint', item, e.target.checked)} />
                        <span className="text-sm text-gray-300">{item}</span>
                      </label>
                    ))}
                  </div>
                </div>
                <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-600/30">
                  <h4 className="text-white font-medium">🎨 색상 & 마감</h4>
                  <div className="space-y-3 mt-3 pt-3 border-t border-gray-600/30">
                    <div className="flex items-center justify-between">
                      <label className="text-sm text-gray-300">차체 색상:</label>
                      <input type="text" placeholder="metallic teal" className="w-48 bg-gray-700/80 rounded-lg px-3 py-2 text-sm" onChange={(e) => handleChecklistChange('color', 'Body Color', e.target.value)} />
                    </div>
                  </div>
                </div>
                {/* Add other categories here in the same pattern */}
              </div>
            </div>
            <div className="p-6 border-t border-gray-700">
              <button onClick={handleGenerateImage} disabled={isGenerating} className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-4 rounded-lg transition-colors disabled:bg-gray-500">
                {isGenerating ? '생성 중...' : '✨ 최종 이미지 생성'}
              </button>
              {generationError && <p className="text-red-500 text-xs mt-2 text-center">{generationError}</p>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PrototypeLab;
