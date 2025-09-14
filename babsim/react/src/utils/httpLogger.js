// HTTP 요청 로깅 유틸리티
class HttpLogger {
  constructor() {
    this.requests = [];
    this.isEnabled = true;
  }

  // 요청 로깅
  logRequest(url, options, mockData) {
    if (!this.isEnabled) return;

    const request = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      url,
      method: options.method,
      headers: options.headers,
      body: options.body,
      mockData,
      status: 'pending'
    };

    this.requests.push(request);
    this.logToConsole(request);
    this.logToNetworkTab(request);
    
    return request.id;
  }

  // 응답 로깅
  logResponse(requestId, response, error = null) {
    if (!this.isEnabled) return;

    const request = this.requests.find(r => r.id === requestId);
    if (request) {
      request.status = error ? 'error' : 'success';
      request.response = response;
      request.error = error;
      request.responseTime = Date.now() - request.id;
      
      this.logToConsole(request, 'response');
    }
  }

  // 콘솔에 로깅
  logToConsole(request, type = 'request') {
    const style = `
      background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 8px 12px;
      border-radius: 6px;
      font-family: 'Courier New', monospace;
      font-size: 12px;
      margin: 4px 0;
    `;

    if (type === 'request') {
      console.group(`🌐 HTTP ${request.method} ${request.url}`);
      console.log('%cRequest Details:', style);
      console.table({
        Method: request.method,
        URL: request.url,
        Headers: request.headers,
        Body: request.body,
        MockData: request.mockData
      });
      console.groupEnd();
    } else {
      console.group(`✅ Response for ${request.method} ${request.url}`);
      console.log('%cResponse Details:', style);
      console.table({
        Status: request.status,
        ResponseTime: `${request.responseTime}ms`,
        Response: request.response,
        Error: request.error
      });
      console.groupEnd();
    }
  }

  // Network 탭 시뮬레이션
  logToNetworkTab(request) {
    // 실제 fetch 요청을 보내서 Network 탭에서 확인 가능하게 함
    fetch(request.url, {
      method: request.method,
      headers: request.headers,
      body: request.body
    }).catch(error => {
      // 예상되는 네트워크 오류 (Django 서버가 실행되지 않음)
      console.log('❌ Network Error (Expected - Django server not running):', error.message);
    });
  }

  // 모든 요청 기록 조회
  getRequests() {
    return this.requests;
  }

  // 요청 기록 초기화
  clearRequests() {
    this.requests = [];
  }

  // 로깅 활성화/비활성화
  setEnabled(enabled) {
    this.isEnabled = enabled;
  }

  // 요청 통계
  getStats() {
    const total = this.requests.length;
    const success = this.requests.filter(r => r.status === 'success').length;
    const error = this.requests.filter(r => r.status === 'error').length;
    const pending = this.requests.filter(r => r.status === 'pending').length;

    return {
      total,
      success,
      error,
      pending,
      successRate: total > 0 ? (success / total * 100).toFixed(1) : 0
    };
  }
}

// 전역 인스턴스 생성
const httpLogger = new HttpLogger();

// 개발자 도구에서 접근 가능하도록 전역에 노출
if (typeof window !== 'undefined') {
  window.httpLogger = httpLogger;
  
  // 개발자 도구에서 사용할 수 있는 헬퍼 함수들
  window.httpDebug = {
    // 모든 요청 보기
    showRequests: () => {
      console.table(httpLogger.getRequests().map(r => ({
        id: r.id,
        method: r.method,
        url: r.url,
        status: r.status,
        responseTime: r.responseTime || 'N/A'
      })));
    },
    
    // 요청 기록 초기화
    clearRequests: () => {
      httpLogger.clearRequests();
      console.log('✅ HTTP 요청 기록이 초기화되었습니다.');
    },
    
    // 통계 보기
    showStats: () => {
      const stats = httpLogger.getStats();
      console.log('📊 HTTP 요청 통계:', stats);
    },
    
    // 로깅 활성화/비활성화
    toggleLogging: () => {
      const enabled = !httpLogger.isEnabled;
      httpLogger.setEnabled(enabled);
      console.log(`🔧 HTTP 로깅이 ${enabled ? '활성화' : '비활성화'}되었습니다.`);
    }
  };
}

export default httpLogger;
