// frontend/src/components/AddUserForm.js
import React, { useState } from 'react';
import axios from 'axios';
import { API_URL } from '../config';

function AddUserForm({ onSuccess, onCancel }) {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    phone_number: '',
    role: 'guest',
    is_active: true
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };
  // Safely parse and extract error messages from different error formats
  const getErrorMessage = (err) => {
    // Case 1: Error is an array of validation errors from Pydantic
    if (err.response?.data && Array.isArray(err.response.data)) {
      try {
        return err.response.data.map(item => {
          // Extract just the validation message without the "Value error, " prefix
          const cleanMessage = item.msg.replace('Value error, ', '');
          // For field-specific context, you can use: `${item.loc[1]}: ${cleanMessage}`
          return cleanMessage;
        }).join('. ');
      } catch (e) {
        console.error('Error parsing validation error:', e);
        return 'Validation error occurred. Please check your inputs.';
      }
    }
    
    // Case 2: Error has a detail field
    if (err.response?.data?.detail) {
      return typeof err.response.data.detail === 'object'
        ? JSON.stringify(err.response.data.detail)
        : String(err.response.data.detail);
    }
    
    // Case 3: Error response data is a string
    if (typeof err.response?.data === 'string') {
      return err.response.data;
    }
    
    // Case 4: Error message is available
    if (err.message) {
      return typeof err.message === 'object'
        ? JSON.stringify(err.message)
        : String(err.message);
    }
    
    // Default fallback
    return 'An error occurred while creating the user';
  };

  const handleCheckboxChange = (e) => {
    const { name, checked } = e.target;
    setFormData({
      ...formData,
      [name]: checked
    });
  };

  const validateForm = () => {
    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError('Please enter a valid email address');
      return false;
    }
    
    // Password length validation
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long');
      return false;
    }
    
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;
    
    setLoading(true);
    setError('');
    
    const token = localStorage.getItem('token');
    
    try {
      const response = await axios.post(
        `${API_URL}/users`,
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
      console.error('Error creating user:', err);
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white px-4 pt-5 pb-4 sm:p-6">
      <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
        Create New User
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
        <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
          <div className="sm:col-span-3">
            <label htmlFor="first_name" className="block text-sm font-medium text-gray-700">
              First name
            </label>
            <div className="mt-1">
              <input
                type="text"
                name="first_name"
                id="first_name"
                autoComplete="given-name"
                value={formData.first_name}
                onChange={handleInputChange}
                className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                required
              />
            </div>
          </div>

          <div className="sm:col-span-3">
            <label htmlFor="last_name" className="block text-sm font-medium text-gray-700">
              Last name
            </label>
            <div className="mt-1">
              <input
                type="text"
                name="last_name"
                id="last_name"
                autoComplete="family-name"
                value={formData.last_name}
                onChange={handleInputChange}
                className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                required
              />
            </div>
          </div>

          <div className="sm:col-span-4">
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
              Email address
            </label>
            <div className="mt-1">
              <input
                type="email"
                name="email"
                id="email"
                autoComplete="email"
                value={formData.email}
                onChange={handleInputChange}
                className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                required
              />
            </div>
          </div>

          <div className="sm:col-span-3">
            <label htmlFor="phone_number" className="block text-sm font-medium text-gray-700">
              Phone number
            </label>
            <div className="mt-1">
              <input
                type="text"
                name="phone_number"
                id="phone_number"
                autoComplete="tel"
                value={formData.phone_number}
                onChange={handleInputChange}
                className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
              />
            </div>
          </div>

          <div className="sm:col-span-3">
            <label htmlFor="role" className="block text-sm font-medium text-gray-700">
              Role
            </label>
            <div className="mt-1">
              <select
                id="role"
                name="role"
                autoComplete="role"
                value={formData.role}
                onChange={handleInputChange}
                className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
              >
                <option value="guest">Guest</option>
                <option value="hotel_staff">Hotel Staff</option>
                <option value="admin">Administrator</option>
              </select>
            </div>
          </div>

          <div className="sm:col-span-4">
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
              Password
            </label>
            <div className="mt-1">
              <input
                type="password"
                name="password"
                id="password"
                autoComplete="new-password"
                value={formData.password}
                onChange={handleInputChange}
                className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                required
                minLength="8"
              />
            </div>
            <p className="mt-1 text-xs text-gray-500">Must be at least 8 characters long</p>
          </div>

          <div className="sm:col-span-6">
            <div className="flex items-start">
              <div className="flex items-center h-5">
                <input
                  id="is_active"
                  name="is_active"
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={handleCheckboxChange}
                  className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                />
              </div>
              <div className="ml-3 text-sm">
                <label htmlFor="is_active" className="font-medium text-gray-700">
                  Active Account
                </label>
                <p className="text-gray-500">User can log in and use the system</p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
          <button
            type="submit"
            className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:col-start-2 sm:text-sm"
            disabled={loading}
          >
            {loading ? 'Creating...' : 'Create User'}
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

export default AddUserForm;
