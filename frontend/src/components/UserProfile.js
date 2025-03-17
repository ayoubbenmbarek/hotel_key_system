// frontend/src/components/UserProfile.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../config';

function UserProfile({ user, setUser }) {
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone_number: '',
    password: '',
    confirmPassword: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Initialize form data when user prop changes
  useEffect(() => {
    if (user) {
      setFormData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        phone_number: user.phone_number || '',
        password: '',
        confirmPassword: ''
      });
    }
  }, [user]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate passwords match if provided
    if (formData.password && formData.password !== formData.confirmPassword) {
      setError("Passwords don't match");
      return;
    }
    
    // Clear messages
    setError('');
    setSuccess('');
    setLoading(true);
    
    try {
      // Prepare data for API
      const updateData = {
        first_name: formData.first_name,
        last_name: formData.last_name,
        phone_number: formData.phone_number
      };
      
      // Only include password if provided
      if (formData.password) {
        updateData.password = formData.password;
      }
      
      console.log(`Updating user profile to ${API_URL}/users/me`);
      
      // Send update request
      const token = localStorage.getItem('token');
      const response = await axios.put(
        `${API_URL}/users/me`,
        updateData,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      console.log("Profile update response:", response.data);
      
      // Create updated user object
      const updatedUser = {
        ...user,
        ...response.data
      };
      
      // Update local user data
      setUser(updatedUser);
      
      // Show success and reset form
      setSuccess('Profile updated successfully');
      setFormData({
        ...response.data,
        password: '',
        confirmPassword: ''
      });
      
      // Exit edit mode
      setIsEditing(false);
    } catch (err) {
      console.error('Error updating profile:', err);
      setError(err.response?.data?.detail || 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      <div className="px-4 py-5 sm:px-6 border-b">
        <h3 className="text-lg leading-6 font-medium text-gray-900">
          User Profile
        </h3>
        <p className="mt-1 max-w-2xl text-sm text-gray-500">
          Your personal information and account settings
        </p>
      </div>
      
      <div className="px-4 py-5 sm:p-6">
        {/* Success message */}
        {success && (
          <div className="mb-4 bg-green-50 p-4 rounded-md">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-green-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-green-800">
                  {success}
                </p>
              </div>
            </div>
          </div>
        )}
        
        {/* Error message */}
        {error && (
          <div className="mb-4 bg-red-50 p-4 rounded-md">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-red-800">
                  {error}
                </p>
              </div>
            </div>
          </div>
        )}
        
        {isEditing ? (
          <form onSubmit={handleSubmit}>
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

              <div className="sm:col-span-3">
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
                    disabled
                    className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md bg-gray-50"
                  />
                  <p className="mt-1 text-xs text-gray-500">Email cannot be changed</p>
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
                <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                  New password
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
                  />
                  <p className="mt-1 text-xs text-gray-500">Leave blank to keep current password</p>
                </div>
              </div>

              <div className="sm:col-span-3">
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                  Confirm new password
                </label>
                <div className="mt-1">
                  <input
                    type="password"
                    name="confirmPassword"
                    id="confirmPassword"
                    autoComplete="new-password"
                    value={formData.confirmPassword}
                    onChange={handleInputChange}
                    className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                  />
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-end space-x-3">
              <button
                type="button"
                className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                onClick={() => {
                  setIsEditing(false);
                  setError('');
                  // Reset form data to original values
                  setFormData({
                    first_name: user?.first_name || '',
                    last_name: user?.last_name || '',
                    email: user?.email || '',
                    phone_number: user?.phone_number || '',
                    password: '',
                    confirmPassword: ''
                  });
                }}
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                disabled={loading}
              >
                {loading ? 'Saving...' : 'Save'}
              </button>
            </div>
          </form>
        ) : (
          <div className="space-y-6">
            <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
              <div className="sm:col-span-3">
                <h3 className="text-sm font-medium text-gray-500">First name</h3>
                <p className="mt-1 text-sm text-gray-900">{user?.first_name || 'Not provided'}</p>
              </div>

              <div className="sm:col-span-3">
                <h3 className="text-sm font-medium text-gray-500">Last name</h3>
                <p className="mt-1 text-sm text-gray-900">{user?.last_name || 'Not provided'}</p>
              </div>

              <div className="sm:col-span-3">
                <h3 className="text-sm font-medium text-gray-500">Email address</h3>
                <p className="mt-1 text-sm text-gray-900">{user?.email || 'Not provided'}</p>
              </div>

              <div className="sm:col-span-3">
                <h3 className="text-sm font-medium text-gray-500">Phone number</h3>
                <p className="mt-1 text-sm text-gray-900">{user?.phone_number || 'Not provided'}</p>
              </div>

              <div className="sm:col-span-3">
                <h3 className="text-sm font-medium text-gray-500">Role</h3>
                <p className="mt-1 text-sm text-gray-900">
                  {user?.role === 'admin' ? 'Administrator' : 
                   user?.role === 'hotel_staff' ? 'Hotel Staff' : 
                   user?.role === 'guest' ? 'Guest' : user?.role || 'Not assigned'}
                </p>
              </div>

              <div className="sm:col-span-3">
                <h3 className="text-sm font-medium text-gray-500">Account status</h3>
                <p className="mt-1 text-sm text-gray-900">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    user?.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {user?.is_active ? 'Active' : 'Inactive'}
                  </span>
                </p>
              </div>
            </div>

            <div className="flex justify-end">
              <button
                type="button"
                className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                onClick={() => setIsEditing(true)}
              >
                Edit Profile
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default UserProfile;
