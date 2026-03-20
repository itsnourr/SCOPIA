import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import scopiaLogo from './assets/scopia-grey-favicon.png'

import LoginScreen from "./components/Screens/LoginScreen.jsx";
import GalleryScreen from "./components/Screens/GalleryScreen.jsx";
import HomeScreen from "./components/Screens/HomeScreen.jsx";
import ArchiveScreen from "./components/Screens/ArchiveScreen.jsx";
import CluesScreen from "./components/Screens/CluesScreen.jsx";
import TeamsScreen from "./components/Screens/TeamsScreen.jsx";

import SettingsScreen from "./components/Screens/SettingsScreen.jsx"; 
import GraphScreen from "./components/Screens/GraphScreen.jsx";
import CaseScreen from "./components/Screens/CaseScreen.jsx";
import StudioScreen from "./components/Screens/StudioScreen.jsx";
import SuspectsScreen from "./components/Screens/SuspectsScreen.jsx";
import CaseLayout from './components/Layouts/CaseLayout.jsx';
import HomeLayout from './components/Layouts/HomeLayout.jsx';
import ChatbotScreen from './components/Screens/ChatbotScreen.jsx';
import CatalogScreen from './components/Screens/CatalogScreen.jsx'; 
import PipelineScreen from './components/Screens/PipelineScreen.jsx';
import RoverScreen from './components/Screens/RoverScreen.jsx';

function App() {

  const [selectedUserId, setSelectedUserId] = useState(null);

  return (
    <div className="App">
          <Router>
            <div>
                <Routes>
                    <Route index element={<Navigate to="/login" replace />} />
                    <Route path="/login" element={<LoginScreen />} />
                    
                    <Route path="/home" element={<HomeLayout />}>
                      <Route index element={<HomeScreen />} />  
                      <Route path="cases" element={<HomeScreen />} />
                      <Route path="archive" element={<ArchiveScreen />} />
                      <Route path="catalog" element={<CatalogScreen />} />
                      <Route path="settings" element={<SettingsScreen />} />
                      <Route path="teams" element={<TeamsScreen />} />
                      <Route path="ai" element={<ChatbotScreen />} />
                    </Route>

                    <Route path="/case/:caseKey" element={<CaseLayout />}>
                      <Route index element={<CaseScreen />} /> 
                      <Route path="info" element={<CaseScreen />} /> 
                      <Route path="clues" element={<CluesScreen />} />
                      <Route path="suspects" element={<SuspectsScreen />} />
                      <Route path="gallery" element={<GalleryScreen />} /> 
                      <Route path="studio" element={<StudioScreen />} />
                      <Route path="pipeline" element={<PipelineScreen />} />
                      <Route path="rover" element={<RoverScreen />} />
                      <Route path="graph" element={<GraphScreen />} />
                    </Route>
                </Routes>
            </div>
          </Router>
    </div>
  )
}

export default App
