import React, { useState } from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';

function Chatbot() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'user',
      content: '안녕하세요! 자동차 디자인에 대해 궁금한 점이 있어요.',
      timestamp: '2025-01-20 14:30'
    },
    {
      id: 2,
      type: 'bot',
      content: '안녕하세요! 자동차 디자인에 대해 어떤 것이 궁금하신가요? 전기차, 내연기관차, SUV 등 다양한 차종에 대해 질문해주세요.',
      timestamp: '2025-01-20 14:31'
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    const newMessage = {
      id: messages.length + 1,
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toLocaleString()
    };

    setMessages([...messages, newMessage]);
    setInputMessage('');

    // 봇 응답 시뮬레이션
    setTimeout(() => {
      const botResponse = {
        id: messages.length + 2,
        type: 'bot',
        content: '질문해주셔서 감사합니다. 더 구체적인 정보를 제공해드릴 수 있도록 추가 질문을 해주세요.',
        timestamp: new Date().toLocaleString()
      };
      setMessages(prev => [...prev, botResponse]);
    }, 1000);
  };

  return (
    <div className="min-h-screen" style={{backgroundColor: '#353745'}}>
      <Header />
      
      <div className="flex h-screen">
        {/* Left Sidebar */}
        <div className="w-80 bg-gray-800 border-r border-gray-700 p-6">
          <h2 className="text-white text-xl font-semibold mb-6">채팅 세션</h2>
          
          <button className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg mb-6 flex items-center justify-center space-x-2 hover:bg-blue-700 transition-colors">
            <span>+</span>
            <span>새로운 채팅</span>
          </button>
          
          <div className="space-y-2">
            <div className="bg-gray-700 rounded-lg p-3 cursor-pointer hover:bg-gray-600 transition-colors">
              <h3 className="text-white text-sm font-medium">자동차 디자인 문의</h3>
              <p className="text-gray-400 text-xs">2025-01-20 14:30</p>
            </div>
            
            <div className="bg-gray-700 rounded-lg p-3 cursor-pointer hover:bg-gray-600 transition-colors">
              <h3 className="text-white text-sm font-medium">전기차 정보</h3>
              <p className="text-gray-400 text-xs">2025-01-19 16:45</p>
            </div>
            
            <div className="bg-gray-700 rounded-lg p-3 cursor-pointer hover:bg-gray-600 transition-colors">
              <h3 className="text-white text-sm font-medium">SUV 디자인</h3>
              <p className="text-gray-400 text-xs">2025-01-18 11:20</p>
            </div>
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Chat Header */}
          <div className="bg-gray-800 border-b border-gray-700 p-4">
            <h1 className="text-white text-xl font-semibold">AI 디자인 어시스턴트</h1>
            <p className="text-gray-400 text-sm">자동차 디자인에 대한 모든 질문에 답변해드립니다</p>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.map((message) => (
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
                  <p className="text-sm">{message.content}</p>
                  <p className="text-xs opacity-70 mt-1">{message.timestamp}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Input Area */}
          <div className="bg-gray-800 border-t border-gray-700 p-4">
            <form onSubmit={handleSendMessage} className="flex space-x-4">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="메시지를 입력하세요..."
                className="flex-1 px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
              />
              <button
                type="submit"
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                전송
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