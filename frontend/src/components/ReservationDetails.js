// frontend/src/components/ReservationDetails.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ReservationActions from './ReservationActions';
import { API_URL } from '../config';

function ReservationDetails({ reservationId, onClose, onUpdate, isStaff }) {
  const [reservation, setReservation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchReservationDetails = async () => {
      if (!reservationId) return;
      
      setLoading(true);
      const token = localStorage.getItem('token');
      
      try {
        const response = await axios.get(`${API_URL}/reservations/${reservationId}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        setReservation(response.data);
      } catch (err) {
        console.error('Error fetching reservation details:', err);
        setError(err.response?.data?.detail || 'Failed to load reservation details');
      } finally {
        setLoading(false);
      }
    };
    
    fetchReservationDetails();
  }, [reservationId]);

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    return new Date(dateString).toLocaleDateString(undefined, options);
  };

  const handleReservationUpdate = () => {
    // Refresh the reservation data
    setLoading(true);
    const token = localStorage.getItem('token');
    
    axios.get(`${API_URL}/reservations/${reservationId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(response => {
        setReservation(response.data);
        // Also notify parent component to refresh its data
        if (onUpdate) onUpdate();
      })
      .catch(err => {
        console.error('Error refreshing reservation details:', err);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  if (loading) {
    return (
      <div className="animate-pulse p-4">
        <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
        <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
        <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 p-4 rounded-md">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error loading reservation details</h3>
            <div className="mt-2 text-sm text-red-700">
              <p>{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!reservation) {
    return (
      <div className="text-center p-4">
        <p className="text-gray-500">No reservation details available</p>
      </div>
    );
  }

  return (
    <div className="bg-white shadow overflow-hidden sm:rounded-lg">
      <div className="px-4 py-5 sm:px-6 flex justify-between items-center">
        <div>
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Reservation Details
          </h3>
          <p className="mt-1 max-w-2xl text-sm text-gray-500">
            Confirmation Code: {reservation.confirmation_code}
          </p>
        </div>
        <button
          onClick={onClose}
          className="inline-flex items-center p-1 border border-transparent rounded-full shadow-sm text-white bg-gray-600 hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
        >
          <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </button>
      </div>
      <div className="border-t border-gray-200">
        <dl>
          <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
            <dt className="text-sm font-medium text-gray-500">Status</dt>
            <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
              <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                reservation.status === 'confirmed' ? 'bg-green-100 text-green-800' :
                reservation.status === 'checked_in' ? 'bg-blue-100 text-blue-800' :
                reservation.status === 'checked_out' ? 'bg-gray-100 text-gray-800' :
                'bg-red-100 text-red-800'
              }`}>
                {reservation.status === 'confirmed' ? 'Confirmed' :
                reservation.status === 'checked_in' ? 'Checked In' :
                reservation.status === 'checked_out' ? 'Checked Out' :
                reservation.status === 'cancelled' ? 'Cancelled' :
                reservation.status}
              </span>
            </dd>
          </div>
          <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
            <dt className="text-sm font-medium text-gray-500">Check-in / Check-out</dt>
            <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
              {formatDate(reservation.check_in)} to {formatDate(reservation.check_out)}
            </dd>
          </div>
          <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
            <dt className="text-sm font-medium text-gray-500">Room</dt>
            <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
              {reservation.room?.room_number || 'N/A'}
              {reservation.room?.room_type && ` (${reservation.room.room_type})`}
            </dd>
          </div>
          <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
            <dt className="text-sm font-medium text-gray-500">Hotel</dt>
            <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
              {reservation.room?.hotel?.name || 'N/A'}
              {reservation.room?.hotel?.address && (
                <p className="text-xs text-gray-500 mt-1">
                  {reservation.room.hotel.address}, {reservation.room.hotel.city}, {reservation.room.hotel.state} {reservation.room.hotel.postal_code}
                </p>
              )}
            </dd>
          </div>
          <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
            <dt className="text-sm font-medium text-gray-500">Number of Guests</dt>
            <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
              {reservation.number_of_guests}
            </dd>
          </div>
          {reservation.special_requests && (
            <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500">Special Requests</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                {reservation.special_requests}
              </dd>
            </div>
          )}
        </dl>
      </div>
      
      {/* Add the ReservationActions component */}
      <div className="border-t border-gray-200 px-4 py-5 sm:px-6">
        <ReservationActions
          reservation={reservation}
          onUpdate={handleReservationUpdate}
          isStaff={isStaff}
        />
      </div>
    </div>
  );
}

export default ReservationDetails;
