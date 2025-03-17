// frontend/src/components/StaffPanel.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../config';

function StaffPanel({ user, onRefreshReservations, onRefreshKeys }) {
  const [hotels, setHotels] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState('users');
  const [error, setError] = useState('');

  // Fetch staff panel data
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError('');
      const token = localStorage.getItem('token');
      
      // Make sure we have a valid token
      if (!token) {
        setError('Authentication token missing. Please log in again.');
        setLoading(false);
        return;
      }
      
      try {
        console.log('Fetching data for staff panel...');
        // Fetch users (admin only)
        if (user.role === 'admin') {
          console.log('Fetching users...');
          try {
            const usersResponse = await axios.get(`${API_URL}/users`, {
              headers: { 'Authorization': `Bearer ${token}` }
            });
            console.log('Users data:', usersResponse.data);
            setUsers(Array.isArray(usersResponse.data) ? usersResponse.data : []);
          } catch (userErr) {
            console.error('Error fetching users:', userErr);
            // Don't fail the whole component if just user fetching fails
          }
        }
        
        // Fetch hotels
        console.log('Fetching hotels...');
        const hotelsResponse = await axios.get(`${API_URL}/hotels`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        console.log('Hotels data:', hotelsResponse.data);
        setHotels(Array.isArray(hotelsResponse.data) ? hotelsResponse.data : []);
        
        // Fetch rooms
        console.log('Fetching rooms...');
        const roomsResponse = await axios.get(`${API_URL}/rooms`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        console.log('Rooms data:', roomsResponse.data);
        setRooms(Array.isArray(roomsResponse.data) ? roomsResponse.data : []);
        
      } catch (err) {
        console.error('Error fetching staff data:', err);
        setError(`Error loading data: ${err.response?.data?.detail || err.message}`);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [user.role]);

  if (loading) {
    return (
      <div className="bg-white shadow rounded-lg p-4">
        <div className="animate-pulse flex space-x-4">
          <div className="flex-1 space-y-4 py-1">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="space-y-2">
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded w-5/6"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center">
          <div className="text-red-500 mb-4">
            <svg className="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Data</h3>
          <p className="text-gray-500">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
          >
            Refresh Page
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      <div className="px-4 py-5 sm:px-6 border-b">
        <h3 className="text-lg leading-6 font-medium text-gray-900">
          Staff Management Panel
        </h3>
        <p className="mt-1 max-w-2xl text-sm text-gray-500">
          Manage hotels, rooms, and users
        </p>
      </div>
      
      <div className="border-b border-gray-200">
        <nav className="flex -mb-px">
          <button
            className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${
              activeSection === 'users'
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } mx-6`}
            onClick={() => setActiveSection('users')}
          >
            Users
          </button>
          <button
            className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${
              activeSection === 'hotels'
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } mx-6`}
            onClick={() => setActiveSection('hotels')}
          >
            Hotels
          </button>
          <button
            className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${
              activeSection === 'rooms'
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } mx-6`}
            onClick={() => setActiveSection('rooms')}
          >
            Rooms
          </button>
        </nav>
      </div>
      
      <div className="p-4">
        {activeSection === 'users' && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {users && users.length > 0 ? (
                  users.map((user) => (
                    <tr key={user.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {user.first_name} {user.last_name}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-500">{user.email}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-500">{user.role}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          user.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {user.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button className="text-indigo-600 hover:text-indigo-900 mr-3">
                          Edit
                        </button>
                        <button className={`${
                          user.is_active ? 'text-red-600 hover:text-red-900' : 'text-green-600 hover:text-green-900'
                        }`}>
                          {user.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5" className="px-6 py-4 text-center text-sm text-gray-500">
                      {user.role === 'admin' ? 'No users found' : 'Only admins can view user data'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
        
        {activeSection === 'hotels' && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Address
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Contact
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {hotels && hotels.length > 0 ? (
                  hotels.map((hotel) => (
                    <tr key={hotel.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{hotel.name}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-500">
                          {hotel.address}, {hotel.city}, {hotel.state} {hotel.postal_code}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-500">{hotel.phone_number}</div>
                        <div className="text-sm text-gray-500">{hotel.email}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          hotel.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {hotel.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button className="text-indigo-600 hover:text-indigo-900 mr-3">
                          Edit
                        </button>
                        <button className={`${
                          hotel.is_active ? 'text-red-600 hover:text-red-900' : 'text-green-600 hover:text-green-900'
                        }`}>
                          {hotel.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5" className="px-6 py-4 text-center text-sm text-gray-500">
                      No hotels found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
        
        {activeSection === 'rooms' && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Room
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Hotel
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Lock ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {rooms && rooms.length > 0 ? (
                  rooms.map((room) => (
                    <tr key={room.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">Room {room.room_number}</div>
                        <div className="text-sm text-gray-500">Floor {room.floor}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-500">
                          {hotels.find(h => h.id === room.hotel_id)?.name || 'Unknown Hotel'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-500">{room.room_type}</div>
                        <div className="text-sm text-gray-500">Max: {room.max_occupancy} guests</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {room.nfc_lock_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          room.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {room.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button className="text-indigo-600 hover:text-indigo-900 mr-3">
                          Edit
                        </button>
                        <button className={`${
                          room.is_active ? 'text-red-600 hover:text-red-900' : 'text-green-600 hover:text-green-900'
                        }`}>
                          {room.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="6" className="px-6 py-4 text-center text-sm text-gray-500">
                      No rooms found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default StaffPanel;
