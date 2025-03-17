// frontend/src/components/AddReservationForm.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../config';

function AddReservationForm({ onSuccess, onCancel }) {
  const [formData, setFormData] = useState({
    user_id: '',
    room_id: '',
    check_in: '',
    check_out: '',
    number_of_guests: 1,
    special_requests: ''
  });
  const [users, setUsers] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [error, setError] = useState('');

  // Fetch users and rooms for dropdowns
  useEffect(() => {
    const fetchData = async () => {
      const token = localStorage.getItem('token');
      
      try {
        // Fetch users
        const usersResponse = await axios.get(`${API_URL}/users`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        // Fetch available rooms
        const roomsResponse = await axios.get(`${API_URL}/rooms`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        setUsers(Array.isArray(usersResponse.data) ? usersResponse.data : []);
        setRooms(Array.isArray(roomsResponse.data) ? roomsResponse.data : []);
      } catch (err) {
        console.error('Error fetching form data:', err);
        setError('Failed to load users and rooms data');
      } finally {
        setLoadingData(false);
      }
    };
    
    fetchData();
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    const token = localStorage.getItem('token');
    
    try {
      const response = await axios.post(
        `${API_URL}/reservations`,
        formData,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      onSuccess(response.data);
    } catch (err) {
      console.error('Error creating reservation:', err);
      setError(err.response?.data?.detail || 'Failed to create reservation');
    } finally {
      setLoading(false);
    }
  };

  if (loadingData) {
    return (
      <div className="animate-pulse p-4">
        <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
        <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
        <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
      </div>
    );
  }

  return (
    <div className="bg-white px-4 pt-5 pb-4 sm:p-6">
      <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
        Create New Reservation
      </h3>
      
      {error && (
        <div className="mb-4 bg-red-50 p-4 rounded-md">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="user_id" className="block text-sm font-medium text-gray-700">Guest</label>
          <select
            id="user_id"
            name="user_id"
            value={formData.user_id}
            onChange={handleInputChange}
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            required
          >
            <option value="">Select a guest</option>
            {users.map(user => (
              <option key={user.id} value={user.id}>
                {user.first_name} {user.last_name} ({user.email})
              </option>
            ))}
          </select>
        </div>
        
        <div>
          <label htmlFor="room_id" className="block text-sm font-medium text-gray-700">Room</label>
          <select
            id="room_id"
            name="room_id"
            value={formData.room_id}
            onChange={handleInputChange}
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            required
          >
            <option value="">Select a room</option>
            {rooms.map(room => (
              <option key={room.id} value={room.id}>
                Room {room.room_number} - {room.room_type} ({room.max_occupancy} guests)
              </option>
            ))}
          </select>
        </div>
        
        <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-2">
          <div>
            <label htmlFor="check_in" className="block text-sm font-medium text-gray-700">Check-in Date/Time</label>
            <input
              type="datetime-local"
              id="check_in"
              name="check_in"
              value={formData.check_in}
              onChange={handleInputChange}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              required
            />
          </div>
          
          <div>
            <label htmlFor="check_out" className="block text-sm font-medium text-gray-700">Check-out Date/Time</label>
            <input
              type="datetime-local"
              id="check_out"
              name="check_out"
              value={formData.check_out}
              onChange={handleInputChange}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              required
            />
          </div>
        </div>
        
        <div>
          <label htmlFor="number_of_guests" className="block text-sm font-medium text-gray-700">Number of Guests</label>
          <input
            type="number"
            id="number_of_guests"
            name="number_of_guests"
            min="1"
            max="10"
            value={formData.number_of_guests}
            onChange={handleInputChange}
            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            required
          />
        </div>
        
        <div>
          <label htmlFor="special_requests" className="block text-sm font-medium text-gray-700">Special Requests</label>
          <textarea
            id="special_requests"
            name="special_requests"
            rows="3"
            value={formData.special_requests}
            onChange={handleInputChange}
            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          ></textarea>
        </div>
        
        <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
          <button
            type="submit"
            className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:col-start-2 sm:text-sm"
            disabled={loading}
          >
            {loading ? 'Creating...' : 'Create Reservation'}
          </button>
          <button
            type="button"
            className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:col-start-1 sm:text-sm"
            onClick={onCancel}
            disabled={loading}
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

export default AddReservationForm;
