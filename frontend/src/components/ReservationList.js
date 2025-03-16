// frontend/src/components/ReservationList.js
import React, { useState } from 'react';

function ReservationList({ reservations, loading, onCreateKey, isStaff, onRefresh }) {
  const [expandedId, setExpandedId] = useState(null);
  const [selectedReservation, setSelectedReservation] = useState(null);
  const [showKeyModal, setShowKeyModal] = useState(false);
  const [passType, setPassType] = useState('apple');
  const [sendEmail, setSendEmail] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleCreateKey = async () => {
    if (!selectedReservation) return;
    
    setIsGenerating(true);
    try {
      await onCreateKey(selectedReservation.id, passType, sendEmail);
      setShowKeyModal(false);
      setSelectedReservation(null);
    } catch (err) {
      console.error('Error creating key:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  const openKeyModal = (reservation) => {
    setSelectedReservation(reservation);
    setShowKeyModal(true);
  };

  // Get reservation status label and color
  const getStatusLabel = (status) => {
    switch (status) {
      case 'confirmed':
        return { text: 'Confirmed', color: 'bg-blue-100 text-blue-800' };
      case 'checked_in':
        return { text: 'Checked In', color: 'bg-green-100 text-green-800' };
      case 'checked_out':
        return { text: 'Checked Out', color: 'bg-gray-100 text-gray-800' };
      case 'cancelled':
        return { text: 'Cancelled', color: 'bg-red-100 text-red-800' };
      case 'no_show':
        return { text: 'No Show', color: 'bg-yellow-100 text-yellow-800' };
      default:
        return { text: status, color: 'bg-gray-100 text-gray-800' };
    }
  };

  // Format date for display
  const formatDate = (dateString) => {
    const options = { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
  };

  // Check if key creation is allowed for this reservation
  const canCreateKey = (reservation) => {
    return ['confirmed', 'checked_in'].includes(reservation.status);
  };

  return (
    <div className="bg-white shadow overflow-hidden sm:rounded-md">
      <div className="px-4 py-5 sm:px-6 flex justify-between items-center">
        <h3 className="text-lg leading-6 font-medium text-gray-900">Reservations</h3>
        <button
          onClick={onRefresh}
          className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm leading-5 font-medium rounded-md text-gray-700 bg-white hover:text-gray-500 focus:outline-none focus:border-blue-300 focus:shadow-outline-blue active:text-gray-800 active:bg-gray-50 transition ease-in-out duration-150"
        >
          <svg className="-ml-1 mr-2 h-5 w-5 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>
      
      {loading ? (
        <div className="text-center py-10">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-600"></div>
          <p className="mt-2 text-gray-500">Loading reservations...</p>
        </div>
      ) : reservations.length === 0 ? (
        <div className="text-center py-10">
          <p className="text-gray-500">No reservations found.</p>
        </div>
      ) : (
        <ul className="divide-y divide-gray-200">
          {reservations.map((reservation) => {
            const statusLabel = getStatusLabel(reservation.status);
            
            return (
              <li key={reservation.id}>
                <div 
                  className="block hover:bg-gray-50 cursor-pointer transition duration-150 ease-in-out"
                  onClick={() => setExpandedId(expandedId === reservation.id ? null : reservation.id)}
                >
                  <div className="px-4 py-4 sm:px-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <p className="text-sm font-medium text-indigo-600 truncate">
                          Confirmation #{reservation.confirmation_code}
                        </p>
                        <div className={`ml-2 flex-shrink-0 flex`}>
                          <p className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${statusLabel.color}`}>
                            {statusLabel.text}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center">
                        {canCreateKey(reservation) && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              openKeyModal(reservation);
                            }}
                            className="mr-2 inline-flex items-center px-2.5 py-1.5 border border-transparent text-xs leading-4 font-medium rounded text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:border-indigo-700 focus:shadow-outline-indigo active:bg-indigo-700"
                          >
                            Create Key
                          </button>
                        )}
                        <svg 
                          className={`h-5 w-5 text-gray-400 transition-transform duration-200 ${expandedId === reservation.id ? 'transform rotate-180' : ''}`} 
                          xmlns="http://www.w3.org/2000/svg" 
                          viewBox="0 0 20 20" 
                          fill="currentColor"
                        >
                          <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                        </svg>
                      </div>
                    </div>
                    <div className="mt-2 sm:flex sm:justify-between">
                      <div className="sm:flex">
                        <p className="flex items-center text-sm text-gray-500">
                          <svg className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                          </svg>
                          {reservation.user?.first_name} {reservation.user?.last_name}
                        </p>
                        <p className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0 sm:ml-6">
                          <svg className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                          </svg>
                          Room {reservation.room?.room_number}
                        </p>
                      </div>
                      <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                        <svg className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                        </svg>
                        <p>
                          {formatDate(reservation.check_in)} - {formatDate(reservation.check_out)}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Expanded details */}
                {expandedId === reservation.id && (
                  <div className="px-4 py-4 sm:px-6 bg-gray-50 border-t border-gray-200">
                    <dl className="grid grid-cols-1 gap-x-4 gap-y-4 sm:grid-cols-2">
                      <div className="sm:col-span-1">
                        <dt className="text-sm font-medium text-gray-500">Guest</dt>
                        <dd className="mt-1 text-sm text-gray-900">{reservation.user?.first_name} {reservation.user?.last_name}</dd>
                      </div>
                      <div className="sm:col-span-1">
                        <dt className="text-sm font-medium text-gray-500">Email</dt>
                        <dd className="mt-1 text-sm text-gray-900">{reservation.user?.email}</dd>
                      </div>
                      <div className="sm:col-span-1">
                        <dt className="text-sm font-medium text-gray-500">Check-in</dt>
                        <dd className="mt-1 text-sm text-gray-900">{formatDate(reservation.check_in)}</dd>
                      </div>
                      <div className="sm:col-span-1">
                        <dt className="text-sm font-medium text-gray-500">Check-out</dt>
                        <dd className="mt-1 text-sm text-gray-900">{formatDate(reservation.check_out)}</dd>
                      </div>
                      <div className="sm:col-span-1">
                        <dt className="text-sm font-medium text-gray-500">Room</dt>
                        <dd className="mt-1 text-sm text-gray-900">{reservation.room?.room_number} ({reservation.room?.room_type})</dd>
                      </div>
                      <div className="sm:col-span-1">
                        <dt className="text-sm font-medium text-gray-500">Guests</dt>
                        <dd className="mt-1 text-sm text-gray-900">{reservation.number_of_guests} person(s)</dd>
                      </div>
                      {reservation.special_requests && (
                        <div className="sm:col-span-2">
                          <dt className="text-sm font-medium text-gray-500">Special Requests</dt>
                          <dd className="mt-1 text-sm text-gray-900">{reservation.special_requests}</dd>
                        </div>
                      )}
                    </dl>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
      
      {/* Create Key Modal */}
      {showKeyModal && selectedReservation && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            
            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
              <div>
                <div className="mt-3 text-center sm:mt-5">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    Create Digital Key
                  </h3>
                  <div className="mt-2">
                    <p className="text-sm text-gray-500">
                      Create a digital key for reservation #{selectedReservation.confirmation_code} for {selectedReservation.user?.first_name} {selectedReservation.user?.last_name}.
                    </p>
                  </div>
                </div>
                
                <div className="mt-5 sm:mt-6 space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Pass Type</label>
                    <select
                      className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                      value={passType}
                      onChange={(e) => setPassType(e.target.value)}
                    >
                      <option value="apple">Apple Wallet</option>
                      <option value="google">Google Wallet</option>
                    </select>
                  </div>
                  
                  <div className="flex items-center">
                    <input
                      id="send-email"
                      name="send-email"
                      type="checkbox"
                      className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                      checked={sendEmail}
                      onChange={(e) => setSendEmail(e.target.checked)}
                    />
                    <label htmlFor="send-email" className="ml-2 block text-sm text-gray-900">
                      Send email to guest
                    </label>
                  </div>
                </div>
              </div>
              
              <div className="mt-5 sm:mt-6 grid grid-cols-2 gap-3">
                <button
                  type="button"
                  className="w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:text-sm"
                  onClick={() => setShowKeyModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:text-sm"
                  onClick={handleCreateKey}
                  disabled={isGenerating}
                >
                  {isGenerating ? 'Creating...' : 'Create Key'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ReservationList;
