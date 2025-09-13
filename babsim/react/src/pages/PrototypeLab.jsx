import React, { useState, useEffect, useRef } from 'react';
import { flushSync } from 'react-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { useAuth } from '../contexts/AuthContext';
import { 
  getChatSessions, 
  createChatSession, 
  getPromptLogs,
  sendChatMessage,
  deleteChatSession
} from '../services/chatService';
import backgroundImage from '../assets/prototypelab.jpg';

function PrototypeLab() {
  const [chatSessions, setChatSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [forceRender, setForceRender] = useState(0);
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  // ... other state variables ...

  const { isAuthenticated, user } = useAuth(); // Context에서 인증 상태 가져오기

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

  // 페이지 로드 시 자동으로 새 대화 시작 (인증된 사용자만)
  useEffect(() => {
    if (isAuthenticated && chatSessions.length === 0) {
      startNewConversation();
    }
  }, [isAuthenticated, chatSessions.length]);

  // currentSession에 메시지가 없을 때 자동으로 파이프라인 호출
  useEffect(() => {
    if (isAuthenticated && currentSession && messages.length === 0) {
      // 빈 user_query로 파이프라인 호출 (WELCOME_TEXT 표시용)
      handleInitialPipelineCall();
    }
  }, [isAuthenticated, currentSession, messages.length]);

  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);
  const [scrollY, setScrollY] = useState(0);
  const [isChecklistExpanded, setIsChecklistExpanded] = useState(false);
  const [isChecklistHovered, setIsChecklistHovered] = useState(false);
  const [selectedCategories, setSelectedCategories] = useState({
    viewpoint: false,
    bodyClassification: false,
    proportions: false,
    surfacing: false,
    fascia: false,
    lighting: false,
    wheels: false,
    glass: false,
    aero: false,
    color: false
  });

  // 체크리스트 데이터 상태
  const [checklistData, setChecklistData] = useState({
    viewpoint: "",
    body_type: "",
    body_classification: "",
    proportions: "",
    surfacing: "",
    fascia: "",
    lighting: "",
    glasshouse: "",
    aero: "",
    color_finish: "",
    wheel: "",
  });
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

  // 이미지 업로드 핸들러
  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedImage(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  // 이미지 제거 핸들러
  const handleImageRemove = () => {
    setSelectedImage(null);
    setImagePreview(null);
  };

  // 체크리스트 데이터 업데이트 함수
  const updateChecklistData = (field, value) => {
    setChecklistData(prev => {
      const updated = {
        ...prev,
        [field]: value
      };
      // 완성도 실시간 업데이트를 위한 로그
      const completed = Object.values(updated).filter(v => v.trim() !== "").length;
      const total = Object.keys(updated).length;
      const percentage = Math.round((completed / total) * 100);
      console.log(`[체크리스트] ${field} 업데이트: "${value}" -> 완성도: ${percentage}% (${completed}/${total})`);
      return updated;
    });
  };

  // 체크리스트 완성도 계산
  const getChecklistCompletion = () => {
    const totalFields = Object.keys(checklistData).length;
    const completedFields = Object.values(checklistData).filter(value => value.trim() !== "").length;
    return {
      completed: completedFields,
      total: totalFields,
      percentage: Math.round((completedFields / totalFields) * 100)
    };
  };

  // 필수 항목만의 완료 상태 확인
  const getRequiredChecklistCompletion = () => {
    const requiredFields = ['viewpoint', 'body_type', 'color_finish'];
    const completedRequired = requiredFields.filter(field => 
      checklistData[field] && checklistData[field].trim() !== ""
    ).length;
    return {
      completed: completedRequired,
      total: requiredFields.length,
      percentage: Math.round((completedRequired / requiredFields.length) * 100)
    };
  };

  // 필수 체크리스트 필드 확인 (viewpoint, body_type, color_finish)
  const isChecklistComplete = (() => {
    const requiredFields = ['viewpoint', 'body_type', 'color_finish'];
    return requiredFields.every(field => 
      checklistData[field] && checklistData[field].trim() !== ""
    );
  })();

  // 체크리스트 전송 핸들러
  const handleChecklistSubmit = async () => {
    if (!isChecklistComplete) {
      console.log('❌ 필수 체크리스트 필드가 모두 채워지지 않았습니다.');
      return;
    }

    // 로딩 메시지 먼저 표시 (스코프 밖에서 선언)
    const loadingMessage = {
      id: `loading-${Date.now()}`,
      type: 'result',
      resultType: 'image',
      content: '',
      filePath: '',
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, loadingMessage]);

    try {
      console.log('🚀 체크리스트 기반 이미지 생성 시작:', checklistData);

      // API 호출
      const response = await fetch('/api/chat/checklist/generate-image/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          checklist_data: checklistData,
          session_id: currentSession?.session_id,
          user_id: isAuthenticated ? user?.user_id : 'anonymous_user'
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ 체크리스트 이미지 생성 응답:', data);

      // 로딩 메시지 제거
      setMessages(prev => prev.filter(msg => msg.id !== loadingMessage.id));

      // 생성된 이미지 결과 추가
      if (data.generated_results && data.generated_results.length > 0) {
        data.generated_results.forEach(result => {
          const resultMessage = {
            id: `result-${Date.now()}-${Math.random()}`,
            type: 'result',
            resultType: result.result_type,
            content: result.result || '',
            filePath: result.result_path || '',
            timestamp: new Date().toISOString()
          };
          setMessages(prev => [...prev, resultMessage]);
        });
      }

    } catch (error) {
      console.error('❌ 체크리스트 이미지 생성 실패:', error);
      
      // 로딩 메시지 제거
      setMessages(prev => prev.filter(msg => msg.id !== loadingMessage.id));
      
      // 에러 메시지 추가
      const errorMessage = {
        id: `error-${Date.now()}`,
        type: 'error',
        content: `이미지 생성 실패: ${error.message}`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
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
      console.log('🔄 새 대화 시작 중...');
      console.log('🔍 createChatSession 호출 전');
      const newSession = await createChatSession();
      console.log('🔍 createChatSession 호출 후:', newSession);
      console.log('✅ 새 세션 생성됨:', newSession);
      
      // 새 세션에 기본 제목 설정 (created_at 기반)
      const defaultTitle = new Date(newSession.started_at).toLocaleString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
      
      const sessionWithDefaultTitle = {
        ...newSession,
        title: defaultTitle
      };
      
      console.log('📝 세션 제목 설정됨:', sessionWithDefaultTitle);
            
      // 기존 세션들을 유지하고 새 세션을 맨 앞에 추가
      setChatSessions(prev => [sessionWithDefaultTitle, ...prev]);
      setCurrentSession(sessionWithDefaultTitle);
      setShouldAutoScroll(true);
      
      console.log('✅ 새 대화 시작 완료 - currentSession 설정됨:', sessionWithDefaultTitle);
    } catch (error) {
      console.error('새 대화 시작 실패:', error);
    }
  };


  const loadMessages = async (sessionId) => {
    try {
      const response = await getPromptLogs(sessionId);
      const rawLogs = response.results || [];

      // Combine user prompts and AI responses, then sort by timestamp
      const combinedMessages = [];
      rawLogs.forEach(log => {
        combinedMessages.push({
          id: `user-${log.prompt_id}`,
          type: 'user',
          content: log.user_prompt,
          timestamp: log.created_at
        });
        combinedMessages.push({
          id: `ai-${log.prompt_id}`,
          type: 'ai',
          content: log.ai_response,
          timestamp: log.created_at
        });
      });

      // Sort messages by timestamp to ensure correct order
      combinedMessages.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

      setMessages(combinedMessages);
    } catch (error) {
      console.error('메시지 로드 실패:', error);
    }
  };

  // 메시지 내용을 간단하게 요약하는 함수
  const generateTitleFromMessage = (message) => {
    // 메시지가 너무 길면 앞부분만 사용
    const maxLength = 20;
    if (message.length <= maxLength) {
      return message;
    }
    
    // 문장 단위로 자르기
    const sentences = message.split(/[.!?]/).filter(s => s.trim().length > 0);
    if (sentences.length > 0) {
      const firstSentence = sentences[0].trim();
      if (firstSentence.length <= maxLength) {
        return firstSentence;
      }
    }
    
    // 단어 단위로 자르기
    const words = message.split(' ').filter(w => w.trim().length > 0);
    let title = '';
    for (const word of words) {
      if ((title + ' ' + word).length <= maxLength) {
        title += (title ? ' ' : '') + word;
      } else {
        break;
      }
    }
    
    return title || message.substring(0, maxLength) + '...';
  };

  // 세션 제목 업데이트 함수
  const updateSessionTitle = async (sessionId, newTitle) => {
    try {
      // 로컬 상태 업데이트
      setChatSessions(prev => prev.map(session => 
        session.session_id === sessionId 
          ? { ...session, title: newTitle }
          : session
      ));
      
      // 현재 세션이라면 현재 세션도 업데이트
      if (currentSession?.session_id === sessionId) {
        setCurrentSession(prev => ({ ...prev, title: newTitle }));
      }
      
      // TODO: 백엔드 API 호출하여 제목 업데이트 (필요시 구현)
      // await updateChatSessionTitle(sessionId, newTitle);
    } catch (error) {
      console.error('세션 제목 업데이트 실패:', error);
    }
  };


  // 메시지 전송
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;
    
    // currentSession이 없으면 새 세션 생성
    if (!currentSession) {
      try {
        console.log('🔄 currentSession이 없어서 새 세션 생성 중...');
        await startNewConversation();
        console.log('✅ 새 세션 생성 완료, 메시지 전송 재시도');
        // 새 세션이 생성된 후 메시지 전송을 위해 재귀 호출
        setTimeout(() => {
          console.log('🔄 메시지 전송 재시도:', inputMessage);
          handleSendMessage(e);
        }, 200);
        return;
      } catch (error) {
        console.error('세션 생성 실패:', error);
        return;
      }
    }
    
    // currentSession.session_id가 undefined인 경우도 처리
    if (!currentSession.session_id) {
      console.error('❌ currentSession.session_id가 undefined입니다:', currentSession);
      try {
        await startNewConversation();
        setTimeout(() => handleSendMessage(e), 200);
        return;
      } catch (error) {
        console.error('세션 재생성 실패:', error);
        return;
      }
    }
    
    const userMessage = { 
      id: `user-${Date.now()}`, 
      type: 'user', 
      content: inputMessage, 
      timestamp: new Date().toISOString(),
      image: imagePreview
    };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setSelectedImage(null);
    setImagePreview(null);
    setShouldAutoScroll(true);

    // 첫 번째 메시지인 경우 제목 자동 생성
    if (messages.length === 0) {
      const generatedTitle = generateTitleFromMessage(inputMessage);
      await updateSessionTitle(currentSession.session_id, generatedTitle);
    }

    try {
      // 디버깅: 사용자 정보 확인
      console.log('🔍 사용자 정보 디버깅:');
      // console.log('  - user 객체:', user);
      console.log('  - user?.user_id:', user?.user_id); // user.id 는 없음
      // console.log('  - isAuthenticated:', isAuthenticated);
      
      // 체크리스트 데이터와 함께 메시지 전송
      const completionStatus = getChecklistCompletion();
      console.log('  - completionStatus:', completionStatus);
      // 스트리밍 방식으로 변경되어 기존 동기식 코드는 제거됨
      
      // 스트리밍 응답 처리 부분
      // user_id만 사용
      const userId = isAuthenticated ? user?.user_id : 'anonymous_user';
      
      console.log('🔍 API 호출 시작:', { sessionId: currentSession.session_id, message: inputMessage, userId });
      
      // 스트리밍 메시지 ID 생성
      const streamingMessageId = `ai-streaming-${Date.now()}`;
      
      // 실시간 스트리밍 업데이트 콜백
      const onStreamingUpdate = (partialResponse) => {
        // console.log('🔄 onStreamingUpdate 호출됨!');
        // console.log('🔄 partialResponse:', partialResponse);
        // console.log('🔄 partialResponse 타입:', typeof partialResponse);
        
        // console.log('🔄 스트리밍 청크 수신:', { // 이상없음. 계속 청크마다 누적하는 중.
        //   streamingMessageId,
        //   partialResponse: partialResponse.substring(0, 100) + (partialResponse.length > 100 ? '...' : ''),
        //   responseLength: partialResponse.length,
        //   timestamp: new Date().toISOString()
        // });
        
        flushSync(() => {
          // 여기서는 이미 존재하는 스트리밍 메시지 업데이트만
          setMessages(prev => prev.map(msg => 
              msg.id === streamingMessageId 
                ? { ...msg, content: partialResponse }
                : msg
            ));
        });
        
        // 강제 리렌더링 트리거
        setForceRender(prev => prev + 1);
      };
      
      // 스트리밍 시작 (await 제거!)
      sendChatMessage(currentSession.session_id, inputMessage, userId, onStreamingUpdate, setMessages, streamingMessageId, checklistData, completionStatus)
      .then(response => {
        console.log('✅ 스트리밍 완료 - 최종 응답:', {
          streamingMessageId,
          finalResponse: response.response?.substring(0, 100) + (response.response?.length > 100 ? '...' : ''),
          responseLength: response.response?.length,
          timestamp: new Date().toISOString()
        });

        if (response.isJson) {
          const jsonMessage = { id: `json-${Date.now()}`, type: 'ai', content: response.response, timestamp: new Date().toISOString(), isStreaming: false };
          setMessages(prev => [...prev, jsonMessage]);
        } else {// 스트리밍 완료 - isStreaming을 false로 변경
          setMessages(prev => prev.map(msg => 
            msg.id === streamingMessageId 
              ? { ...msg, isStreaming: false }
              : msg
          ));
        }            
        
        // 백엔드에서 받은 체크리스트 데이터로 프론트엔드 체크리스트 업데이트
        if (response.completionStatus && response.completionStatus.checklist_data) {
          const backendChecklistData = response.completionStatus.checklist_data;
          setChecklistData(prev => ({
            ...prev,
            ...backendChecklistData
          }));
        }
        
        // 생성된 결과들 처리
        if (response.generatedResults) {
          response.generatedResults.forEach(result => {
            const resultMessage = { 
              id: `result-${Date.now()}-${result.result_id || Math.random()}`, 
              type: 'result', 
              resultType: result.result_type, 
              content: result.result || '', 
              filePath: result.result_path || '', 
              timestamp: new Date().toISOString() 
            };
            setMessages(prev => [...prev, resultMessage]);
          });
        }
      })
      .catch(error => {
        console.error('❌ API 호출 실패:', error);
        const errorMessage = { id: `error-${Date.now()}`, type: 'error', content: `API 호출 실패: ${error.message || '알 수 없는 오류'}`, timestamp: new Date().toISOString() };
        setMessages(prev => [...prev, errorMessage]);
      });
    } catch (error) {
      console.error('메시지 전송 실패:', error);
      const errorMessage = { id: `error-${Date.now()}`, type: 'error', content: '메시지 전송에 실패했습니다. 다시 시도해주세요.', timestamp: new Date().toISOString() };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      // 스트리밍이 완료되면 로딩 상태 해제
      setIsLoading(false);
    }
  };
  
  const handleInitialPipelineCall = async () => {
    try {
      const userId = isAuthenticated ? user?.user_id : 'anonymous_user';
      
      // 빈 user_query로 파이프라인 호출
      const response = await sendChatMessage(
        currentSession.session_id, 
        "", // 빈 user_query
        userId, 
        null, 
        null, 
        null
      );
      
      // 응답을 message 객체로 변환하여 추가
      if (response && response.response) {
        const welcomeMessage = {
          id: `welcome-${Date.now()}`,
          type: 'ai',
          content: response.response,
          timestamp: new Date().toISOString()
        };
        
        setMessages(prev => [...prev, welcomeMessage]);
      }
    } catch (error) {
      console.error('초기 파이프라인 호출 실패:', error);
    }
  };

  // 세션 삭제 함수
  const handleDeleteSession = async (sessionId, e) => {
    e.stopPropagation(); // 부모 div의 onClick 이벤트 방지
    
    if (window.confirm('이 대화를 삭제하시겠습니까?')) {
      try {
        await deleteChatSession(sessionId);
        
        // 세션 목록에서 제거
        setChatSessions(prev => prev.filter(session => session.session_id !== sessionId));
        
        // 현재 선택된 세션이 삭제된 세션이면 초기화
        if (currentSession?.session_id === sessionId) {
          setCurrentSession(null);
          setMessages([]);
        }
        
        console.log('세션 삭제 완료:', sessionId);
      } catch (error) {
        console.error('세션 삭제 실패:', error);
        alert('세션 삭제에 실패했습니다.');
      }
    }
  };

  const renderMessage = (message) => {
    // console.log('🎨 renderMessage 실행:', {
    //   messageId: message.id,
    //   messageType: message.type,
    //   content: message.content,
    //   isStreaming: message.isStreaming, 
    //   timestamp: new Date().toISOString()
    // });
    
    // 메시지 타입이 없거나 'ai'가 아닌 경우 'ai'로 처리
    const messageType = message.type || 'ai';
    
    switch (messageType) {
      case 'user':
        // user_query가 비어있으면 렌더링하지 않음
        if (!message.content || message.content.trim() === '') {
          console.log('🔍 user_query가 비어있어서 렌더링하지 않음');
          return null;
        }
        
        return (
          <div key={message.id} className="flex justify-end mb-6">
            <div className="bg-gray-700/90 backdrop-blur-md text-white rounded-2xl px-6 py-3 max-w-xs lg:max-w-md shadow-lg border border-gray-600/30">
              {message.image && (
                <div className="mb-3">
                  <img 
                    src={message.image} 
                    alt="Uploaded" 
                    className="w-full h-auto rounded-lg shadow-md"
                  />
                </div>
              )}
              <p className="text-sm font-medium text-left">{message.content}</p>
                <p className="text-xs text-gray-300 mt-2 opacity-80">
                {new Date(message.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>
        );
      
      case 'ai':
        // Django 응답에서 오는 메시지 처리
        const content = message.content || message.response || message.reply || '';
        return (
          <div key={message.id} className="flex justify-start mb-6">
            <div className="bg-gray-800/90 backdrop-blur-md text-white rounded-2xl px-6 py-4 max-w-xs lg:max-w-2xl shadow-lg border border-gray-600/30">
              <div className="text-sm font-medium text-left whitespace-pre-line leading-relaxed">
                {content}
              </div>
              <p className="text-xs text-gray-300 mt-3 opacity-80">
                {new Date(message.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>
        );
      
      case 'result':
        // result_path가 빈 문자열인 경우 로딩박스 표시
        if (!message.filePath || message.filePath.trim() === '') {
          return (
            <div key={message.id} className="flex justify-start mb-6">
              <div className="bg-gray-800/90 backdrop-blur-md text-white rounded-2xl px-6 py-4 max-w-xs lg:max-w-md shadow-lg border border-gray-600/30">
                <div className="flex items-center space-x-2 mb-3">
                  <span className="text-lg">
                    {message.resultType === 'image' ? '🖼️' : 
                     message.resultType === '3d' ? '🎲' : 
                     message.resultType === '4d' ? '🎬' : '📄'}
                  </span>
                  <span className="text-sm font-medium">
                    {message.resultType === 'image' ? '이미지 생성 중' :
                     message.resultType === '3d' ? '3D 모델 생성 중' :
                     message.resultType === '4d' ? '4D 시뮬레이션 생성 중' : '처리 중'}
                  </span>
                </div>
                
                {/* 로딩 애니메이션 */}
                <div className="flex items-center justify-center py-8">
                  <div className="relative">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-2xl">
                        {message.resultType === 'image' ? '🖼️' : 
                         message.resultType === '3d' ? '🎲' : 
                         message.resultType === '4d' ? '🎬' : '📄'}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="text-center">
                  <p className="text-sm text-gray-300 mb-2">
                    {message.resultType === 'image' ? 'AI가 이미지를 생성하고 있습니다...' :
                     message.resultType === '3d' ? '3D 모델을 렌더링하고 있습니다...' :
                     message.resultType === '4d' ? '4D 시뮬레이션을 준비하고 있습니다...' : '처리 중입니다...'}
                  </p>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div className="bg-blue-500 h-2 rounded-full animate-pulse" style={{width: '60%'}}></div>
                  </div>
                </div>
              </div>
            </div>
          );
        }
        
        // result_path가 있는 경우 기존 렌더링
        return (
          <div key={message.id} className="flex justify-start mb-6">
            <div className="bg-gray-800/90 backdrop-blur-md text-white rounded-2xl px-6 py-4 max-w-xs lg:max-w-md shadow-lg border border-gray-600/30">
              <div className="flex items-center space-x-2 mb-3">
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
                    className="w-full h-auto rounded-xl mb-3 shadow-lg"
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
                  <div className="text-4xl mb-3">🎲</div>
                  <p className="text-sm mb-3 font-medium">3D 모델이 생성되었습니다</p>
                  
                  {/* 실제 비디오 플레이어 */}
                  <video 
                    className="w-full max-w-md mx-auto rounded-xl mb-4 shadow-lg"
                    controls
                    preload="metadata"
                  >
                    <source src={message.filePath || "/src/assets/prototype_lab/Ionic6_3D.mp4"} type="video/mp4" />
                    브라우저가 비디오를 지원하지 않습니다.
                  </video>
                  
                  <div className="bg-gray-700/80 backdrop-blur-sm rounded-xl p-4 mb-3 border border-gray-600/30">
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
                      className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-xl text-sm font-medium transition-all shadow-lg hover:shadow-xl"
                    >
                      다운로드
                    </button>
                  </div>
                </div>
              )}
              
              {message.resultType === '4d' && (
                <div className="text-center py-4">
                  <div className="text-4xl mb-3">🎬</div>
                  <p className="text-sm mb-3 font-medium">4D 시뮬레이션이 생성되었습니다</p>
                  
                  {/* 실제 비디오 플레이어 */}
                  <video 
                    className="w-full max-w-md mx-auto rounded-xl mb-4 shadow-lg"
                    controls
                    preload="metadata"
                  >
                    <source src={message.filePath || "/src/assets/prototype_lab/Ionic6_4D.mp4"} type="video/mp4" />
                    브라우저가 비디오를 지원하지 않습니다.
                  </video>
                  
                  <div className="bg-gray-700/80 backdrop-blur-sm rounded-xl p-4 mb-3 border border-gray-600/30">
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
                      className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-xl text-sm font-medium transition-all shadow-lg hover:shadow-xl"
                    >
                      다운로드
                    </button>
                  </div>
                </div>
              )}
              
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
      
      case 'completion':
        return (
          <div key={message.id} className="flex justify-center mb-6">
            <div className="bg-green-600/90 backdrop-blur-md text-white rounded-2xl px-6 py-3 shadow-lg border border-green-500/30">
              <p className="text-sm font-medium text-center">{message.content}</p>
            </div>
          </div>
        );
      
      default:
        // 알 수 없는 메시지 타입은 'ai'로 처리
        console.log('⚠️ 알 수 없는 메시지 타입:', messageType, '-> ai로 처리');
        const defaultContent = message.content || message.response || message.reply || '';
        return (
          <div key={message.id} className="flex justify-start mb-6">
            <div className="bg-gray-800/90 backdrop-blur-md text-white rounded-2xl px-6 py-4 max-w-xs lg:max-w-2xl shadow-lg border border-gray-600/30">
              <div className="text-sm font-medium text-left whitespace-pre-line leading-relaxed">
                {defaultContent}
              </div>
              <p className="text-xs text-gray-300 mt-3 opacity-80">
                {new Date(message.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>
        );
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
        <div className="fixed left-4 top-20 bottom-4 w-64 z-30">
          <div className="bg-gray-800/70 backdrop-blur-md rounded-2xl border border-gray-600/50 shadow-2xl h-full">
            {/* Fixed Header */}
            <div className="p-6 border-b border-gray-700">
              <h3 className="text-xl font-bold text-white text-center">내 대화</h3>
              <button
                onClick={() => {
                  console.log('🖱️ 새 대화 버튼 클릭됨!');
                  startNewConversation();
                }}
                className="w-full bg-white hover:bg-gray-100 text-black font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center space-x-2 mt-4"
              >
                <span className="text-lg">+</span>
                <span>새로운 대화</span>
              </button>
            </div>
            
            {/* Scrollable Content */}
            <div className="p-6 flex-1 overflow-y-auto">
              <div className="space-y-4">
                {chatSessions.map((session) => (
                  <div
                    key={session.session_id}
                    onClick={() => setCurrentSession(session)}
                    className={`p-3 rounded-lg cursor-pointer transition-colors group relative ${
                      currentSession?.session_id === session.session_id
                        ? 'bg-gray-700 text-white'
                        : 'bg-gray-800/50 hover:bg-gray-800/70 text-gray-300'
                    }`}
                  >
                    {/* 삭제 버튼 */}
                    <button
                      onClick={(e) => handleDeleteSession(session.session_id, e)}
                      className="absolute top-2 right-2 w-5 h-5 rounded-full bg-red-500/80 hover:bg-red-600 text-white text-xs flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-10"
                      title="대화 삭제"
                    >
                      ×
                    </button>
                    
                    <div className="flex items-center justify-between mb-2 pr-6">
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
        <div className="flex-1 flex flex-col relative min-h-screen ml-72">
          {/* Content Overlay */}
          <div className="relative z-10 flex-1 flex flex-col">
            {/* Hero Section */}
            <section className="relative py-16 lg:py-20">
              {/* Dark overlay for better text readability */}
              <div className="absolute inset-0 bg-black/50"></div>
              
              <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                <h1 className="text-6xl font-bold text-white mb-6 drop-shadow-2xl">Prototype Lab</h1>
                <p className="text-gray-300 text-xl mb-8 drop-shadow-lg">
                  Turn your ideas into images — with just one prompt.
                </p>
                <div className="text-gray-300 space-y-2 mb-8 drop-shadow-md">
                  <p>다양한 조건을 프롬프트로 입력하면, AI가 text-to-image 및 image-to-image 기술로 다채로운 시각적 프로토타입을 생성해줍니다.</p>
                </div>
              </div>
            </section>

            {/* Chat Container - 메시지와 입력창을 하나로 통합 */}
            <div className="flex-1 px-8 pb-4 relative">
              {/* Chat Messages - 백그라운드 위에 직접 배치 */}
              <div className="relative z-10 h-full mb-40">
                <div className="space-y-6 px-4 h-[calc(100vh-200px)] overflow-y-auto pb-20">
                  {messages.map((message, index) => renderMessage(message, index))}
                  
                  {isLoading && !messages.some(msg => msg.isStreaming) && (
                    <div className="flex justify-start mb-4">
                      <div className="bg-gray-700/90 backdrop-blur-sm text-white rounded-lg px-4 py-2 border border-gray-600/50">
                        <div className="flex items-center space-x-2">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          <span className="text-sm">AI가 응답을 생성하고 있습니다...</span>
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              </div>
              
              {/* Chat Input - 하단에 고정된 입력창 */}
              <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2 w-full max-w-4xl px-8 z-20">
                <div className="bg-gray-800/90 backdrop-blur-md rounded-3xl border border-gray-700/50 shadow-2xl p-4">
                  {/* 이미지 미리보기 */}
                  {imagePreview && (
                    <div className="mb-4 relative">
                      <img 
                        src={imagePreview} 
                        alt="Preview" 
                        className="w-32 h-32 object-cover rounded-2xl shadow-lg"
                      />
                      <button
                        onClick={handleImageRemove}
                        className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 hover:bg-red-600 text-white rounded-full flex items-center justify-center text-sm"
                      >
                        ×
                      </button>
                    </div>
                  )}
                  
                  <form onSubmit={handleSendMessage} className="flex space-x-4">
                    {/* 이미지 업로드 버튼 */}
                      <label className="bg-white/90 hover:bg-gray-100/90 text-black rounded-2xl px-4 py-3 transition-all cursor-pointer flex items-center space-x-2 shadow-lg hover:shadow-xl">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      <span className="text-sm">이미지</span>
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleImageUpload}
                        className="hidden"
                        disabled={!currentSession || isLoading}
                      />
                    </label>
                    
                    <input
                      id="chat-input"
                      name="chatMessage"
                      type="text"
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      placeholder="무엇이든 물어보세요"
                      className="flex-1 bg-gray-700/90 backdrop-blur-sm border border-gray-600/50 rounded-2xl px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                      disabled={!currentSession || isLoading}
                    />
                    <button
                      type="submit"
                      disabled={(!inputMessage.trim() && !selectedImage) || !currentSession || isLoading}
                      onClick={(e) => {
                        console.log('🔍 버튼 클릭됨!');
                        handleSendMessage(e);
                      }}
                      className="bg-white hover:bg-gray-100 disabled:bg-gray-300 text-black rounded-2xl px-6 py-3 transition-all disabled:cursor-not-allowed flex items-center space-x-2 shadow-lg hover:shadow-xl"
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

        {/* Floating Design Checklist - 오른쪽 아래 */}
        <div 
          className={`fixed right-4 bottom-4 z-40 transition-all duration-500 ease-in-out ${
            isChecklistExpanded 
              ? 'w-[calc(100vw-8rem)] h-[calc(100vh-8rem)]' 
              : isChecklistHovered 
                ? 'w-[calc(100vw-8rem)] h-[calc(100vh-8rem)]' 
                : 'w-auto h-auto'
          }`}
          onMouseEnter={() => setIsChecklistHovered(true)}
          onMouseLeave={() => setIsChecklistHovered(false)}
        >
          <div className={`bg-gray-800/70 backdrop-blur-md rounded-2xl border border-gray-600/50 shadow-2xl transition-all duration-500 ${
            isChecklistExpanded || isChecklistHovered ? 'h-full' : 'h-auto'
          }`}>
            {/* Collapsed State */}
            {!isChecklistExpanded && !isChecklistHovered && (
              <div className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="text-lg">🚗</span>
                    <div>
                      <h3 className="text-white font-bold text-sm">디자인 체크리스트</h3>
                      <p className="text-gray-400 text-xs">자동차 프로토타입 생성 가이드</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="text-right">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-gray-400">완성도</span>
                        <span className="text-xs text-gray-300">{getChecklistCompletion().percentage}%</span>
                      </div>
                      <div className="w-20 bg-gray-700 rounded-full h-1.5">
                        <div 
                          className="bg-gray-500 h-1.5 rounded-full transition-all duration-300"
                          style={{ width: `${getChecklistCompletion().percentage}%` }}
                        ></div>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {getChecklistCompletion().completed}/{getChecklistCompletion().total} 항목 완료
                      </p>
                    </div>
                    <button
                      onClick={() => {
                        setIsChecklistExpanded(true);
                        // 확장 시 모든 카테고리를 펼치기
                        setSelectedCategories({
                          viewpoint: true,
                          bodyClassification: true,
                          proportions: true,
                          surfacing: true,
                          fascia: true,
                          lighting: true,
                          wheels: true,
                          glass: true,
                          aero: true,
                          color: true
                        });
                      }}
                      className="bg-white hover:bg-gray-100 text-black p-2 rounded-lg transition-all duration-200"
                      title="확장하기"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Expanded State */}
            {(isChecklistExpanded || isChecklistHovered) && (
              <div className="p-6 border-b border-gray-700 flex items-center justify-between">
                <div className="text-left">
                  <h3 className="text-xl font-bold text-white">🚗 디자인 체크리스트</h3>
                  <p className="text-gray-400 text-sm mt-2">자동차 프로토타입 생성 가이드</p>
                  {/* 체크리스트 완성도 표시 */}
                  <div className="mt-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-gray-400">완성도</span>
                      <span className="text-xs text-gray-300">{getChecklistCompletion().percentage}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-gray-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${getChecklistCompletion().percentage}%` }}
                      ></div>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {getChecklistCompletion().completed}/{getChecklistCompletion().total} 항목 완료
                    </p>
                  </div>
                </div>
                {isChecklistExpanded && (
                  <button
                    onClick={() => {
                      setIsChecklistExpanded(false);
                      // 축소 시 모든 카테고리를 접기
                      setSelectedCategories({
                        viewpoint: false,
                        bodyClassification: false,
                        proportions: false,
                        surfacing: false,
                        fascia: false,
                        lighting: false,
                        wheels: false,
                        glass: false,
                        aero: false,
                        color: false
                      });
                    }}
                    className="bg-red-600 hover:bg-red-700 text-white p-2 rounded-lg transition-all duration-200"
                    title="축소하기"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>
            )}
            
            {/* Content - 계층적 체크리스트 */}
            {(isChecklistExpanded || isChecklistHovered) && (
              <div className="p-6 flex-1 overflow-y-auto">
                <div className="space-y-4 grid grid-cols-3 gap-4">
                {/* 뷰포인트 - 대분류만 표시 */}
                <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-600/30">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-white font-medium text-left flex-1">📐 뷰포인트 (Viewpoint)</h4>
                    <button
                      onClick={() => setSelectedCategories(prev => ({...prev, viewpoint: !prev.viewpoint}))}
                      className="text-blue-400 hover:text-blue-300 text-sm whitespace-nowrap px-2 py-1 rounded hover:bg-blue-500/20 transition-colors ml-2"
                    >
                      {selectedCategories.viewpoint ? "접기" : "펼치기"}
                    </button>
                  </div>
                  
                  {selectedCategories.viewpoint && (
                    <div className="space-y-2 mt-3 pt-3 border-t border-gray-600/30">
                      <label className="flex items-center space-x-3 cursor-pointer">
                        <input 
                          type="checkbox" 
                          checked={checklistData.viewpoint === "front view"}
                          onChange={(e) => updateChecklistData('viewpoint', e.target.checked ? "front view" : "")}
                          className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500 focus:ring-2" 
                        />
                        <span className="text-sm text-gray-300">Front view</span>
                      </label>
                      <label className="flex items-center space-x-3 cursor-pointer">
                        <input 
                          type="checkbox" 
                          checked={checklistData.viewpoint === "3/4 view"}
                          onChange={(e) => updateChecklistData('viewpoint', e.target.checked ? "3/4 view" : "")}
                          className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500 focus:ring-2" 
                        />
                        <span className="text-sm text-gray-300">3/4 front view</span>
                      </label>
                      <label className="flex items-center space-x-3 cursor-pointer">
                        <input 
                          type="checkbox" 
                          checked={checklistData.viewpoint === "side view"}
                          onChange={(e) => updateChecklistData('viewpoint', e.target.checked ? "side view" : "")}
                          className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500 focus:ring-2" 
                        />
                        <span className="text-sm text-gray-300">Side view</span>
                      </label>
                      <label className="flex items-center space-x-3 cursor-pointer">
                        <input 
                          type="checkbox" 
                          checked={checklistData.viewpoint === "rear view"}
                          onChange={(e) => updateChecklistData('viewpoint', e.target.checked ? "rear view" : "")}
                          className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500 focus:ring-2" 
                        />
                        <span className="text-sm text-gray-300">Rear view</span>
                      </label>
                    </div>
                  )}
                </div>

                {/* 차체 분류 - 대분류만 표시 */}
                <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-600/30">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-white font-medium text-left flex-1">🏗️ 차체 분류 (Body Classification)</h4>
                    <button
                      onClick={() => setSelectedCategories(prev => ({...prev, bodyClassification: !prev.bodyClassification}))}
                      className="text-blue-400 hover:text-blue-300 text-sm whitespace-nowrap px-2 py-1 rounded hover:bg-blue-500/20 transition-colors ml-2"
                    >
                      {selectedCategories.bodyClassification ? "접기" : "펼치기"}
                    </button>
                  </div>
                  
                  {selectedCategories.bodyClassification && (
                    <div className="space-y-3 mt-3 pt-3 border-t border-gray-600/30">
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">크기 등급:</label>
                        <input 
                          type="text" 
                          placeholder="소형/준중형/중형/대형" 
                          value={checklistData.body_classification}
                          onChange={(e) => updateChecklistData('body_classification', e.target.value)}
                          className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" 
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">차체 유형:</label>
                        <input 
                          type="text" 
                          placeholder="SUV/세단/쿠페/해치백" 
                          value={checklistData.body_type}
                          onChange={(e) => updateChecklistData('body_type', e.target.value)}
                          className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" 
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">형태:</label>
                        <input 
                          type="text" 
                          placeholder="two-box/three-box" 
                          value={checklistData.proportions}
                          onChange={(e) => updateChecklistData('proportions', e.target.value)}
                          className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" 
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* 비율 & 자세 - 대분류만 표시 */}
                <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-600/30">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-white font-medium text-left flex-1">⚖️ 비율 & 자세 (Proportions & Stance)</h4>
                    <button
                      onClick={() => setSelectedCategories(prev => ({...prev, proportions: !prev.proportions}))}
                      className="text-blue-400 hover:text-blue-300 text-sm whitespace-nowrap px-2 py-1 rounded hover:bg-blue-500/20 transition-colors ml-2"
                    >
                      {selectedCategories.proportions ? "접기" : "펼치기"}
                    </button>
                  </div>
                  
                  {selectedCategories.proportions && (
                    <div className="space-y-3 mt-3 pt-3 border-t border-gray-600/30">
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">휠베이스:</label>
                        <input type="text" placeholder="short/long" className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" />
                      </div>
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">트랙:</label>
                        <input type="text" placeholder="narrow/wide" className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" />
                      </div>
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">오버행:</label>
                        <input type="text" placeholder="front short, rear long" className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" />
                      </div>
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">자세:</label>
                        <input type="text" placeholder="upright/low/aggressive" className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" />
                      </div>
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">대시-투-액슬:</label>
                        <input type="text" placeholder="short/long" className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" />
                      </div>
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">벨트라인:</label>
                        <input type="text" placeholder="low/high" className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" />
                      </div>
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">그린하우스:</label>
                        <input type="text" placeholder="large/small" className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" />
                      </div>
                    </div>
                  )}
                </div>

                {/* 차체 표면 - 대분류만 표시 */}
                <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-600/30">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-white font-medium text-left flex-1">🎨 차체 표면 (Body Surfacing)</h4>
                    <button
                      onClick={() => setSelectedCategories(prev => ({...prev, surfacing: !prev.surfacing}))}
                      className="text-blue-400 hover:text-blue-300 text-sm whitespace-nowrap px-2 py-1 rounded hover:bg-blue-500/20 transition-colors ml-2"
                    >
                      {selectedCategories.surfacing ? "접기" : "펼치기"}
                    </button>
                  </div>
                  
                  {selectedCategories.surfacing && (
                    <div className="space-y-2 mt-3 pt-3 border-t border-gray-600/30">
                      <label className="flex items-center space-x-3 cursor-pointer">
                        <input type="checkbox" className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500 focus:ring-2" />
                        <span className="text-sm text-gray-300">Clean</span>
                      </label>
                      <label className="flex items-center space-x-3 cursor-pointer">
                        <input type="checkbox" className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500 focus:ring-2" />
                        <span className="text-sm text-gray-300">Taut</span>
                      </label>
                      <label className="flex items-center space-x-3 cursor-pointer">
                        <input type="checkbox" className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500 focus:ring-2" />
                        <span className="text-sm text-gray-300">Soft</span>
                      </label>
                      <label className="flex items-center space-x-3 cursor-pointer">
                        <input type="checkbox" className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500 focus:ring-2" />
                        <span className="text-sm text-gray-300">Chamfers</span>
                      </label>
                      <label className="flex items-center space-x-3 cursor-pointer">
                        <input type="checkbox" className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500 focus:ring-2" />
                        <span className="text-sm text-gray-300">Bulges</span>
                      </label>
                      <label className="flex items-center space-x-3 cursor-pointer">
                        <input type="checkbox" className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500 focus:ring-2" />
                        <span className="text-sm text-gray-300">Strong shoulder line</span>
                      </label>
                    </div>
                  )}
                </div>

                {/* 전면부 & 측면부 요소 - 대분류만 표시 */}
                <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-600/30">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-white font-medium text-left flex-1">🔧 전면부 & 측면부 요소 (Fascia & Profile)</h4>
                    <button
                      onClick={() => setSelectedCategories(prev => ({...prev, fascia: !prev.fascia}))}
                      className="text-blue-400 hover:text-blue-300 text-sm whitespace-nowrap px-2 py-1 rounded hover:bg-blue-500/20 transition-colors ml-2"
                    >
                      {selectedCategories.fascia ? "접기" : "펼치기"}
                    </button>
                  </div>
                  
                  {selectedCategories.fascia && (
                    <div className="space-y-3 mt-3 pt-3 border-t border-gray-600/30">
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">그릴:</label>
                        <input type="text" placeholder="parametric/mesh/slats" className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" />
                      </div>
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">흡기구:</label>
                        <input type="text" placeholder="large/small" className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" />
                      </div>
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">범퍼:</label>
                        <input type="text" placeholder="sporty/rugged" className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" />
                      </div>
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">후드:</label>
                        <input type="text" placeholder="clamshell/sculpted" className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" />
                      </div>
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">도어 핸들:</label>
                        <input type="text" placeholder="flush/pull type" className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" />
                      </div>
                    </div>
                  )}
                </div>

                {/* 조명 - 대분류만 표시 */}
                <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-600/30">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-white font-medium text-left flex-1">💡 조명 (Lighting)</h4>
                    <button
                      onClick={() => setSelectedCategories(prev => ({...prev, lighting: !prev.lighting}))}
                      className="text-blue-400 hover:text-blue-300 text-sm whitespace-nowrap px-2 py-1 rounded hover:bg-blue-500/20 transition-colors ml-2"
                    >
                      {selectedCategories.lighting ? "접기" : "펼치기"}
                    </button>
                  </div>
                  
                  {selectedCategories.lighting && (
                    <div className="space-y-3 mt-3 pt-3 border-t border-gray-600/30">
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">DRL:</label>
                        <input type="text" placeholder="pixel DRL/strip DRL" className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" />
                      </div>
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">헤드램프:</label>
                        <input type="text" placeholder="LED/matrix/projector" className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" />
                      </div>
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">테일램프:</label>
                        <input type="text" placeholder="full-width/vertical/horizontal" className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" />
                      </div>
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">형상:</label>
                        <input type="text" placeholder="slim/parametric/pixelated" className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" />
                      </div>
                    </div>
                  )}
                </div>

                {/* 휠 & 타이어 - 대분류만 표시 */}
                <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-600/30">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-white font-medium text-left flex-1">🛞 휠 & 타이어 (Wheels & Tires)</h4>
                    <button
                      onClick={() => setSelectedCategories(prev => ({...prev, wheels: !prev.wheels}))}
                      className="text-blue-400 hover:text-blue-300 text-sm whitespace-nowrap px-2 py-1 rounded hover:bg-blue-500/20 transition-colors ml-2"
                    >
                      {selectedCategories.wheels ? "접기" : "펼치기"}
                    </button>
                  </div>
                  
                  {selectedCategories.wheels && (
                    <div className="space-y-3 mt-3 pt-3 border-t border-gray-600/30">
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">휠 크기:</label>
                        <input type="text" placeholder="20-inch" className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" />
                      </div>
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">스포크 타입:</label>
                        <input type="text" placeholder="multi-spoke/Y-spoke/turbine" className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" />
                      </div>
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">마감:</label>
                        <input type="text" placeholder="chrome/gloss black/satin" className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" />
                      </div>
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">타이어:</label>
                        <input type="text" placeholder="low-profile/thick" className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" />
                      </div>
                    </div>
                  )}
                </div>

                {/* 유리 & 그린하우스 - 대분류만 표시 */}
                <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-600/30">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-white font-medium text-left flex-1">🪟 유리 & 그린하우스 (Glass/Greenhouse)</h4>
                    <button
                      onClick={() => setSelectedCategories(prev => ({...prev, glass: !prev.glass}))}
                      className="text-blue-400 hover:text-blue-300 text-sm whitespace-nowrap px-2 py-1 rounded hover:bg-blue-500/20 transition-colors ml-2"
                    >
                      {selectedCategories.glass ? "접기" : "펼치기"}
                    </button>
                  </div>
                  
                  {selectedCategories.glass && (
                    <div className="space-y-3 mt-3 pt-3 border-t border-gray-600/30">
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">윈도 라인:</label>
                        <input type="text" placeholder="자유 입력" className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" />
                      </div>
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">윈도 트림:</label>
                        <input type="text" placeholder="chrome/black" className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" />
                      </div>
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">사이드 미러:</label>
                        <input type="text" placeholder="body-color/gloss black" className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" />
                      </div>
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">필러 처리:</label>
                        <input type="text" placeholder="자유 입력" className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" />
                      </div>
                    </div>
                  )}
                </div>

                {/* 공기역학 & 추가 요소 - 대분류만 표시 */}
                <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-600/30">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-white font-medium text-left flex-1">🚀 공기역학 & 추가 요소 (Aero/Add-ons)</h4>
                    <button
                      onClick={() => setSelectedCategories(prev => ({...prev, aero: !prev.aero}))}
                      className="text-blue-400 hover:text-blue-300 text-sm whitespace-nowrap px-2 py-1 rounded hover:bg-blue-500/20 transition-colors ml-2"
                    >
                      {selectedCategories.aero ? "접기" : "펼치기"}
                    </button>
                  </div>
                  
                  {selectedCategories.aero && (
                    <div className="space-y-2 mt-3 pt-3 border-t border-gray-600/30">
                      <label className="flex items-center space-x-3 cursor-pointer">
                        <input type="checkbox" className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500 focus:ring-2" />
                        <span className="text-sm text-gray-300">Splitter</span>
                      </label>
                      <label className="flex items-center space-x-3 cursor-pointer">
                        <input type="checkbox" className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500 focus:ring-2" />
                        <span className="text-sm text-gray-300">Vents</span>
                      </label>
                      <label className="flex items-center space-x-3 cursor-pointer">
                        <input type="checkbox" className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500 focus:ring-2" />
                        <span className="text-sm text-gray-300">Roof rails</span>
                      </label>
                      <label className="flex items-center space-x-3 cursor-pointer">
                        <input type="checkbox" className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500 focus:ring-2" />
                        <span className="text-sm text-gray-300">Roof spoiler</span>
                      </label>
                    </div>
                  )}
                </div>

                {/* 색상 & 마감 - 대분류만 표시 */}
                <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-600/30">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-white font-medium text-left flex-1">🎨 색상 & 마감 (Color & Finish)</h4>
                    <button
                      onClick={() => setSelectedCategories(prev => ({...prev, color: !prev.color}))}
                      className="text-blue-400 hover:text-blue-300 text-sm whitespace-nowrap px-2 py-1 rounded hover:bg-blue-500/20 transition-colors ml-2"
                    >
                      {selectedCategories.color ? "접기" : "펼치기"}
                    </button>
                  </div>
                  
                  {selectedCategories.color && (
                    <div className="space-y-3 mt-3 pt-3 border-t border-gray-600/30">
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">차체 색상:</label>
                        <input 
                          type="text" 
                          placeholder="metallic teal, titanium gray" 
                          value={checklistData.color_finish}
                          onChange={(e) => updateChecklistData('color_finish', e.target.value)}
                          className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" 
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">휠 디자인:</label>
                        <input 
                          type="text" 
                          placeholder="multi-spoke, Y-spoke, turbine" 
                          value={checklistData.wheel}
                          onChange={(e) => updateChecklistData('wheel', e.target.value)}
                          className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" 
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">루프 대비 색상:</label>
                        <input type="text" placeholder="black, silver" className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" />
                      </div>
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-gray-300 whitespace-nowrap">트림 악센트:</label>
                        <input type="text" placeholder="chrome/gloss black/satin" className="w-48 bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500" />
                      </div>
                    </div>
                  )}
                </div>

                {/* 자유 입력 필드 */}
                <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-600/30">
                  <h4 className="text-white font-medium mb-3">✏️ 추가 요구사항</h4>
                  <textarea 
                    placeholder="자유롭게 추가 요구사항을 입력하세요..."
                    className="w-full bg-gray-700/80 border border-gray-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 resize-none"
                    rows="3"
                  ></textarea>
                </div>
                </div>
              </div>
            )}
            
            {/* 체크리스트 전송 버튼 */}
            {(isChecklistExpanded || isChecklistHovered) && (
              <div className="p-6 border-t border-gray-700">
              <button
                onClick={handleChecklistSubmit}
                disabled={!isChecklistComplete}
                className={`w-full py-3 px-6 rounded-xl font-medium transition-all duration-300 ${
                  isChecklistComplete
                    ? 'bg-green-600 hover:bg-green-700 text-white shadow-lg hover:shadow-xl transform hover:scale-105'
                    : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                }`}
              >
                {isChecklistComplete ? '🚀 이미지 생성하기' : '📝 필수 항목을 모두 채워주세요'}
              </button>
              {!isChecklistComplete && (
                <p className="text-xs text-gray-500 mt-2 text-center">
                  필수 항목: {getRequiredChecklistCompletion().completed}/{getRequiredChecklistCompletion().total} 완료
                </p>
              )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default PrototypeLab;