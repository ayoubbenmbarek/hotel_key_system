// frontend/src/components/NFCSimulator.js
import React, { useState } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'https://166e-2a01-e0a-159-2b50-d852-e24a-103a-1ec0.ngrok-free.app/api/v1';

function NFCSimulator() {
  const [keyUuid, setKeyUuid] = useState('');
  const [lockId, setLockId] = useState('');
  const [deviceInfo, setDeviceInfo] = useState('NFC Simulator Device');
  const [location, setLocation] = useState('Main Entrance');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleSimulateNFC = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await axios.post(`${API_URL}/verify/key`, {
        key_uuid: keyUuid,
        lock_id: lockId,
        device_info: deviceInfo,
        location: location
      });

      setResult(response.data);
    } catch (err) {
      console.error('Error verifying key:', err);
      setError(err.response?.data?.detail || 'Failed to verify key. Please check your inputs and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white shadow-md rounded-lg p-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">NFC Lock Simulator</h2>
      
      <form onSubmit={handleSimulateNFC} className="space-y-4">
        <div>
          <label htmlFor="keyUuid" className="block text-sm font-medium text-gray-700">Key UUID</label>
          <input
            type="text"
            id="keyUuid"
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            placeholder="Enter the key UUID"
            value={keyUuid}
            onChange={(e) => setKeyUuid(e.target.value)}
            required
          />
        </div>

        <div>
          <label htmlFor="lockId" className="block text-sm font-medium text-gray-700">Lock ID</label>
          <input
            type="text"
            id="lockId"
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            placeholder="Enter the lock ID (e.g., LOCK-12345678)"
            value={lockId}
            onChange={(e) => setLockId(e.target.value)}
            required
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="deviceInfo" className="block text-sm font-medium text-gray-700">Device Info</label>
            <input
              type="text"
              id="deviceInfo"
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="Device information"
              value={deviceInfo}
              onChange={(e) => setDeviceInfo(e.target.value)}
            />
          </div>

          <div>
            <label htmlFor="location" className="block text-sm font-medium text-gray-700">Location</label>
            <input
              type="text"
              id="location"
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="Lock location"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            />
          </div>
        </div>

        <div>
          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            {loading ? 'Simulating...' : 'Simulate NFC Authentication'}
          </button>
        </div>
      </form>

      {error && (
        <div className="mt-4 bg-red-50 p-4 rounded-md">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {result && (
        <div className={`mt-4 ${result.is_valid ? 'bg-green-50' : 'bg-yellow-50'} p-4 rounded-md`}>
          <div className="flex">
            <div className="flex-shrink-0">
              {result.is_valid ? (
                <svg className="h-5 w-5 text-green-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className="h-5 w-5 text-yellow-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              )}
            </div>
            <div className="ml-3">
              <h3 className={`text-sm font-medium ${result.is_valid ? 'text-green-800' : 'text-yellow-800'}`}>
                {result.is_valid ? 'Access Granted' : 'Access Denied'}
              </h3>
              <div className={`mt-2 text-sm ${result.is_valid ? 'text-green-700' : 'text-yellow-700'}`}>
                <p><strong>Message:</strong> {result.message}</p>
                {result.is_valid && (
                  <>
                    <p className="mt-1"><strong>Room:</strong> {result.room_number}</p>
                    <p><strong>Guest:</strong> {result.guest_name}</p>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default NFCSimulator;
