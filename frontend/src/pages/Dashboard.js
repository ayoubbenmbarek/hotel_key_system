import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import ReservationList from '../components/ReservationList';
import DigitalKeyList from '../components/DigitalKeyList';
import UserProfile from '../components/UserProfile';
import StaffPanel from '../components/StaffPanel';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const API_URL = process.env.REACT_APP_API_URL || 'https://8f35-2a01-e0a-159-2b50-59fa-aa12-df1c-1016.ngrok-free.app/api/v1';

function Dashboard() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('reservations');
  const [reservations, setReservations] = useState([]);
  const [digitalKeys, setDigitalKeys] = useState([]);
  const [reservationsLoading, setReservationsLoading] = useState(false);
  const [keysLoading, setKeysLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }

    const fetchUserData = async () => {
      try {
        const response = await axios.get(`${API_URL}/users/me`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        setUser(response.data);
        
        // Fetch initial data based on user role
        if (response.data.role === 'guest') {
          fetchUserReservations();
          fetchUserKeys();
        } else if (['admin', 'hotel_staff'].includes(response.data.role)) {
          fetchAllReservations();
          fetchAllKeys();
        }
        
      } catch (err) {
        console.error('Error fetching user data:', err);
        if (err.response?.status === 401) {
          toast.error('Session expired. Please log in again.');
          localStorage.removeItem('token');
          navigate('/login');
        } else {
          toast.error('Failed to load user data. Please try again.');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, [navigate]);

  const fetchUserReservations = async () => {
    setReservationsLoading(true);
    const token = localStorage.getItem('token');
    
    try {
      const response = await axios.get(`${API_URL}/reservations`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setReservations(response.data);
    } catch (err) {
      console.error('Error fetching reservations:', err);
      toast.error('Failed to load reservations');
    } finally {
      setReservationsLoading(false);
    }
  };

  const fetchUserKeys = async () => {
    setKeysLoading(true);
    const token = localStorage.getItem('token');
    
    try {
      // First get user's reservations if they haven't been loaded
      let userReservations = reservations;
      if (userReservations.length === 0) {
        const reservationsResponse = await axios.get(`${API_URL}/reservations`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        userReservations = reservationsResponse.data;
      }
      
      // Then get keys for each reservation
      const keys = [];
      for (const reservation of userReservations) {
        const keysResponse = await axios.get(`${API_URL}/keys?reservation_id=${reservation.id}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        keys.push(...keysResponse.data);
      }
      
      setDigitalKeys(keys);
    } catch (err) {
      console.error('Error fetching keys:', err);
      toast.error('Failed to load digital keys');
    } finally {
      setKeysLoading(false);
    }
  };

  const fetchAllReservations = async () => {
    setReservationsLoading(true);
    const token = localStorage.getItem('token');
    
    try {
      const response = await axios.get(`${API_URL}/reservations`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setReservations(response.data);
    } catch (err) {
      console.error('Error fetching all reservations:', err);
      toast.error('Failed to load reservations');
    } finally {
      setReservationsLoading(false);
    }
  };

  const fetchAllKeys = async () => {
    setKeysLoading(true);
    const token = localStorage.getItem('token');
    
    try {
      const response = await axios.get(`${API_URL}/keys`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setDigitalKeys(response.data);
    } catch (err) {
      console.error('Error fetching all keys:', err);
      toast.error('Failed to load digital keys');
    } finally {
      setKeysLoading(false);
    }
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

  const handleExtendKey = async (keyId, newEndDate) => {
    const token = localStorage.getItem('token');
    
    try {
      await axios.patch(`${API_URL}/keys/${keyId}/extend`, 
        { new_end_date: newEndDate },
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
      // This endpoint is not in the original API, but would be useful
      await axios.post(`${API_URL}/keys/${keyId}/send-email`, {}, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      toast.success('Key email sent successfully');
    } catch (err) {
      console.error('Error sending key email:', err);
      toast.error('Failed to send key email');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
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
                setUser={setUser}
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
