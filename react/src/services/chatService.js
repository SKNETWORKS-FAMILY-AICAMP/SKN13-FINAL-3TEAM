import { createMockResponse } from './mockData';

const API_BASE_URL = 'http://localhost:8000/api/v1';
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

// 챗봇 세션 관련 API
export const getChatSessions = async (page = 1, pageSize = 10) => {
  if (USE_MOCK_DATA) {
    const mockResponse = await createMockResponse({
      count: mockChatSessions.length,
      next: null,
      previous: null,
      results: mockChatSessions
    });
    return await mockResponse.json();
  }

  try {
    const response = await fetch(`${API_BASE_URL}/chat/sessions/?page=${page}&page_size=${pageSize}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    return await response.json();
  } catch (error) {
    console.error('Get chat sessions error:', error);
    throw error;
  }
};

export const createChatSession = async () => {
  if (USE_MOCK_DATA) {
    const newSession = {
      session_id: `session-${Date.now()}`,
      user_id: 'user-1',
      started_at: new Date().toISOString(),
      ended_at: null
    };
    mockChatSessions.push(newSession);
    
    const mockResponse = await createMockResponse(newSession, 201);
    return await mockResponse.json();
  }

  try {
    const response = await fetch(`${API_BASE_URL}/chat/sessions/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
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
  if (USE_MOCK_DATA) {
    const session = mockChatSessions.find(s => s.session_id === sessionId);
    if (session) {
      session.ended_at = new Date().toISOString();
    }
    
    const mockResponse = await createMockResponse({
      message: '세션이 종료되었습니다.',
      session: session
    });
    return await mockResponse.json();
  }

  try {
    const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/end/`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
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
  if (USE_MOCK_DATA) {
    const sessionLogs = mockPromptLogs.filter(log => log.session_id === sessionId);
    const mockResponse = await createMockResponse({
      count: sessionLogs.length,
      next: null,
      previous: null,
      results: sessionLogs
    });
    return await mockResponse.json();
  }

  try {
    const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/prompts/?page=${page}&page_size=${pageSize}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    return await response.json();
  } catch (error) {
    console.error('Get prompt logs error:', error);
    throw error;
  }
};

export const createPromptLog = async (sessionId, userPrompt, aiResponse) => {
  if (USE_MOCK_DATA) {
    const newPrompt = {
      prompt_id: `prompt-${Date.now()}`,
      session_id: sessionId,
      user_prompt: userPrompt,
      ai_response: aiResponse,
      created_at: new Date().toISOString()
    };
    mockPromptLogs.push(newPrompt);
    
    const mockResponse = await createMockResponse(newPrompt, 201);
    return await mockResponse.json();
  }

  try {
    const response = await fetch(`${API_BASE_URL}/chat/prompts/`, {
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
    const promptResults = mockGeneratedResults.filter(result => result.prompt_id === promptId);
    const mockResponse = await createMockResponse({
      count: promptResults.length,
      results: promptResults
    });
    return await mockResponse.json();
  }

  try {
    const response = await fetch(`${API_BASE_URL}/chat/prompts/${promptId}/results/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    return await response.json();
  } catch (error) {
    console.error('Get generated results error:', error);
    throw error;
  }
};

export const createGeneratedResult = async (promptId, resultType, resultPath, result) => {
  if (USE_MOCK_DATA) {
    const newResult = {
      result_id: `result-${Date.now()}`,
      prompt_id: promptId,
      result_type: resultType,
      result_path: resultPath,
      result: result
    };
    mockGeneratedResults.push(newResult);
    
    const mockResponse = await createMockResponse(newResult, 201);
    return await mockResponse.json();
  }

  try {
    const response = await fetch(`${API_BASE_URL}/chat/results/`, {
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
    });
    return await response.json();
  } catch (error) {
    console.error('Create generated result error:', error);
    throw error;
  }
};

// 챗봇 메시지 전송 (AI 응답 시뮬레이션)
export const sendChatMessage = async (sessionId, message) => {
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
