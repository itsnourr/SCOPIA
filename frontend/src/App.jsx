import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

import LoginScreen from "./components/Screens/LoginScreen.jsx";
import CaseScreen from "./components/Screens/CaseScreen.jsx";
import HomeScreen from "./components/Screens/HomeScreen.jsx";
import UploadScreen from "./components/Screens/UploadScreen.jsx";
import ArchiveScreen from "./components/Screens/ArchiveScreen.jsx";
import CluesScreen from "./components/Screens/CluesScreen.jsx";
import CaseControlScreen from "./components/Screens/CaseControlScreen.jsx";
import SettingsScreen from "./components/Screens/SettingsScreen.jsx";
import ProfileScreen from "./components/Screens/ProfileScreen.jsx";
import GraphScreen from "./components/Screens/GraphScreen.jsx";
import CoCustodyScreen from "./components/Screens/CoCustodyScreen.jsx";
import StudioScreen from "./components/Screens/StudioScreen.jsx";

import UserSelector from "./components/Selectors/UserSelector.jsx"

function App() {

  const [selectedUserId, setSelectedUserId] = useState(null);

  return (
    <div className="App">
          <Router>
            <div>
                <Routes>
                    <Route index element={<Navigate to="/login" replace />} />
                    <Route path="/archive" element={<ArchiveScreen />} />
                    <Route path="/cases" element={<HomeScreen />} />
                    <Route path="/cases/:id" element={<CaseScreen />} />
                    <Route path="/clues" element={<CluesScreen />} />
                    <Route path="/control" element={<CaseControlScreen />} />
                    <Route path="/custody" element={<CoCustodyScreen />} />
                    <Route path="/graph" element={<GraphScreen />} />
                    <Route path="/login" element={<LoginScreen />} />
                    <Route path="/profile" element={<ProfileScreen />} />
                    <Route path="/selector" element={<UserSelector assignerStatus="admin" value={selectedUserId}  onChange={setSelectedUserId} />} />
                    <Route path="/studio/:caseKey" element={<StudioScreen />} />
                    <Route path="/upload" element={<UploadScreen />} />
                </Routes>
            </div>
          </Router>
    </div>
  )
}

export default App
