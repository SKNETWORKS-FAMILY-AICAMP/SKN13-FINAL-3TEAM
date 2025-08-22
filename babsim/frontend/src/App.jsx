import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Home from './pages/Home';
import Login from './pages/Login';
import Signup from './pages/Signup';
import AssetLibrary from './pages/AssetLibrary';
import InsightTrends from './pages/InsightTrends';
import PrototypeLab from './pages/PrototypeLab';
import Chatbot from './pages/Chatbot';
import Profile from './pages/Profile';
import MyWorkspace from './pages/MyWorkspace';
import './App.css';

function App() {
  useEffect(() => {
    // 개발자 도구에서 HTTP 요청 확인 안내
    console.log(`
🚀 React 앱이 시작되었습니다!

📡 HTTP 요청 모니터링:
- 모든 HTTP 요청이 콘솔에 로깅됩니다
- Network 탭에서 실제 요청을 확인할 수 있습니다
- Django 서버가 실행되지 않아 네트워크 오류가 발생하는 것은 정상입니다

🔧 개발자 도구에서 사용할 수 있는 명령어:
- httpDebug.showRequests() - 모든 요청 보기
- httpDebug.showStats() - 요청 통계 보기
- httpDebug.clearRequests() - 요청 기록 초기화
- httpDebug.toggleLogging() - 로깅 활성화/비활성화

💡 팁: Network 탭을 열고 앱을 사용하면 실제 HTTP 요청을 확인할 수 있습니다!
    `);
  }, []);

  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/library" element={
            <ProtectedRoute>
              <AssetLibrary />
            </ProtectedRoute>
          } />
          <Route path="/insights" element={
            <ProtectedRoute>
              <InsightTrends />
            </ProtectedRoute>
          } />
          <Route path="/lab" element={
            <ProtectedRoute>
              <PrototypeLab />
            </ProtectedRoute>
          } />
          <Route path="/chatbot" element={
            <ProtectedRoute>
              <Chatbot />
            </ProtectedRoute>
          } />
          <Route path="/profile" element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          } />
          <Route path="/workspace" element={
            <ProtectedRoute>
              <MyWorkspace />
            </ProtectedRoute>
          } />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
