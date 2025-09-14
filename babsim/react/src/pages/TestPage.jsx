import React, { useState } from 'react';
import { flushSync } from 'react-dom';

const TestPage = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [streamingMessageId, setStreamingMessageId] = useState(null);

  // flushSync 없이 일반 setMessages 호출 (새 메시지 생성)
  const handleNormalUpdate = (text) => {
    console.log('🔄 일반 업데이트:', text);
    setMessages(prev => [...prev, { 
      id: Date.now(), 
      content: text, 
      type: 'normal',
      timestamp: new Date().toISOString()
    }]);
  };

  // flushSync를 사용한 즉시 업데이트 (새 메시지 생성)
  const handleFlushSyncUpdate = (text) => {
    console.log('⚡ flushSync 업데이트:', text);
    flushSync(() => {
      setMessages(prev => [...prev, { 
        id: Date.now(), 
        content: text, 
        type: 'flushSync',
        timestamp: new Date().toISOString()
      }]);
    });
  };

  // 스트리밍 메시지 시작 (새 메시지 객체 생성)
  const startStreamingMessage = (type) => {
    const messageId = Date.now();
    setStreamingMessageId(messageId);
    
    const newMessage = {
      id: messageId,
      content: '',
      type: type,
      timestamp: new Date().toISOString(),
      isStreaming: true
    };

    if (type === 'flushSync') {
      flushSync(() => {
        setMessages(prev => [...prev, newMessage]);
      });
    } else {
      setMessages(prev => [...prev, newMessage]);
    }
    
    console.log(`🚀 스트리밍 메시지 시작 (${type}):`, messageId);
  };

  // 스트리밍 메시지에 청크 추가
  const addChunkToStreamingMessage = (chunk, type) => {
    if (!streamingMessageId) return;

    const timestamp = new Date().toLocaleTimeString('ko-KR', { 
      hour12: false, 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit',
      fractionalSecondDigits: 3
    });

    if (type === 'flushSync') {
      flushSync(() => {
        setMessages(prev => prev.map(msg => 
          msg.id === streamingMessageId 
            ? { ...msg, content: msg.content + chunk }
            : msg
        ));
      });
      console.log(`[${timestamp}] ⚡ flushSync 청크 추가:`, chunk);
    } else {
      setMessages(prev => prev.map(msg => 
        msg.id === streamingMessageId 
          ? { ...msg, content: msg.content + chunk }
          : msg
      ));
      console.log(`[${timestamp}] 🔄 일반 청크 추가:`, chunk);
    }
  };

  // 입력값이 변경될 때마다 청크로 추가
  const handleInputChange = (e) => {
    const value = e.target.value;
    setInputMessage(value);
    
    // 첫 번째 문자면 스트리밍 메시지 시작
    if (value.length === 1) {
      startStreamingMessage('flushSync');
    }
    
    // 문자 하나하나씩 청크로 추가
    if (value.length > 0) {
      const lastChar = value[value.length - 1];
      addChunkToStreamingMessage(lastChar, 'flushSync');
    }
  };

  // 메시지 초기화
  const clearMessages = () => {
    setMessages([]);
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-8 text-gray-800">
          flushSync & setMessages 즉시 리렌더링 테스트
        </h1>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 입력 영역 */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-700">입력 영역</h2>
            
            {/* 실시간 입력 테스트 */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-600 mb-2">
                실시간 입력 (문자 하나하나마다 즉시 반영):
              </label>
              <input
                type="text"
                value={inputMessage}
                onChange={handleInputChange}
                placeholder="여기에 입력하세요..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* 버튼 테스트 */}
            <div className="space-y-4">
              <button
                onClick={() => {
                  startStreamingMessage('normal');
                  // "일반 업데이트 테스트"를 문자 하나씩 청크로 추가
                  const text = '일반 업데이트 테스트';
                  text.split('').forEach((char, index) => {
                    setTimeout(() => {
                      addChunkToStreamingMessage(char, 'normal');
                    }, index * 100); // 100ms 간격으로 청크 추가
                  });
                }}
                className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              >
                일반 스트리밍 (배치 처리)
              </button>
              
              <button
                onClick={() => {
                  startStreamingMessage('flushSync');
                  // "flushSync 업데이트 테스트"를 문자 하나씩 청크로 추가
                  const text = 'flushSync 업데이트 테스트';
                  text.split('').forEach((char, index) => {
                    setTimeout(() => {
                      addChunkToStreamingMessage(char, 'flushSync');
                    }, index * 100); // 100ms 간격으로 청크 추가
                  });
                }}
                className="w-full px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
              >
                flushSync 스트리밍 (즉시 처리)
              </button>
              
              <button
                onClick={clearMessages}
                className="w-full px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
              >
                메시지 초기화
              </button>
            </div>
          </div>

          {/* 출력 영역 */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-700">
              실시간 출력 (총 {messages.length}개 메시지)
            </h2>
            
            <div className="h-96 overflow-y-auto border border-gray-200 rounded-lg p-4 bg-gray-50">
              {messages.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                  메시지가 없습니다. 입력하거나 버튼을 클릭해보세요.
                </p>
              ) : (
                <div className="space-y-2">
                  {messages.map((message, index) => (
                    <div
                      key={message.id}
                      className={`p-3 rounded-lg ${
                        message.type === 'flushSync' 
                          ? 'bg-green-100 border-l-4 border-green-500' 
                          : 'bg-blue-100 border-l-4 border-blue-500'
                      }`}
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-sm text-gray-600">
                              {message.type === 'flushSync' ? '⚡ flushSync' : '🔄 일반'}
                            </span>
                            {message.isStreaming && (
                              <span className="text-xs bg-yellow-200 text-yellow-800 px-2 py-1 rounded">
                                스트리밍 중...
                              </span>
                            )}
                            <span className="text-xs text-gray-500">
                              #{index + 1}
                            </span>
                          </div>
                          <p className="text-gray-800 font-mono text-sm">
                            {message.content || '(빈 메시지)'}
                          </p>
                          <div className="text-xs text-gray-400 mt-1">
                            길이: {message.content.length}자
                          </div>
                        </div>
                      </div>
                      <div className="text-xs text-gray-400 mt-1">
                        {new Date(message.timestamp).toLocaleTimeString('ko-KR', {
                          hour12: false,
                          hour: '2-digit',
                          minute: '2-digit',
                          second: '2-digit',
                          fractionalSecondDigits: 3
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 디버그 정보 */}
        <div className="mt-8 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-yellow-800 mb-2">스트리밍 테스트 방법:</h3>
          <ul className="text-sm text-yellow-700 space-y-1">
            <li>• <strong>실시간 입력:</strong> 입력창에 타이핑하면 문자 하나하나가 청크로 추가되어 즉시 반영됩니다</li>
            <li>• <strong>일반 스트리밍:</strong> React의 기본 배치 처리로 청크들이 묶여서 처리됩니다</li>
            <li>• <strong>flushSync 스트리밍:</strong> 각 청크마다 즉시 DOM 업데이트가 발생하여 실시간으로 보입니다</li>
            <li>• <strong>스트리밍 상태:</strong> "스트리밍 중..." 표시로 실시간 업데이트를 확인할 수 있습니다</li>
            <li>• <strong>콘솔 로그:</strong> 개발자 도구에서 각 청크 추가 로그를 확인할 수 있습니다</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default TestPage;
