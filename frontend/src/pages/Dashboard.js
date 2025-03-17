// frontend/src/pages/Dashboard.js
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import ReservationList from '../components/ReservationList';
import DigitalKeyList from '../components/DigitalKeyList';
import UserProfile from '../components/UserProfile';
import StaffPanel from '../components/StaffPanel';
import { API_URL } from '../config';

// Install react-toastify
// npm install react-toastify
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

function Dashboard() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('reservations');
  const [reservations, setReservations] = useState([]);
  const [digitalKeys, setDigitalKeys] = useState([]);
  const [reservationsLoading, setReservationsLoading] = useState(false);
  const [keysLoading, setKeysLoading] = useState(false);
  const navigate = useNavigate();
  
  // Use refs to prevent infinite request loops
  const initialDataLoaded = useRef(false);
  const initialUserLoaded = useRef(false);

  // Helper function to extract array data from various API response formats
  const extractArrayData = useCallback((data) => {
    // If it's already an array, return it
    if (Array.isArray(data)) {
      return data;
    }
    
    // If it's an object, try to find an array property
    if (data && typeof data === 'object') {
      // Common API response formats
      if (data.data && Array.isArray(data.data)) {
        return data.data;
      }
      if (data.results && Array.isArray(data.results)) {
        return data.results;
      }
      if (data.items && Array.isArray(data.items)) {
        return data.items;
      }
      if (data.content && Array.isArray(data.content)) {
        return data.content;
      }
      if (data.result && Array.isArray(data.result)) {
        return data.result;
      }
      
      // Check if it's a single object that should be in an array
      if (data.id !== undefined) {
        return [data];
      }
    }
    
    // If all else fails, return empty array
    return [];
  }, []);

  const fetchUserReservations = useCallback(async () => {
    setReservationsLoading(true);
    const token = localStorage.getItem('token');
    
    try {
      const response = await axios.get(`${API_URL}/reservations`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      // Extract array data from the response
      const reservationsData = extractArrayData(response.data);
      setReservations(reservationsData);
      
      if (reservationsData.length === 0) {
        toast.info('No reservations found');
      }
    } catch (err) {
      console.error('Error fetching reservations:', err);
      toast.error('Failed to load reservations: ' + (err.response?.data?.detail || err.message));
      setReservations([]);
    } finally {
      setReservationsLoading(false);
    }
  }, [extractArrayData]);

  const fetchUserKeys = useCallback(async () => {
    setKeysLoading(true);
    const token = localStorage.getItem('token');
    
    try {
      // First get user's reservations if they haven't been loaded
      let userReservations = reservations;
      if (!userReservations || userReservations.length === 0) {
        const reservationsResponse = await axios.get(`${API_URL}/reservations`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        userReservations = extractArrayData(reservationsResponse.data);
      }
      
      // Then get keys for each reservation
      const keys = [];
      if (userReservations && userReservations.length > 0) {
        for (const reservation of userReservations) {
          try {
            const keysResponse = await axios.get(`${API_URL}/keys?reservation_id=${reservation.id}`, {
              headers: { 'Authorization': `Bearer ${token}` }
            });
            const reservationKeys = extractArrayData(keysResponse.data);
            keys.push(...reservationKeys);
          } catch (keyError) {
            console.error(`Error fetching keys for reservation ${reservation.id}:`, keyError);
          }
        }
      }
      
      // If no keys found via reservations, try direct approach
      if (keys.length === 0) {
        const allKeysResponse = await axios.get(`${API_URL}/keys`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const allKeys = extractArrayData(allKeysResponse.data);
        keys.push(...allKeys);
      }
      
      setDigitalKeys(keys);
      
      if (keys.length === 0) {
        toast.info('No digital keys found');
      }
    } catch (err) {
      console.error('Error fetching keys:', err);
      toast.error('Failed to load digital keys: ' + (err.response?.data?.detail || err.message));
      setDigitalKeys([]);
    } finally {
      setKeysLoading(false);
    }
  }, [extractArrayData, reservations]);

  const fetchAllReservations = useCallback(async () => {
    fetchUserReservations(); // Reuse the same function for simplicity
  }, [fetchUserReservations]);

  const fetchAllKeys = useCallback(async () => {
    fetchUserKeys(); // Reuse the same function for simplicity
  }, [fetchUserKeys]);

  // Persist user data in local storage
  const persistUserData = useCallback((userData) => {
    if (userData) {
      localStorage.setItem('userData', JSON.stringify(userData));
    }
  }, []);

  // Load user data from local storage
  const loadUserData = useCallback(() => {
    const savedUserData = localStorage.getItem('userData');
    if (savedUserData) {
      try {
        return JSON.parse(savedUserData);
      } catch (e) {
        console.error('Error parsing saved user data:', e);
        return null;
      }
    }
    return null;
  }, []);

  // Initial data load effect - only runs once
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }

    // Try to load user from localStorage first for faster initial render
    const savedUser = loadUserData();
    if (savedUser) {
      setUser(savedUser);
      setLoading(false);
    }

    // Only fetch user data once
    if (!initialUserLoaded.current) {
      initialUserLoaded.current = true;
      
      const fetchUserData = async () => {
        try {
          const response = await axios.get(`${API_URL}/users/me`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          
          // Handle potential nested data response
          const userData = response.data?.data || response.data;
          setUser(userData);
          
          // Save user data to local storage
          persistUserData(userData);
          
        } catch (err) {
          console.error('Error fetching user data:', err);
          if (err.response?.status === 401) {
            toast.error('Session expired. Please log in again.');
            localStorage.removeItem('token');
            localStorage.removeItem('userData');
            navigate('/login');
          } else {
            toast.error('Failed to load user data. Please try again.');
          }
        } finally {
          setLoading(false);
        }
      };

      fetchUserData();
    }
  }, [navigate, persistUserData, loadUserData]);

  // Load initial data based on user role - only runs once when user is loaded
  useEffect(() => {
    // Only fetch data once after user is loaded
    if (user && !initialDataLoaded.current) {
      initialDataLoaded.current = true;
      
      if (user.role === 'guest') {
        fetchUserReservations();
        fetchUserKeys();
      } else if (['admin', 'hotel_staff'].includes(user.role)) {
        fetchAllReservations();
        fetchAllKeys();
      }
    }
  }, [user, fetchUserReservations, fetchUserKeys, fetchAllReservations, fetchAllKeys]);

  // Update the user state when UserProfile makes changes
  const handleUserUpdate = (updatedUser) => {
    setUser(updatedUser);
    persistUserData(updatedUser); // Save to localStorage
  };

  const handleCreateKey = async (reservationId, passType, sendEmail) => {
    const token = localStorage.getItem('token');
    
    try {
      const response = await axios.post(`${API_URL}/keys`, 
        {
          reservation_id: reservationId,
          pass_type: passType,
          send_email: sendEmail
        },
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      
      toast.success('Digital key created successfully');
      
      // Refresh keys list
      if (user.role === 'guest') {
        fetchUserKeys();
      } else {
        fetchAllKeys();
      }
      
      return response.data;
    } catch (err) {
      console.error('Error creating digital key:', err);
      toast.error(err.response?.data?.detail || 'Failed to create digital key');
      throw err;
    }
  };

  const handleActivateKey = async (keyId) => {
    const token = localStorage.getItem('token');
    
    try {
      await axios.patch(`${API_URL}/keys/${keyId}/activate`, {}, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      toast.success('Key activated successfully');
      
      // Refresh keys list
      if (user.role === 'guest') {
        fetchUserKeys();
      } else {
        fetchAllKeys();
      }
    } catch (err) {
      console.error('Error activating key:', err);
      toast.error(err.response?.data?.detail || 'Failed to activate key');
    }
  };

  const handleDeactivateKey = async (keyId) => {
    const token = localStorage.getItem('token');
    
    try {
      await axios.patch(`${API_URL}/keys/${keyId}/deactivate`, {}, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      toast.success('Key deactivated successfully');
      
      // Refresh keys list
      if (user.role === 'guest') {
        fetchUserKeys();
      } else {
        fetchAllKeys();
      }
    } catch (err) {
      console.error('Error deactivating key:', err);
      toast.error(err.response?.data?.detail || 'Failed to deactivate key');
    }
  };
  
  const handleExtendKey = async (keyId, newEndDateTime) => {
    const token = localStorage.getItem('token');
    
    try {
      // Parse the input date/time
      const dateObj = new Date(newEndDateTime);
      
      // Use ISO string which includes milliseconds and timezone
      // This creates a format like: 2025-07-15T15:07:00.000Z
      const isoString = dateObj.toISOString();
      
      console.log(`Extending key ${keyId} to new end date/time (ISO): ${isoString}`);
      
      // Let's also log what the raw date-time input was
      console.log(`Original date-time input: ${newEndDateTime}`);
      
      await axios.patch(`${API_URL}/keys/${keyId}/extend`, 
        { new_end_date: isoString },
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      
      toast.success('Key validity extended successfully');
      
      // Refresh keys list
      if (user.role === 'guest') {
        fetchUserKeys();
      } else {
        fetchAllKeys();
      }
    } catch (err) {
      console.error('Error extending key validity:', err);
      toast.error(err.response?.data?.detail || 'Failed to extend key validity');
    }
  };

  const handleSendKeyEmail = async (keyId) => {
    const token = localStorage.getItem('token');
    
    try {
      // Check if endpoint exists by checking if we get a 404
      try {
        await axios.post(`${API_URL}/keys/${keyId}/send-email`, {}, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        toast.success('Key email sent successfully');
      } catch (err) {
        // If 404, use alternative approach
        if (err.response?.status === 404) {
          console.warn("Key email endpoint not available, using alternative");
          
          // Get the key information first
          const keyResponse = await axios.get(`${API_URL}/keys/${keyId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          
          // Display pass URL to user since the email feature isn't available
          const passUrl = keyResponse.data.pass_url;
          if (passUrl) {
            toast.info(`Email endpoint not available. Please share this pass URL: ${passUrl}`);
          } else {
            toast.error('No pass URL available for this key');
          }
        } else {
          // For other errors, show error message
          console.error('Error sending key email:', err);
          toast.error('Failed to send key email: ' + (err.response?.data?.detail || err.message));
        }
      }
    } catch (err) {
      console.error('Error in handleSendKeyEmail:', err);
      toast.error('Failed to process key email request');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    // Don't remove userData on logout so it's available next time
    navigate('/login');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-100">
      <ToastContainer position="top-right" autoClose={3000} />
      
      {/* Sidebar */}
      <Sidebar 
        user={user} 
        activeTab={activeTab} 
        onTabChange={setActiveTab} 
        onLogout={handleLogout} 
      />
      
      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header user={user} onLogout={handleLogout} />
        
        <main className="flex-1 overflow-y-auto bg-gray-50 p-4">
          <div className="container mx-auto">
            {/* Render content based on active tab */}
            {activeTab === 'reservations' && (
              <ReservationList 
                reservations={reservations} 
                loading={reservationsLoading} 
                onCreateKey={handleCreateKey}
                isStaff={['admin', 'hotel_staff'].includes(user?.role)}
                onRefresh={user?.role === 'guest' ? fetchUserReservations : fetchAllReservations}
              />
            )}
            
            {activeTab === 'keys' && (
              <DigitalKeyList 
                keys={digitalKeys} 
                loading={keysLoading} 
                onActivate={handleActivateKey}
                onDeactivate={handleDeactivateKey}
                onExtend={handleExtendKey}
                onSendEmail={handleSendKeyEmail}
                isStaff={['admin', 'hotel_staff'].includes(user?.role)}
                onRefresh={user?.role === 'guest' ? fetchUserKeys : fetchAllKeys}
              />
            )}
            
            {activeTab === 'profile' && (
              <UserProfile 
                user={user} 
                setUser={handleUserUpdate}
              />
            )}
            
            {activeTab === 'staff' && ['admin', 'hotel_staff'].includes(user?.role) && (
              <StaffPanel 
                user={user} 
                onRefreshReservations={fetchAllReservations}
                onRefreshKeys={fetchAllKeys}
              />
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

export default Dashboard;
