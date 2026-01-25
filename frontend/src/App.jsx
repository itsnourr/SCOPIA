import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

import LoginScreen from "./components/Screens/LoginScreen.jsx";
import CaseScreen from "./components/Screens/GalleryScreen.jsx";
import HomeScreen from "./components/Screens/HomeScreen.jsx";
import UploadScreen from "./components/Screens/UploadScreen.jsx";
import ArchiveScreen from "./components/Screens/ArchiveScreen.jsx";
import CluesScreen from "./components/Screens/CluesScreen.jsx";
import CaseControlScreen from "./components/Screens/CaseControlScreen.jsx";
import SettingsScreen from "./components/Screens/SettingsScreen.jsx"; 
import ProfileScreen from "./components/Screens/ProfileScreen.jsx"; // might delete later if no use
import GraphScreen from "./components/Screens/GraphScreen.jsx";
import GalleryScreen from "./components/Screens/CaseScreen.jsx";
import StudioScreen from "./components/Screens/StudioScreen.jsx";

import TeamsTable from "./components/Tables/TeamsTable.jsx";
import CluesTable from "./components/Tables/CluesTable.jsx";
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
                    <Route path="/cases/:caseKey" element={<CaseScreen />} /> 
                    <Route path="/clues/:caseKey" element={<CluesScreen />} />
                    <Route path="/control/:caseKey" element={<CaseControlScreen />} />
                    <Route path="/gallery/:id" element={<GalleryScreen />} /> {/* TODO Replace id by caseKey */}
                    <Route path="/graph" element={<GraphScreen />} /> {/* TODO add /:caseKey */}
                    <Route path="/login" element={<LoginScreen />} />
                    <Route path="/settings" element={<SettingsScreen />} />
                    <Route path="/studio/:caseKey" element={<StudioScreen />} />
                    <Route path="/teams" element={<CluesTable />} />
                    <Route path="/upload/:caseKey" element={<UploadScreen />} />

                    {/* To delete later, for testing */}
                    <Route path="/selector" element={<UserSelector assignerStatus="admin" value={selectedUserId}  onChange={setSelectedUserId} />} />
                  
                </Routes>
            </div>
          </Router>
    </div>
  )
}

export default App
