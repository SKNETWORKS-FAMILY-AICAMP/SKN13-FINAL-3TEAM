import React, { useState, useEffect, useRef } from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { 
  getChatSessions, 
  createChatSession, 
  endChatSession, 
  getPromptLogs, 
  sendChatMessage 
} from '../services/chatService';

function Chatbot() {
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isCreatingSession, setIsCreatingSession] = useState(false);
  const messagesEndRef = useRef(null);

  // 세션 목록 로드
  useEffect(() => {
    loadSessions();
  }, []);

  // 현재 세션의 메시지 로드
  useEffect(() => {
    if (currentSession) {
      loadSessionMessages(currentSession.session_id);
    }
  }, [currentSession]);

  // 메시지 스크롤 자동 이동
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadSessions = async () => {
    try {
      const response = await getChatSessions();
      setSessions(response.results || []);
    } catch (error) {
      console.error('세션 로드 실패:', error);
    }
  };

  const loadSessionMessages = async (sessionId) => {
    try {
      const response = await getPromptLogs(sessionId);
      const sessionMessages = (response.results || []).map(log => ({
        id: log.prompt_id,
        type: 'user',
        content: log.user_prompt,
        timestamp: new Date(log.created_at).toLocaleString()
      })).concat((response.results || []).map(log => ({
        id: `ai-${log.prompt_id}`,
        type: 'bot',
        content: log.ai_response,
        timestamp: new Date(log.created_at).toLocaleString()
      })));

      setMessages(sessionMessages);
    } catch (error) {
      console.error('메시지 로드 실패:', error);
    }
  };

  const createNewSession = async () => {
    setIsCreatingSession(true);
    try {
      const newSession = await createChatSession();
      setSessions(prev => [newSession, ...prev]);
      setCurrentSession(newSession);
      setMessages([]);
    } catch (error) {
      console.error('새 세션 생성 실패:', error);
    } finally {
      setIsCreatingSession(false);
    }
  };

  const selectSession = async (session) => {
    setCurrentSession(session);
  };

  const endCurrentSession = async () => {
    if (!currentSession) return;

    try {
      await endChatSession(currentSession.session_id);
      setSessions(prev => 
        prev.map(s => 
          s.session_id === currentSession.session_id 
            ? { ...s, ended_at: new Date().toISOString() }
            : s
        )
      );
      setCurrentSession(null);
      setMessages([]);
    } catch (error) {
      console.error('세션 종료 실패:', error);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || !currentSession || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toLocaleString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await sendChatMessage(currentSession.session_id, inputMessage);
      
      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: response.response,
        timestamp: new Date().toLocaleString()
      };

      setMessages(prev => [...prev, botMessage]);
      
      // 세션 목록 새로고침
      await loadSessions();
    } catch (error) {
      console.error('메시지 전송 실패:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: '죄송합니다. 메시지 전송 중 오류가 발생했습니다.',
        timestamp: new Date().toLocaleString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const formatSessionTitle = (session) => {
    const startDate = new Date(session.started_at);
    return `세션 ${startDate.toLocaleDateString()} ${startDate.toLocaleTimeString()}`;
  };

  const isSessionActive = (session) => {
    return !session.ended_at;
  };

  return (
    <div className="min-h-screen" style={{backgroundColor: '#353745'}}>
      <Header />
      
      <div className="flex h-screen">
        {/* Left Sidebar */}
        <div className="w-80 bg-gray-800 border-r border-gray-700 p-6">
          <h2 className="text-white text-xl font-semibold mb-6">채팅 세션</h2>
          
          <button 
            onClick={createNewSession}
            disabled={isCreatingSession}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg mb-6 flex items-center justify-center space-x-2 hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span>+</span>
            <span>{isCreatingSession ? '생성 중...' : '새로운 채팅'}</span>
          </button>
          
          <div className="space-y-2">
            {sessions.map((session) => (
              <div 
                key={session.session_id}
                onClick={() => selectSession(session)}
                className={`rounded-lg p-3 cursor-pointer transition-colors ${
                  currentSession?.session_id === session.session_id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-white hover:bg-gray-600'
                }`}
              >
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium truncate">
                    {formatSessionTitle(session)}
                  </h3>
                  {isSessionActive(session) && (
                    <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                  )}
                </div>
                <p className="text-xs opacity-70 mt-1">
                  {new Date(session.started_at).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Chat Header */}
          <div className="bg-gray-800 border-b border-gray-700 p-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-white text-xl font-semibold">AI 디자인 어시스턴트</h1>
                <p className="text-gray-400 text-sm">
                  {currentSession 
                    ? `현재 세션: ${formatSessionTitle(currentSession)}`
                    : '자동차 디자인에 대한 모든 질문에 답변해드립니다'
                  }
                </p>
              </div>
              {currentSession && isSessionActive(currentSession) && (
                <button
                  onClick={endCurrentSession}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                >
                  세션 종료
                </button>
              )}
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 ? (
              <div className="text-center text-gray-400 mt-8">
                <p>새로운 세션을 시작하거나 기존 세션을 선택해주세요.</p>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                      message.type === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-700 text-white'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    <p className="text-xs opacity-70 mt-1">{message.timestamp}</p>
                  </div>
                </div>
              ))
            )}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-700 text-white px-4 py-2 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span className="text-sm">AI가 응답을 생성하고 있습니다...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="bg-gray-800 border-t border-gray-700 p-4">
            <form onSubmit={handleSendMessage} className="flex space-x-4">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder={currentSession ? "메시지를 입력하세요..." : "세션을 선택해주세요"}
                disabled={!currentSession || isLoading}
                className="flex-1 px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              />
              <button
                type="submit"
                disabled={!currentSession || isLoading || !inputMessage.trim()}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? '전송 중...' : '전송'}
              </button>
            </form>
          </div>
        </div>
      </div>
      
      <Footer />
    </div>
  );
}

export default Chatbot; 