import { createMockResponse } from './mockData';
import { apiRequest } from './authService';
import httpLogger from '../utils/httpLogger';

const API_BASE_URL = 'http://localhost:8000/api';
const USE_MOCK_DATA = true;

// 목업 데이터
const mockChatSessions = [
  {
    session_id: 'session-1',
    user_id: 'user-1',
    started_at: '2024-01-01T10:00:00Z',
    ended_at: null
  }
];

const mockPromptLogs = [
  {
    prompt_id: 'prompt-1',
    session_id: 'session-1',
    user_prompt: '현대차 디자인에 대해 알려주세요',
    ai_response: '현대차는 Fluidic Sculpture 디자인 철학을 바탕으로...',
    created_at: '2024-01-01T10:05:00Z'
  }
];

const mockGeneratedResults = [
  {
    result_id: 'result-1',
    prompt_id: 'prompt-1',
    result_type: 'text',
    result_path: '/results/text-1.txt',
    result: '현대차 디자인 분석 결과...'
  }
];

// HTTP 요청 시뮬레이션 함수
const simulateHttpRequest = async (url, options, mockData) => {
  const requestId = httpLogger.logRequest(url, options, mockData);

  console.log('🌐 HTTP 요청 시뮬레이션:', {
    url,
    method: options.method,
    headers: options.headers,
    body: options.body
  });

  // 실제 fetch 요청을 보내지만 목업 응답을 반환
  try {
    const response = await fetch(url, options);
    console.log('📡 실제 HTTP 요청 전송됨:', {
      status: response.status,
      statusText: response.statusText,
      url: response.url
    });
    httpLogger.logResponse(requestId, response);
  } catch (error) {
    console.log('❌ 네트워크 오류 (예상됨 - Django 서버가 실행되지 않음):', error.message);
    httpLogger.logResponse(requestId, null, error);
  }

  // 목업 응답 반환
  const mockResponse = await createMockResponse(mockData);
  console.log('✅ 목업 응답 반환:', mockData);
  return mockResponse;
};

// 챗봇 세션 관련 API
export const getChatSessions = async (page = 1, pageSize = 10) => {
  const mockData = {
    count: mockChatSessions.length,
    next: null,
    previous: null,
    results: mockChatSessions
  };

  if (USE_MOCK_DATA) {
    return await simulateHttpRequest(
      `${API_BASE_URL}/chat/sessions/?page=${page}&page_size=${pageSize}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      },
      mockData
    ).then(response => response.json());
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

export const createChatSession = async () => {
  const newSession = {
    session_id: `session-${Date.now()}`,
    user_id: 'user-1',
    started_at: new Date().toISOString(),
    ended_at: null
  };
  mockChatSessions.push(newSession);

  const mockData = newSession;

  if (USE_MOCK_DATA) {
    return await simulateHttpRequest(
      `${API_BASE_URL}/chat/sessions/`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          started_at: new Date().toISOString()
        })
      },
      mockData
    ).then(response => response.json());
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

export const endChatSession = async (sessionId) => {
  const session = mockChatSessions.find(s => s.session_id === sessionId);
  if (session) {
    session.ended_at = new Date().toISOString();
  }

  const mockData = {
    message: '세션이 종료되었습니다.',
    session: session
  };

  if (USE_MOCK_DATA) {
    return await simulateHttpRequest(
      `${API_BASE_URL}/chat/sessions/${sessionId}/end/`,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          ended_at: new Date().toISOString()
        })
      },
      mockData
    ).then(response => response.json());
  }

  try {
    const response = await apiRequest(`${API_BASE_URL}/chat/sessions/${sessionId}/end/`, {
      method: 'PUT',
      body: JSON.stringify({
        ended_at: new Date().toISOString()
      })
    });
    return await response.json();
  } catch (error) {
    console.error('End chat session error:', error);
    throw error;
  }
};

// 프롬프트 로그 관련 API
export const getPromptLogs = async (sessionId, page = 1, pageSize = 20) => {
  const sessionLogs = mockPromptLogs.filter(log => log.session_id === sessionId);
  const mockData = {
    count: sessionLogs.length,
    next: null,
    previous: null,
    results: sessionLogs
  };

  if (USE_MOCK_DATA) {
    return await simulateHttpRequest(
      `${API_BASE_URL}/chat/sessions/${sessionId}/prompts/?page=${page}&page_size=${pageSize}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      },
      mockData
    ).then(response => response.json());
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
    prompt_id: `prompt-${Date.now()}`,
    session_id: sessionId,
    user_prompt: userPrompt,
    ai_response: aiResponse,
    created_at: new Date().toISOString()
  };
  mockPromptLogs.push(newPrompt);

  const mockData = newPrompt;

  if (USE_MOCK_DATA) {
    return await simulateHttpRequest(
      `${API_BASE_URL}/chat/prompts/`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          session_id: sessionId,
          user_prompt: userPrompt,
          ai_response: aiResponse
        })
      },
      mockData
    ).then(response => response.json());
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
  const promptResults = mockGeneratedResults.filter(result => result.prompt_id === promptId);
  const mockData = {
    count: promptResults.length,
    results: promptResults
  };

  if (USE_MOCK_DATA) {
    return await simulateHttpRequest(
      `${API_BASE_URL}/chat/prompts/${promptId}/results/`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      },
      mockData
    ).then(response => response.json());
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
    result_id: `result-${Date.now()}`,
    prompt_id: promptId,
    result_type: resultType,
    result_path: resultPath,
    result: result
  };
  mockGeneratedResults.push(newResult);

  const mockData = newResult;

  if (USE_MOCK_DATA) {
    return await simulateHttpRequest(
      `${API_BASE_URL}/chat/results/`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          prompt_id: promptId,
          result_type: resultType,
          result_path: resultPath,
          result: result
        })
      },
      mockData
    ).then(response => response.json());
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
export const sendChatMessage = async (sessionId, message) => {
  console.log('💬 챗봇 메시지 전송:', { sessionId, message });
  
  // 실제로는 AI 서비스와 연동
  const aiResponse = `현대차 디자인에 대한 질문이군요. ${message}에 대한 답변입니다.`;
  
  // 프롬프트 로그 생성
  const promptLog = await createPromptLog(sessionId, message, aiResponse);
  
  // 생성 결과 저장 (텍스트 타입)
  await createGeneratedResult(promptLog.prompt_id, 'text', '/results/text.txt', aiResponse);
  
  return {
    success: true,
    response: aiResponse,
    promptLog: promptLog
  };
};

export default {
  getChatSessions,
  createChatSession,
  endChatSession,
  getPromptLogs,
  createPromptLog,
  getGeneratedResults,
  createGeneratedResult,
  sendChatMessage
};
