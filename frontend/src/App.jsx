import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import scopiaLogo from './assets/scopia-grey-favicon.png'

import LoginScreen from "./components/Screens/LoginScreen.jsx";
import GalleryScreen from "./components/Screens/GalleryScreen.jsx";
import HomeScreen from "./components/Screens/HomeScreen.jsx";
// import UploadScreen from "./components/Screens/UploadScreen.jsx";
import ArchiveScreen from "./components/Screens/ArchiveScreen.jsx";
import CluesScreen from "./components/Screens/CluesScreen.jsx";
import CaseControlScreen from "./components/Screens/CaseControlScreen.jsx";
import SettingsScreen from "./components/Screens/SettingsScreen.jsx"; 
import ProfileScreen from "./components/Screens/ProfileScreen.jsx"; // might delete later if no use
import GraphScreen from "./components/Screens/GraphScreen.jsx";
import CaseScreen from "./components/Screens/CaseScreen.jsx";
import StudioScreen from "./components/Screens/StudioScreen.jsx";

// import TeamsTable from "./components/Tables/TeamsTable.jsx";
// import CluesTable from "./components/Tables/CluesTable.jsx";
// import UserSelector from "./components/Selectors/UserSelector.jsx";
// import Graph from "./components/Graphs/Graph.jsx";
import CaseSideBar from "./components/Bars/CaseSideBar.jsx";
import CaseLayout from './components/Layouts/CaseLayout.jsx';
import HomeLayout from './components/Layouts/HomeLayout.jsx';
import ChatbotScreen from './components/Screens/ChatbotScreen.jsx';
import CatalogScreen from './components/Screens/CatalogScreen.jsx'; 
import HomeSideBar from './components/Bars/HomeSideBar.jsx';  

function App() {

  const [selectedUserId, setSelectedUserId] = useState(null);

  return (
    <div className="App">
          <Router>
            <div>
                <Routes>
                    <Route index element={<Navigate to="/login" replace />} />
                    <Route path="/teams/:caseKey" element={<CaseControlScreen />} /> {/* double check if in sidebar */}
                    <Route path="/login" element={<LoginScreen />} />
                    
                    <Route path="/home" element={<HomeLayout />}>
                      <Route index element={<HomeScreen />} />  
                      <Route path="cases" element={<HomeScreen />} />
                      <Route path="archive" element={<ArchiveScreen />} />
                      <Route path="catalog" element={<CatalogScreen />} />
                      <Route path="settings" element={<SettingsScreen />} />
                      <Route path="ai" element={<ChatbotScreen />} />
                    </Route>

                    
                    {/* To delete later, for testing */}
                    {/* <Route path="/selector" element={<UserSelector assignerStatus="admin" value={selectedUserId}  onChange={setSelectedUserId} />} /> */}
                    <Route path="/homesidebar" element={<HomeSideBar />} />
                    <Route path="/casesidebar" element={<CaseSideBar />} />

                    <Route path="/case/:caseKey" element={<CaseLayout />}>
                      <Route index element={<CaseScreen />} /> 
                      <Route path="info" element={<CaseScreen />} /> 
                      <Route path="clues" element={<CluesScreen />} />
                      <Route path="gallery" element={<GalleryScreen />} /> {/* with upload */}
                      <Route path="studio" element={<StudioScreen />} />
                      <Route path="graph" element={<GraphScreen />} />
                    </Route>
                </Routes>
            </div>
          </Router>
    </div>
  )
}

export default App
