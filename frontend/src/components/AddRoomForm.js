// frontend/src/components/AddRoomForm.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../config';

function AddRoomForm({ onSuccess, onCancel }) {
  const [formData, setFormData] = useState({
    hotel_id: '',
    room_number: '',
    floor: 1,
    room_type: 'standard',
    max_occupancy: 2,
    nfc_lock_id: ''
  });
  const [hotels, setHotels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingHotels, setLoadingHotels] = useState(true);
  const [error, setError] = useState('');

  // Fetch hotels for dropdown
  useEffect(() => {
    const fetchHotels = async () => {
      setLoadingHotels(true);
      const token = localStorage.getItem('token');
      
      try {
        const response = await axios.get(`${API_URL}/hotels`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        // Filter for active hotels only
        const activeHotels = Array.isArray(response.data) 
          ? response.data.filter(hotel => hotel.is_active)
          : [];
        
        setHotels(activeHotels);
        
        // Set default hotel if available
        if (activeHotels.length > 0 && !formData.hotel_id) {
          setFormData(prev => ({ ...prev, hotel_id: activeHotels[0].id }));
        }
      } catch (err) {
        console.error('Error fetching hotels:', err);
        setError('Failed to load hotels. Please try again.');
      } finally {
        setLoadingHotels(false);
      }
    };
    
    fetchHotels();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  // Safely parse and extract error messages from different error formats
  const getErrorMessage = (err) => {
    // Case 1: Error is an array of validation errors
    if (err.response?.data && Array.isArray(err.response.data)) {
      try {
        const messages = err.response.data.map(item => {
          return item.msg || 'Validation error';
        });
        return messages.join('. ');
      } catch (e) {
        return 'Validation error occurred. Please check your inputs.';
      }
    }
    
    // Case 2: Error has a detail field
    if (err.response?.data?.detail) {
      return String(err.response.data.detail);
    }
    
    // Case 3: Error response data is a string
    if (typeof err.response?.data === 'string') {
      return err.response.data;
    }
    
    // Case 4: Error message is available
    if (err.message) {
      return err.message;
    }
    
    // Default fallback
    return 'An error occurred while creating the room';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    const token = localStorage.getItem('token');
    
    try {
      const response = await axios.post(
        `${API_URL}/rooms`,
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
      console.error('Error creating room:', err);
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  if (loadingHotels) {
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
        Create New Room
      </h3>
      
      {error && typeof error === 'string' && (
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
      
      {hotels.length === 0 && (
        <div className="mb-4 bg-yellow-50 p-4 rounded-md">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-yellow-800">
                No hotels available. Please create a hotel first.
              </p>
            </div>
          </div>
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="hotel_id" className="block text-sm font-medium text-gray-700">Hotel</label>
          <select
            id="hotel_id"
            name="hotel_id"
            value={formData.hotel_id}
            onChange={handleInputChange}
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            required
            disabled={hotels.length === 0}
          >
            <option value="">Select a hotel</option>
            {hotels.map(hotel => (
              <option key={hotel.id} value={hotel.id}>
                {hotel.name}
              </option>
            ))}
          </select>
        </div>
        
        <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-2">
          <div>
            <label htmlFor="room_number" className="block text-sm font-medium text-gray-700">Room Number</label>
            <input
              type="text"
              id="room_number"
              name="room_number"
              value={formData.room_number}
              onChange={handleInputChange}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              required
            />
          </div>
          
          <div>
            <label htmlFor="floor" className="block text-sm font-medium text-gray-700">Floor</label>
            <input
              type="number"
              id="floor"
              name="floor"
              value={formData.floor}
              onChange={handleInputChange}
              min="1"
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              required
            />
          </div>
        </div>
        
        <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-2">
          <div>
            <label htmlFor="room_type" className="block text-sm font-medium text-gray-700">Room Type</label>
            <select
              id="room_type"
              name="room_type"
              value={formData.room_type}
              onChange={handleInputChange}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
              required
            >
              <option value="standard">Standard</option>
              <option value="suite">Suite</option>
              <option value="deluxe">Deluxe</option>
              <option value="executive">Executive</option>
              <option value="presidential">Presidential</option>
            </select>
          </div>
          
          <div>
            <label htmlFor="max_occupancy" className="block text-sm font-medium text-gray-700">Max Occupancy</label>
            <input
              type="number"
              id="max_occupancy"
              name="max_occupancy"
              value={formData.max_occupancy}
              onChange={handleInputChange}
              min="1"
              max="10"
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              required
            />
          </div>
        </div>
        
        <div>
          <label htmlFor="nfc_lock_id" className="block text-sm font-medium text-gray-700">NFC Lock ID</label>
          <input
            type="text"
            id="nfc_lock_id"
            name="nfc_lock_id"
            value={formData.nfc_lock_id}
            onChange={handleInputChange}
            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          />
          <p className="mt-1 text-xs text-gray-500">Optional - Leave blank to auto-generate</p>
        </div>
        
        <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
          <button
            type="submit"
            className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:col-start-2 sm:text-sm"
            disabled={loading || hotels.length === 0}
          >
            {loading ? 'Creating...' : 'Create Room'}
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

export default AddRoomForm;
