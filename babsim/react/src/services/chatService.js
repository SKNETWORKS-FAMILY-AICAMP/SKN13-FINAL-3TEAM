import { createMockResponse } from './mockData';
import { apiRequest } from './authService';
import httpLogger from '../utils/httpLogger';
import { flushSync } from 'react-dom';

// const API_BASE_URL = 'http://localhost:8000/api';
const API_BASE_URL = '/api';
const USE_MOCK_DATA = false;

// 목업 데이터 - 실제 파일 경로 사용
const mockChatSessions = [
  {
    session_id: 'session-1',
    user_id: 'user-1',
    started_at: '2024-01-01T10:00:00Z',
    ended_at: null,
    title: '현대차 아이오닉6 프로토타입 대화'
  }
];

const mockPromptLogs = [];
const mockGeneratedResults = [];


// 고유 ID 생성 함수
const generateUniqueId = () => {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

// 스트리밍 응답 처리 함수
const handleStreamingResponse = async (response, onStreamingUpdate, setMessages, streamingMessageId) => {
  console.log('🔍 [StreamingHttpResponse] ReadableStream 시작 - response.body:', response.body);
  console.log('🔍 [StreamingHttpResponse] ReadableStream locked:', response.body.locked);
  
  // HTTP 헤더에서 메타데이터 읽기
  const metadata = {
    sessionId: response.headers.get('X-Session-ID') || '',
    promptId: response.headers.get('X-Prompt-ID') || '',
    intent: response.headers.get('X-Intent') || '',
    isFormComplete: response.headers.get('X-Is-Form-Complete') === 'true',
    imageQuery: response.headers.get('X-Image-Query') || '',
    generatedResultsCount: parseInt(response.headers.get('X-Generated-Results') || '0'),
    completionStatus: response.headers.get('X-Completion-Status') || '{}',
    checklistData: response.headers.get('X-Checklist-Data') || '{}',
    userId: response.headers.get('X-User-ID') || 'default_user',
    userMessage: response.headers.get('X-User-Message') || '사용자 메시지'
  };
  
  console.log('🔍 스트리밍 응답 메타데이터:', metadata);
  
  // 초기 스트리밍 메시지 생성
  if (setMessages) {
    setMessages(prev => {
      return [...prev, { 
        id: streamingMessageId, 
        type: 'ai', 
        content: '', 
        timestamp: new Date().toISOString(),
        isStreaming: true
      }];
    });
  }
  
  // StreamingHttpResponse를 ReadableStream으로 처리
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let fullResponse = '';
  
  console.log('🔍 [StreamingHttpResponse] Reader 생성 완료:', reader);
  
  try {
    while (true) {
      const { done, value } = await reader.read();  
      if (done) break;
      
      console.log('🔍 [StreamingHttpResponse] 새로 들어온 ChunkValue:', value);

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n'); // 각각의 줄이 하나하나의 이벤트(청크)

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataContent = line.slice(6).trim();
          
          // [DONE] 신호 처리
          if (dataContent === '[DONE]') {
            console.log('✅ 스트리밍 완료: [DONE]');
            break;
          }
          
          try {
            const data = JSON.parse(dataContent);
            if (data.error) {
              throw new Error(data.error);
            }
            if (data.content) {
              fullResponse += data.content;
              // 실시간으로 UI 업데이트
              const timestamp = new Date().toLocaleTimeString('ko-KR', { 
                hour12: false, 
                hour: '2-digit', 
                minute: '2-digit', 
                second: '2-digit',
                fractionalSecondDigits: 3
              });
              console.log(`[${timestamp}] 스트리밍 청크:`, data.content);
              
              // 실시간 스트리밍 메시지 업데이트를 위한 콜백 호출
              if (onStreamingUpdate) {
                console.log('🔄 onStreamingUpdate 호출:', fullResponse);
                onStreamingUpdate(fullResponse);
              }
            } else {
              console.log('⚠️ content가 없습니다:', data);
            }
          } catch (e) {
            console.warn('JSON 파싱 실패, 원본 데이터 사용:', e.message, '원본 데이터:', dataContent);
            // JSON 파싱 실패 시 원본 데이터를 그대로 사용
            if (dataContent && dataContent.trim()) {
              fullResponse += dataContent;
              if (onStreamingUpdate) {
                onStreamingUpdate(fullResponse);
              }
            }
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
  
  console.log('✅ 스트리밍 응답 완료:', fullResponse);
  
  // 스트리밍 완료 후 대화 기록 업데이트
  try {
    console.log('🔄 대화 기록 업데이트 시작:', {
      sessionId: metadata.sessionId,
      userId: metadata.userId,
      userMessage: metadata.userMessage,
      responseLength: fullResponse.length
    });
    
    // 올바른 데이터 전달
    await updateChatHistory(
      metadata.sessionId, 
      metadata.userId || 'default_user', 
      metadata.userMessage || '사용자 메시지', 
      fullResponse
    );
    console.log('✅ 대화 기록 업데이트 완료');
  } catch (error) {
    console.error('❌ 대화 기록 업데이트 실패:', error);
    // 오류가 발생해도 스트리밍 응답은 정상적으로 반환
  }
  
  return {
    success: true,
    response: fullResponse,
    generatedResults: [],
    completionStatus: metadata.completionStatus ? JSON.parse(metadata.completionStatus) : {},
    checklistData: metadata.checklistData ? JSON.parse(metadata.checklistData) : {},
    intent: metadata.intent,
    isFormComplete: metadata.isFormComplete,
    imageQuery: metadata.imageQuery,
    sessionId: metadata.sessionId,
    promptId: metadata.promptId
  };
};

// 챗봇 세션 관련 API
export const getChatSessions = async (page = 1, pageSize = 10) => {
  if (USE_MOCK_DATA) {
    console.log('🔄 목업 모드: 채팅 세션 목록 반환');
    return {
      count: mockChatSessions.length,
      next: null,
      previous: null,
      results: mockChatSessions
    };
  }

  try {
    const response = await apiRequest(`${API_BASE_URL}/chat/sessions/?page=${page}&page_size=${pageSize}`, {
      method: 'GET',
    });
    return await response.json();
  } catch (error) {
    console.error('Get chat sessions error:', error);
    throw error;
  }
};

export const createChatSession = async (title = null) => {
  const newSession = {
    session_id: `session-${generateUniqueId()}`,
    user_id: 'user-1',
    started_at: new Date().toISOString(),
    ended_at: null,
    title: title || `새로운 대화 ${new Date().toLocaleString()}`
  };
  
  if (USE_MOCK_DATA) {
    console.log('🔄 목업 모드: 새 채팅 세션 생성');
    mockChatSessions.push(newSession);
    return newSession;
  }

  try {
    const response = await apiRequest(`${API_BASE_URL}/chat/sessions/`, {
      method: 'POST',
      body: JSON.stringify({
        started_at: new Date().toISOString()
      })
    });
    return await response.json();
  } catch (error) {
    console.error('Create chat session error:', error);
    throw error;
  }
};

// 세션 제목 수정 API
export const updateSessionTitle = async (sessionId, title) => {
  if (USE_MOCK_DATA) {
    console.log('🔄 목업 모드: 세션 제목 수정');
    const session = mockChatSessions.find(s => s.session_id === sessionId);
    if (session) {
      session.title = title;
      return {
        message: '세션 제목이 수정되었습니다.',
        session: {
          session_id: sessionId,
          title: title,
          updated_at: new Date().toISOString()
        }
      };
    }
    throw new Error('세션을 찾을 수 없습니다.');
  }

  try {
    const response = await apiRequest(`${API_BASE_URL}/chat/sessions/${sessionId}/title/`, {
      method: 'PUT',
      body: JSON.stringify({ title })
    });
    return await response.json();
  } catch (error) {
    console.error('Update session title error:', error);
    throw error;
  }
};

export const endChatSession = async (sessionId) => {
  const session = mockChatSessions.find(s => s.session_id === sessionId);
  if (session) {
    session.ended_at = new Date().toISOString();
  }

  if (USE_MOCK_DATA) {
    console.log('🔄 목업 모드: 채팅 세션 종료');
    const promptCount = mockPromptLogs.filter(log => log.session_id === sessionId).length;
    return {
      message: '챗봇 세션이 종료되었습니다.',
      session: {
        session_id: sessionId,
        ended_at: session.ended_at,
        total_prompts: promptCount,
        total_duration: '1시간' // 임시 값
      }
    };
  }

  try {
    const response = await apiRequest(`${API_BASE_URL}/chat/sessions/${sessionId}/end/`, {
      method: 'PUT'
    });
    return await response.json();
  } catch (error) {
    console.error('End chat session error:', error);
    throw error;
  }
};

// 프롬프트 로그 관련 API
export const getPromptLogs = async (sessionId, page = 1, pageSize = 20) => {
  if (USE_MOCK_DATA) {
    console.log('🔄 목업 모드: 프롬프트 로그 반환');
    const sessionLogs = mockPromptLogs.filter(log => log.session_id === sessionId);
    return {
      count: sessionLogs.length,
      next: null,
      previous: null,
      results: sessionLogs
    };
  }

  try {
    const response = await apiRequest(`${API_BASE_URL}/chat/sessions/${sessionId}/prompts/?page=${page}&page_size=${pageSize}`, {
      method: 'GET',
    });
    return await response.json();
  } catch (error) {
    console.error('Get prompt logs error:', error);
    throw error;
  }
};

export const createPromptLog = async (sessionId, userPrompt, aiResponse) => {
  const newPrompt = {
    prompt_id: `prompt-${generateUniqueId()}`,
    session_id: sessionId,
    user_prompt: userPrompt,
    ai_response: aiResponse,
    created_at: new Date().toISOString()
  };
  
  if (USE_MOCK_DATA) {
    console.log('🔄 목업 모드: 프롬프트 로그 생성');
    mockPromptLogs.push(newPrompt);
    return newPrompt;
  }

  try {
    const response = await apiRequest(`${API_BASE_URL}/chat/prompts/`, {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        user_prompt: userPrompt,
        ai_response: aiResponse
      })
    });
    return await response.json();
  } catch (error) {
    console.error('Create prompt log error:', error);
    throw error;
  }
};

// 생성 결과 관련 API
export const getGeneratedResults = async (promptId) => {
  if (USE_MOCK_DATA) {
    console.log('🔄 목업 모드: 생성 결과 반환');
    const promptResults = mockGeneratedResults.filter(result => result.prompt_id === promptId);
    return {
      count: promptResults.length,
      results: promptResults
    };
  }

  try {
    const response = await apiRequest(`${API_BASE_URL}/chat/prompts/${promptId}/results/`, {
      method: 'GET',
    });
    return await response.json();
  } catch (error) {
    console.error('Get generated results error:', error);
    throw error;
  }
};

export const createGeneratedResult = async (promptId, resultType, resultPath, result) => {
  const newResult = {
    result_id: `result-${generateUniqueId()}`,
    prompt_id: promptId,
    result_type: resultType,
    result_path: resultPath,
    result: result
  };
  
  if (USE_MOCK_DATA) {
    console.log('🔄 목업 모드: 생성 결과 저장');
    mockGeneratedResults.push(newResult);
    return newResult;
  }

  try {
    const response = await apiRequest(`${API_BASE_URL}/chat/results/`, {
      method: 'POST',
      body: JSON.stringify({
        prompt_id: promptId,
        result_type: resultType,
        result_path: resultPath,
        result: result
      })
    });
    return await response.json();
  } catch (error) {
    console.error('Create generated result error:', error);
    throw error;
  }
};

// 챗봇 메시지 전송 (AI 응답 시뮬레이션)
export const sendChatMessage = async (sessionId, message, userId, onStreamingUpdate = null, setMessages = null, streamingMessageId = null, checklistData = {}, completionStatus = {}) => {
  console.log('💬 챗봇 메시지 전송:', { sessionId, message, userId, onStreamingUpdate, checklistData, completionStatus });
  
  // 목업 모드일 때는 Django 서버 연결 시도하지 않음
  if (USE_MOCK_DATA) {
    console.log('🔄 목업 모드: 목업 응답 생성');
    
    // 목업 응답 생성
    const mockResponse = generateMockResponse(message);
    
    // 프롬프트 로그 생성
    // const promptLog = await createPromptLog(sessionId, message, mockResponse.aiResponse);
    
    // 생성 결과가 있으면 저장
    // if (mockResponse.generatedResults && mockResponse.generatedResults.length > 0) {
    //   for (const result of mockResponse.generatedResults) {
    //     await createGeneratedResult(
    //       promptLog.prompt_id,
    //       result.result_type,
    //       result.result_path,
    //       result.result
    //     );
    //   }
    // }
    
    return {
      success: true,
      response: mockResponse.aiResponse,
      generatedResults: mockResponse.generatedResults || []
    };
  }
  
  // 실제 서버 모드일 때만 Django 서버 연결 시도
  try {
    // 디버깅: userId 확인
    console.log('🔍 chatService 디버깅:');
    console.log('  - userId:', userId);
    
    const requestBody = {
      user_id: userId || '550e8400-e29b-41d4-a716-446655440000',  // UUID 형식의 기본값 사용
      message: message,
      checklistData: checklistData,
      completionStatus: completionStatus
    };
    
    console.log('  - 최종 requestBody.user_id:', requestBody.user_id);
    
    const response = await apiRequest(`${API_BASE_URL}/chat/sessions/${sessionId}/message/`, {
      method: 'POST',
      body: JSON.stringify(requestBody)
    });
    
    if (response.ok) {
      // Content-Type 확인하여 스트리밍 응답인지 판단
      const contentType = response.headers.get('content-type');
      console.log('🔍 응답 Content-Type:', contentType);
      
      if (contentType && contentType.includes('text/event-stream')) {
        // 스트리밍 응답 처리
        console.log('🔄 스트리밍 응답 감지 - 스트리밍 처리 시작');
        return await handleStreamingResponse(response, onStreamingUpdate, setMessages, streamingMessageId);
      } else {
        // 일반 JSON 응답 처리
        console.log('✅ Django 서버 일반 응답: response', response);
        const data = await response.json();
        
        return {
          success: true,
          response: data.reply,  // config/views.py에서 reply로 반환
          generatedResults: data.generated_results || [],
          completionStatus: data.completion_status || null,  // 체크리스트 완성도 정보
          checklistData: data.checklist_data || {},
          intent: data.intent || '',
          isFormComplete: data.is_form_complete || false,
          imageQuery: data.image_query || ''
        };
      }
    } else {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    
  } catch (error) {
    console.error('❌ Django 서버 연동 실패:', error);
    throw error;
  }
};

// 목업 응답 생성 - 실제 파일 경로 사용
const generateMockResponse = (message) => {
  // 메시지 내용에 따라 다른 응답 생성
  const lowerMessage = message.toLowerCase();
  
  if (lowerMessage.includes('안녕') || lowerMessage.includes('hello') || lowerMessage.includes('hi')) {
    return {
      aiResponse: '안녕하세요! 현대차 Prototype Lab에 오신 것을 환영합니다. 저는 AI 어시스턴트로, 현대차 디자인과 관련된 질문에 답변하고 프로토타입을 생성해드릴 수 있습니다. 무엇을 도와드릴까요?',
      generatedResults: []
    };
  }
  
  if (lowerMessage.includes('공기역학') || lowerMessage.includes('푸른') || lowerMessage.includes('파스텔') || lowerMessage.includes('ionic') || lowerMessage.includes('차량') || lowerMessage.includes('개발') || lowerMessage.includes('이미지')) {
    return {
      aiResponse: '공기역학적인 푸른 파스텔 계열의 Ionic 차량 개발 요청을 받았습니다. 사용자의 쿼리를 분석하여 최적의 디자인을 제안해드리겠습니다.',
      generatedResults: [
        {
          result_id: `result-${generateUniqueId()}-image`,
          prompt_id: `prompt-${generateUniqueId()}`,
          result_type: 'image',
          result_path: '/src/assets/prototype_lab/Ionic6.png',
          result: '/src/assets/prototype_lab/Ionic6.png'
        }
      ]
    };
  }
  
  if (lowerMessage.includes('3d') || lowerMessage.includes('모델') || lowerMessage.includes('glb') || lowerMessage.includes('3d모델')) {
    return {
      aiResponse: '3D 모델을 생성해드리겠습니다. 공기역학적 설계가 반영된 푸른 파스텔 계열 Ionic 차량의 3D 모델을 준비했습니다.',
      generatedResults: [
        {
          result_id: `result-${generateUniqueId()}-3d`,
          prompt_id: `prompt-${generateUniqueId()}`,
          result_type: '3d',
          result_path: '/src/assets/prototype_lab/Ionic6_3D.mp4',
          result: '공기역학적 설계가 반영된 푸른 파스텔 계열 Ionic 차량의 3D 모델이 생성되었습니다. MP4 파일을 재생하여 3D 모델을 확인하세요.'
        }
      ]
    };
  }
  
  if (lowerMessage.includes('4d') || lowerMessage.includes('비디오') || lowerMessage.includes('영상') || lowerMessage.includes('시뮬레이션') || lowerMessage.includes('4d비디오')) {
    return {
      aiResponse: '4D 시뮬레이션을 생성해드리겠습니다. 시간에 따른 변화를 포함한 동적 모델을 준비했습니다.',
      generatedResults: [
        {
          result_id: `result-${generateUniqueId()}-4d`,
          prompt_id: `prompt-${generateUniqueId()}`,
          result_type: '4d',
          result_path: '/src/assets/prototype_lab/Ionic6_4D.mp4',
          result: '4D 시뮬레이션 결과입니다. 시간에 따른 변화를 포함한 동적 모델입니다. MP4 파일을 재생하여 시뮬레이션을 확인하세요.'
        }
      ]
    };
  }
  
  // 기본 응답
  return {
    aiResponse: `"${message}"에 대한 답변입니다. 현대차는 Fluidic Sculpture 디자인 철학을 바탕으로 미래지향적이고 역동적인 디자인을 추구합니다. 더 구체적인 질문이 있으시면 말씀해주세요.`,
    generatedResults: []
  };
};

// 스트리밍 완료 후 대화 기록 업데이트
const updateChatHistory = async (sessionId, userId, userMessage, assistantResponse) => {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/update-history/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
      body: JSON.stringify({
        user_id: userId,
        user_message: userMessage,
        assistant_response: assistantResponse
      })
    });
    
    if (!response.ok) {
      // 서버 응답 텍스트를 먼저 읽어서 오류 내용 확인
      const errorText = await response.text();
      console.error('❌ 서버 오류 응답:', errorText);
      throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
    }
    
    // Content-Type 확인
    const contentType = response.headers.get('content-type');
    console.log('🔍 updateChatHistory 응답 Content-Type:', contentType);
    
    if (contentType && contentType.includes('application/json')) {
      const result = await response.json();
      console.log('✅ updateChatHistory JSON 응답:', result);
      return result;
    } else {
      // JSON이 아닌 경우 텍스트로 처리
      const result = await response.text();
      console.log('✅ updateChatHistory 텍스트 응답:', result);
      return { success: true, message: result };
    }
    
  } catch (error) {
    console.error('대화 기록 업데이트 API 호출 실패:', error);
    throw error;
  }
};

export default {
  getChatSessions,
  createChatSession,
  updateSessionTitle,
  endChatSession,
  getPromptLogs,
  createPromptLog,
  getGeneratedResults,
  createGeneratedResult,
  sendChatMessage
};
