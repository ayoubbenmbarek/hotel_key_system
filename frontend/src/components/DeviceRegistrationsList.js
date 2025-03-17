// frontend/src/components/DeviceRegistrationsList.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../config';

function DeviceRegistrationsList() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  useEffect(() => {
    const fetchDevices = async () => {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      try {
        const response = await axios.get(`${API_URL}/devices/registrations`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        setDevices(Array.isArray(response.data) ? response.data : []);
      } catch (err) {
        console.error('Error fetching device registrations:', err);
        setError(err.response?.data?.detail || 'Failed to load device registrations');
      } finally {
        setLoading(false);
      }
    };
    
    fetchDevices();
  }, []);

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A';
    const options = { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric', 
      hour: '2-digit', 
      minute: '2-digit'
    };
    return new Date(timestamp).toLocaleDateString(undefined, options);
  };

  const handleUnregisterDevice = async (deviceId) => {
    const token = localStorage.getItem('token');
    
    try {
      await axios.delete(`${API_URL}/devices/registrations/${deviceId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      // Remove the device from the list
      setDevices(devices.filter(device => device.id !== deviceId));
    } catch (err) {
      console.error('Error unregistering device:', err);
      alert('Failed to unregister device: ' + (err.response?.data?.detail || err.message));
    }
  };

  if (loading) {
    return (
      <div className="bg-white shadow sm:rounded-lg animate-pulse">
        <div className="px-4 py-5 sm:p-6">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded w-full"></div>
            <div className="h-4 bg-gray-200 rounded w-full"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="bg-red-50 p-4 rounded-md">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error loading device registrations</h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{error}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow overflow-hidden sm:rounded-lg">
      <div className="px-4 py-5 sm:px-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900">Device Registrations</h3>
        <p className="mt-1 max-w-2xl text-sm text-gray-500">Devices registered to receive push notifications for digital keys</p>
      </div>
      <div className="border-t border-gray-200">
        {devices.length === 0 ? (
          <div className="px-4 py-5 sm:px-6 text-center text-gray-500">
            No device registrations found
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Device ID
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Key
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Pass Type
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Registered
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th scope="col" className="relative px-6 py-3">
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {devices.map((device) => (
                <tr key={device.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {device.device_library_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {device.serial_number}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {device.pass_type_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatTimestamp(device.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${device.active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                      {device.active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => handleUnregisterDevice(device.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Unregister
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default DeviceRegistrationsList;
