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
import AddReservationForm from '../components/AddReservationForm';
import AddUserForm from '../components/AddUserForm';
import AddHotelForm from '../components/AddHotelForm';
import AddRoomForm from '../components/AddRoomForm';
import { API_URL } from '../config';

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
  const [showAddUser, setShowAddUser] = useState(false);
  const [showAddReservation, setShowAddReservation] = useState(false);
  const [showAddHotel, setShowAddHotel] = useState(false);
  const [showAddRoom, setShowAddRoom] = useState(false);
  const [staffData, setStaffData] = useState({
    hotels: [],
    rooms: [],
    users: []
  });
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

  const fetchStaffData = useCallback(async () => {
    if (!user || !['admin', 'hotel_staff'].includes(user.role)) return;
    
    const token = localStorage.getItem('token');
    if (!token) return;
    
    try {
      // Fetch hotels
      const hotelsResponse = await axios.get(`${API_URL}/hotels`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const hotels = extractArrayData(hotelsResponse.data);
      
      // Fetch rooms
      const roomsResponse = await axios.get(`${API_URL}/rooms`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const rooms = extractArrayData(roomsResponse.data);
      
      // Fetch users (admin only)
      let users = [];
      if (user.role === 'admin') {
        const usersResponse = await axios.get(`${API_URL}/users`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        users = extractArrayData(usersResponse.data);
      }
      
      setStaffData({
        hotels,
        rooms,
        users
      });
      
    } catch (err) {
      console.error('Error fetching staff data:', err);
      toast.error('Failed to load staff data: ' + (err.response?.data?.detail || err.message));
    }
  }, [user, extractArrayData]);

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
        fetchStaffData();
      }
    }
  }, [user, fetchUserReservations, fetchUserKeys, fetchAllReservations, fetchAllKeys, fetchStaffData]);

  // Update the user state when UserProfile makes changes
  const handleUserUpdate = (updatedUser) => {
    setUser(updatedUser);
    persistUserData(updatedUser); // Save to localStorage
  };

  const handleCreateKey = async (
    reservationId, 
    passType, 
    sendEmail, 
    alternativeEmail = null, 
  ) => {
    const token = localStorage.getItem('token');
    
    try {
      const payload = {
        reservation_id: reservationId,
        pass_type: passType,
        send_email: sendEmail
      };

      // Add optional parameters if they exist
      if (alternativeEmail) {
        payload.alternative_email = alternativeEmail;
      }
      
      const response = await axios.post(
        `${API_URL}/keys`, 
        payload,
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
      
      // Preserve the user's intended local time by including time zone offset
      // This will correctly communicate the intended local time to the server
      const localISOString = new Date(
        dateObj.getTime() - dateObj.getTimezoneOffset() * 60000
      ).toISOString().slice(0, 19) + 'Z';
      
      console.log(`Extending key ${keyId} to new end date/time: ${localISOString}`);
      console.log(`Original date-time input: ${newEndDateTime}`);
      
      await axios.patch(`${API_URL}/keys/${keyId}/extend`, 
        { new_end_date: localISOString },
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

  const handleSendKeyEmail = async (keyId, alternativeEmail = null) => {
    const token = localStorage.getItem('token');
    
    try {
      // Prepare payload
      const payload = {};
      if (alternativeEmail) {
        payload.alternative_email = alternativeEmail;
      }

      console.log(`Sending key email for key ${keyId}${alternativeEmail ? ' to ' + alternativeEmail : ''}`);

      // Send request
      try {
        await axios.post(`${API_URL}/keys/${keyId}/send-email`, payload, {
          headers: { 
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        
        toast.success(`Key email sent successfully${alternativeEmail ? ' to ' + alternativeEmail : ''}`);
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

  const handleSendKeySMS = async (keyId, phoneNumbers) => {
    const token = localStorage.getItem('token');
    
    if (!phoneNumbers || phoneNumbers.length === 0) {
      toast.error('No phone numbers provided');
      return;
    }
    
    try {
      console.log('Sending SMS to numbers:', phoneNumbers);
      
      await axios.post(  // Remove the 'response =' part
        `${API_URL}/keys/${keyId}/send-sms`, 
        phoneNumbers,
        {
          headers: { 
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      toast.success('Key SMS sent successfully');
    } catch (err) {
      console.error('Error sending key SMS:', err);
      toast.error('Failed to send key SMS: ' + (err.response?.data?.detail || err.message));
      throw err;
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    // Don't remove userData on logout so it's available next time
    navigate('/login');
  };

  // Handle adding a new user
  const handleAddUser = (newUser) => {
    toast.success('User created successfully');
    setShowAddUser(false);
    
    // Refresh the data
    fetchStaffData();
  };

  // Handle adding a new reservation
  const handleAddReservation = (newReservation) => {
    toast.success('Reservation created successfully');
    setShowAddReservation(false);
    
    // Refresh the reservations list
    fetchAllReservations();
  };

  // Handle adding a new hotel
  const handleAddHotel = (newHotel) => {
    toast.success('Hotel created successfully');
    setShowAddHotel(false);
    
    // Refresh the staff data
    fetchStaffData();
  };

  // Handle adding a new room
  const handleAddRoom = (newRoom) => {
    toast.success('Room created successfully');
    setShowAddRoom(false);
    
    // Refresh the staff data
    fetchStaffData();
  };

  // Handle updating hotel status
  const handleToggleHotelStatus = async (hotelId, currentStatus) => {
    const token = localStorage.getItem('token');
    
    try {
      // Call API to update hotel status
      await axios.put(
        `${API_URL}/hotels/${hotelId}`,
        { is_active: !currentStatus },
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      
      toast.success(`Hotel ${currentStatus ? 'deactivated' : 'activated'} successfully`);
      
      // Refresh staff data
      fetchStaffData();
    } catch (err) {
      console.error('Error updating hotel status:', err);
      toast.error(`Failed to ${currentStatus ? 'deactivate' : 'activate'} hotel: ${err.response?.data?.detail || err.message}`);
    }
  };

  // Handle updating room status
  const handleToggleRoomStatus = async (roomId, currentStatus) => {
    const token = localStorage.getItem('token');
    
    try {
      // Call API to update room status
      await axios.delete(
        `${API_URL}/rooms/${roomId}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      
      toast.success(`Room ${currentStatus ? 'deactivated' : 'activated'} successfully`);
      
      // Refresh staff data
      fetchStaffData();
    } catch (err) {
      console.error('Error updating room status:', err);
      toast.error(`Failed to ${currentStatus ? 'deactivate' : 'activate'} room: ${err.response?.data?.detail || err.message}`);
    }
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
                onAddReservation={() => setShowAddReservation(true)}
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
                onSendSMS={handleSendKeySMS}
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
                staffData={staffData}
                onRefreshData={fetchStaffData}
                onAddUser={() => setShowAddUser(true)}
                onAddHotel={() => setShowAddHotel(true)}
                onAddRoom={() => setShowAddRoom(true)}
                onToggleHotelStatus={handleToggleHotelStatus}
                onToggleRoomStatus={handleToggleRoomStatus}
              />
            )}
          </div>
        </main>
      </div>

      {/* Add User Modal */}
      {showAddUser && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <AddUserForm 
                onSuccess={handleAddUser} 
                onCancel={() => setShowAddUser(false)} 
              />
            </div>
          </div>
        </div>
      )}

      {/* Add Reservation Modal */}
      {showAddReservation && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <AddReservationForm 
                onSuccess={handleAddReservation} 
                onCancel={() => setShowAddReservation(false)} 
              />
            </div>
          </div>
        </div>
      )}

      {/* Add Hotel Modal */}
      {showAddHotel && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <AddHotelForm 
                onSuccess={handleAddHotel} 
                onCancel={() => setShowAddHotel(false)} 
              />
            </div>
          </div>
        </div>
      )}

      {/* Add Room Modal */}
      {showAddRoom && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <AddRoomForm 
                onSuccess={handleAddRoom} 
                onCancel={() => setShowAddRoom(false)} 
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
