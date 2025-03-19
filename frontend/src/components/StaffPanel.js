// frontend/src/components/StaffPanel.js
import React, { useState } from 'react';
import axios from 'axios';
import { API_URL } from '../config';
import DeviceRegistrationsList from './DeviceRegistrationsList';

function StaffPanel({ 
  user, 
  staffData = { hotels: [], rooms: [], users: [] }, 
  onRefreshData,
  onAddUser, 
  onAddHotel, 
  onAddRoom,
  onToggleHotelStatus,
  onToggleRoomStatus
}) {
  const [loading, setLoading] = useState(false);
  const [activeSection, setActiveSection] = useState('users');
  const [error, setError] = useState('');
  const [editingUser, setEditingUser] = useState(null);
  const [processingUser, setProcessingUser] = useState(null);
  const [processingHotel, setProcessingHotel] = useState(null);
  const [processingRoom, setProcessingRoom] = useState(null);
  
  // Form state for user editing
  const [editForm, setEditForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    role: 'guest',
    is_active: true
  });

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    return new Date(dateString).toLocaleDateString(undefined, options);
  };

  const handleToggleUserActive = async (userId, currentStatus) => {
    setProcessingUser(userId);
    const token = localStorage.getItem('token');
    
    try {
      // Call the API to update user status
      await axios.put(
        `${API_URL}/users/${userId}`,
        { is_active: !currentStatus },
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      
      // Show success message
      alert(`User ${!currentStatus ? 'activated' : 'deactivated'} successfully`);
      
      // Refresh the data
      if (onRefreshData) onRefreshData();
    } catch (err) {
      console.error('Error updating user:', err);
      alert(`Failed to ${currentStatus ? 'deactivate' : 'activate'} user: ${err.response?.data?.detail || err.message}`);
    } finally {
      setProcessingUser(null);
    }
  };

  const handleEditUser = (userData) => {
    setEditingUser(userData.id);
    setEditForm({
      first_name: userData.first_name || '',
      last_name: userData.last_name || '',
      email: userData.email || '',
      role: userData.role || 'guest',
      is_active: userData.is_active
    });
  };

  const handleCancelEdit = () => {
    setEditingUser(null);
  };

  const handleEditFormChange = (e) => {
    const { name, value, type, checked } = e.target;
    setEditForm({
      ...editForm,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  const handleSaveUser = async () => {
    if (!editingUser) return;
    
    setProcessingUser(editingUser);
    const token = localStorage.getItem('token');
    
    try {
      // Call the API to update user
      await axios.put(
        `${API_URL}/users/${editingUser}`,
        editForm,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      
      // Reset editing state
      setEditingUser(null);
      
      // Show success message
      alert('User updated successfully');
      
      // Refresh the data
      if (onRefreshData) onRefreshData();
    } catch (err) {
      console.error('Error updating user:', err);
      alert(`Failed to update user: ${err.response?.data?.detail || err.message}`);
    } finally {
      setProcessingUser(null);
    }
  };

  const handleHotelStatusToggle = async (hotelId, currentStatus) => {
    setProcessingHotel(hotelId);
    try {
      if (onToggleHotelStatus) {
        await onToggleHotelStatus(hotelId, currentStatus);
      }
    } finally {
      setProcessingHotel(null);
    }
  };

  const handleRoomStatusToggle = async (roomId, currentStatus) => {
    setProcessingRoom(roomId);
    try {
      if (onToggleRoomStatus) {
        await onToggleRoomStatus(roomId, currentStatus);
      }
    } finally {
      setProcessingRoom(null);
    }
  };

  const { hotels, rooms, users } = staffData;

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
            onClick={onRefreshData} 
            className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
          >
            Refresh
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
          <button
            className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${
              activeSection === 'devices'
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } mx-6`}
            onClick={() => setActiveSection('devices')}
          >
            Device Registrations
          </button>
        </nav>
      </div>
      
      <div className="p-4">
        {activeSection === 'users' && (
          <div>
            <div className="mb-4 flex justify-between items-center">
              <h2 className="text-lg font-medium text-gray-900">User Management</h2>
              {user.role === 'admin' && (
                <button
                  onClick={onAddUser}
                  className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  <svg className="h-4 w-4 mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  Add User
                </button>
              )}
            </div>
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
                    users.map((userItem) => (
                      <tr key={userItem.id}>
                        {editingUser === userItem.id ? (
                          // Edit User Form
                          <>
                            <td className="px-6 py-4 whitespace-nowrap" colSpan={3}>
                              <div className="grid grid-cols-1 gap-y-2 sm:grid-cols-2 sm:gap-x-4">
                                <div>
                                  <label htmlFor="first_name" className="block text-xs font-medium text-gray-700">First Name</label>
                                  <input
                                    type="text"
                                    id="first_name"
                                    name="first_name"
                                    value={editForm.first_name}
                                    onChange={handleEditFormChange}
                                    className="mt-1 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                                  />
                                </div>
                                <div>
                                  <label htmlFor="last_name" className="block text-xs font-medium text-gray-700">Last Name</label>
                                  <input
                                    type="text"
                                    id="last_name"
                                    name="last_name"
                                    value={editForm.last_name}
                                    onChange={handleEditFormChange}
                                    className="mt-1 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                                  />
                                </div>
                                <div className="sm:col-span-2">
                                  <label htmlFor="email" className="block text-xs font-medium text-gray-700">Email</label>
                                  <input
                                    type="email"
                                    id="email"
                                    name="email"
                                    value={editForm.email}
                                    onChange={handleEditFormChange}
                                    className="mt-1 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                                    disabled
                                  />
                                </div>
                                <div>
                                  <label htmlFor="role" className="block text-xs font-medium text-gray-700">Role</label>
                                  <select
                                    id="role"
                                    name="role"
                                    value={editForm.role}
                                    onChange={handleEditFormChange}
                                    className="mt-1 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                                  >
                                    <option value="guest">Guest</option>
                                    <option value="hotel_staff">Hotel Staff</option>
                                    <option value="admin">Administrator</option>
                                  </select>
                                </div>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center h-5">
                                <input
                                  id="is_active"
                                  name="is_active"
                                  type="checkbox"
                                  checked={editForm.is_active}
                                  onChange={handleEditFormChange}
                                  className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                                />
                                <label htmlFor="is_active" className="ml-2 text-sm text-gray-700">
                                  Active
                                </label>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                              <button
                                onClick={handleSaveUser}
                                disabled={processingUser === userItem.id}
                                className="text-green-600 hover:text-green-900 mr-3"
                              >
                                {processingUser === userItem.id ? 'Saving...' : 'Save'}
                              </button>
                              <button
                                onClick={handleCancelEdit}
                                disabled={processingUser === userItem.id}
                                className="text-gray-600 hover:text-gray-900"
                              >
                                Cancel
                              </button>
                            </td>
                          </>
                        ) : (
                          // User Display Row
                          <>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm font-medium text-gray-900">
                                {userItem.first_name} {userItem.last_name}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm text-gray-500">{userItem.email}</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm text-gray-500">{userItem.role}</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                userItem.is_active
                                  ? 'bg-green-100 text-green-800'
                                  : 'bg-red-100 text-red-800'
                              }`}>
                                {userItem.is_active ? 'Active' : 'Inactive'}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                              <button 
                                onClick={() => handleEditUser(userItem)}
                                className="text-indigo-600 hover:text-indigo-900 mr-3"
                                disabled={processingUser === userItem.id}
                              >
                                Edit
                              </button>
                              <button 
                                onClick={() => handleToggleUserActive(userItem.id, userItem.is_active)}
                                className={`${
                                  userItem.is_active ? 'text-red-600 hover:text-red-900' : 'text-green-600 hover:text-green-900'
                                }`}
                                disabled={processingUser === userItem.id}
                              >
                                {processingUser === userItem.id ? 'Processing...' : (userItem.is_active ? 'Deactivate' : 'Activate')}
                              </button>
                            </td>
                          </>
                        )}
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
          </div>
        )}
        
        {activeSection === 'hotels' && (
          <div>
            <div className="mb-4 flex justify-between items-center">
              <h2 className="text-lg font-medium text-gray-900">Hotel Management</h2>
              <button
                onClick={onAddHotel}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                <svg className="h-4 w-4 mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                Add Hotel
              </button>
            </div>
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
                          <button 
                            className="text-indigo-600 hover:text-indigo-900 mr-3"
                          >
                            Edit
                          </button>
                          <button 
                            onClick={() => handleHotelStatusToggle(hotel.id, hotel.is_active)}
                            className={`${
                              hotel.is_active ? 'text-red-600 hover:text-red-900' : 'text-green-600 hover:text-green-900'
                            }`}
                            disabled={processingHotel === hotel.id}
                          >
                            {processingHotel === hotel.id ? 'Processing...' : 
                             (hotel.is_active ? 'Deactivate' : 'Activate')}
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
          </div>
        )}
        
        {activeSection === 'rooms' && (
          <div>
            <div className="mb-4 flex justify-between items-center">
              <h2 className="text-lg font-medium text-gray-900">Room Management</h2>
              <button
                onClick={onAddRoom}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                <svg className="h-4 w-4 mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                Add Room
              </button>
            </div>
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
                          <button 
                            className="text-indigo-600 hover:text-indigo-900 mr-3"
                          >
                            Edit
                          </button>
                          <button 
                            onClick={() => handleRoomStatusToggle(room.id, room.is_active)}
                            className={`${
                              room.is_active ? 'text-red-600 hover:text-red-900' : 'text-green-600 hover:text-green-900'
                            }`}
                            disabled={processingRoom === room.id}
                          >
                            {processingRoom === room.id ? 'Processing...' : 
                             (room.is_active ? 'Deactivate' : 'Activate')}
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
          </div>
        )}

        {activeSection === 'devices' && (
          <div className="mt-4">
            <DeviceRegistrationsList />
          </div>
        )}
      </div>
    </div>
  );
}

export default StaffPanel;
