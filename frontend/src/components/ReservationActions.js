// frontend/src/components/ReservationActions.js
import React, { useState } from 'react';
import axios from 'axios';
import { API_URL } from '../config';

function ReservationActions({ reservation, onUpdate, isStaff }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [confirmCancel, setConfirmCancel] = useState(false);
  const [confirmCheckout, setConfirmCheckout] = useState(false);

  const formatDate = (dateString) => {
    const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    return new Date(dateString).toLocaleDateString(undefined, options);
  };

  const handleCheckIn = async () => {
    if (reservation.status !== 'confirmed') return;
    
    setLoading(true);
    setError('');
    const token = localStorage.getItem('token');
    
    try {
      await axios.patch(
        `${API_URL}/reservations/${reservation.id}/check-in`,
        {},
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      
      // Call the parent update function
      onUpdate && onUpdate();
    } catch (err) {
      console.error('Error checking in reservation:', err);
      setError(err.response?.data?.detail || 'Failed to check in guest');
    } finally {
      setLoading(false);
    }
  };

  const handleCheckOut = async () => {
    if (reservation.status !== 'checked_in') return;
    setConfirmCheckout(false);
    
    setLoading(true);
    setError('');
    const token = localStorage.getItem('token');
    
    try {
      await axios.patch(
        `${API_URL}/reservations/${reservation.id}/check-out`,
        {},
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      
      // Call the parent update function
      onUpdate && onUpdate();
    } catch (err) {
      console.error('Error checking out reservation:', err);
      setError(err.response?.data?.detail || 'Failed to check out guest');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    setConfirmCancel(false);
    
    setLoading(true);
    setError('');
    const token = localStorage.getItem('token');
    
    try {
      await axios.delete(
        `${API_URL}/reservations/${reservation.id}`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      
      // Call the parent update function
      onUpdate && onUpdate();
    } catch (err) {
      console.error('Error cancelling reservation:', err);
      setError(err.response?.data?.detail || 'Failed to cancel reservation');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {error && (
        <div className="bg-red-50 p-4 rounded-md">
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
      
      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Reservation Actions
          </h3>
          <div className="mt-2 max-w-xl text-sm text-gray-500">
            <p>
              Confirmation: {reservation.confirmation_code}<br />
              Status: {reservation.status}<br />
              Check-in: {formatDate(reservation.check_in)}<br />
              Check-out: {formatDate(reservation.check_out)}
            </p>
          </div>
          <div className="mt-5 flex flex-col sm:flex-row sm:space-x-4 space-y-2 sm:space-y-0">
            {isStaff && reservation.status === 'confirmed' && (
              <button
                type="button"
                onClick={handleCheckIn}
                disabled={loading}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                {loading ? 'Processing...' : 'Check In Guest'}
              </button>
            )}
            
            {isStaff && reservation.status === 'checked_in' && (
              <>
                {confirmCheckout ? (
                  <div className="flex space-x-2">
                    <button
                      type="button"
                      onClick={handleCheckOut}
                      disabled={loading}
                      className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                    >
                      {loading ? 'Processing...' : 'Confirm Check Out'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setConfirmCheckout(false)}
                      disabled={loading}
                      className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={() => setConfirmCheckout(true)}
                    disabled={loading}
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    Check Out Guest
                  </button>
                )}
              </>
            )}
            
            {reservation.status !== 'checked_out' && reservation.status !== 'cancelled' && (
              <>
                {confirmCancel ? (
                  <div className="flex space-x-2">
                    <button
                      type="button"
                      onClick={handleCancel}
                      disabled={loading}
                      className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                    >
                      {loading ? 'Processing...' : 'Confirm Cancellation'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setConfirmCancel(false)}
                      disabled={loading}
                      className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      Keep Reservation
                    </button>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={() => setConfirmCancel(true)}
                    disabled={loading}
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                  >
                    Cancel Reservation
                  </button>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ReservationActions;
