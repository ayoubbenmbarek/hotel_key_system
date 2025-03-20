// src/App.js - Updated to include password reset route
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import NotFound from './pages/NotFound';
import NFCSimulatorPage from './pages/NFCSimulatorPage';
import PasswordResetForm from './components/PasswordResetForm';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/reset-password" element={<PasswordResetForm />} />
        <Route path="/" element={<Dashboard />} />
        <Route path="/nfc-simulator" element={<NFCSimulatorPage />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Router>
  );
}

export default App;
