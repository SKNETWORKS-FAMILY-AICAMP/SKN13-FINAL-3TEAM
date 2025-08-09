import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import Login from './pages/Login';
import Signup from './pages/Signup';
import AssetLibrary from './pages/AssetLibrary';
import InsightTrends from './pages/InsightTrends';
import PrototypeLab from './pages/PrototypeLab';
import Chatbot from './pages/Chatbot';
import './App.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/library" element={<AssetLibrary />} />
        <Route path="/insights" element={<InsightTrends />} />
        <Route path="/lab" element={<PrototypeLab />} />
        <Route path="/chatbot" element={<Chatbot />} />
      </Routes>
    </Router>
  );
}

export default App;
