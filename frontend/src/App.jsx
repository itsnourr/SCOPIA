import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

import LoginScreen from "./components/Screens/LoginScreen.jsx";
import CaseScreen from "./components/Screens/CaseScreen.jsx";
import HomeScreen from "./components/Screens/HomeScreen.jsx";
import UploadScreen from "./components/Screens/UploadScreen.jsx";

function App() {

  return (
    <div className="App">
          <Router>
            <div>
                <Routes>
                    <Route index element={<Navigate to="/login" replace />} />
                    <Route path="/login" element={<LoginScreen />} />
                    <Route path="/cases" element={<HomeScreen />} />
                    <Route path="/cases/:id" element={<CaseScreen />} />
                    <Route path="/upload" element={<UploadScreen />} />
                </Routes>
            </div>
          </Router>
    </div>
  )
}

export default App
