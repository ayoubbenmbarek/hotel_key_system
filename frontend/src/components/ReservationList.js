// frontend/src/components/ReservationList.js
import React, { useState, useMemo } from 'react';
import ReservationDetails from './ReservationDetails';
import SearchBar from './SearchBar';

function ReservationList({ reservations, loading, onCreateKey, isStaff, onRefresh, onAddReservation }) {
  const [selectedReservation, setSelectedReservation] = useState(null);
  const [viewingReservationId, setViewingReservationId] = useState(null);
  const [creatingKey, setCreatingKey] = useState(false);
  const [passType, setPassType] = useState('apple');
  const [sendEmail, setSendEmail] = useState(true);
  const [alternativeEmail, setAlternativeEmail] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Add console logging for debugging
  React.useEffect(() => {
    if (reservations && reservations.length > 0) {
      console.log('Reservation data structure:', reservations[0]);
      console.log('First reservation user data:', reservations[0]?.user);
    }
  }, [reservations]);

  // Filter reservations based on search query
  const filteredReservations = useMemo(() => {
    if (!searchQuery.trim() || !reservations) return reservations;
    
    const query = searchQuery.toLowerCase();
    return reservations.filter(reservation => {
      const user = reservation.user || {};
      const room = reservation.room || {};
      const hotel = room.hotel || {};
      
      return (
        reservation.confirmation_code?.toLowerCase().includes(query) ||
        room.room_number?.toString().toLowerCase().includes(query) ||
        user.first_name?.toLowerCase().includes(query) ||
        user.last_name?.toLowerCase().includes(query) ||
        user.email?.toLowerCase().includes(query) ||
        hotel.name?.toLowerCase().includes(query) ||
        reservation.status?.toLowerCase().includes(query)
      );
    });
  }, [reservations, searchQuery]);

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    return new Date(dateString).toLocaleDateString(undefined, options);
  };

  const handleCreateKey = async (reservationId) => {
    setCreatingKey(true);
    try {
      await onCreateKey(
        reservationId, 
        passType, 
        sendEmail, 
        alternativeEmail || null, 
      );
      setSelectedReservation(null);
      
      // Reset form fields
      setPassType('apple');
      setSendEmail(true);
      setAlternativeEmail('');
    } catch (err) {
      console.error('Error in ReservationList creating key:', err);
    } finally {
      setCreatingKey(false);
    }
  };

  const handleViewDetails = (reservationId) => {
    setViewingReservationId(reservationId);
  };

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

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      <div className="px-4 py-5 sm:px-6 border-b">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Reservations
            </h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">
              Your current and upcoming hotel reservations
            </p>
          </div>
          <div className="flex space-x-2">
            {isStaff && (
              <button
                onClick={onAddReservation}
                className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                <svg className="h-4 w-4 mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                New Reservation
              </button>
            )}
            <button
              onClick={onRefresh}
              className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              <svg className="h-4 w-4 mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </button>
          </div>
        </div>
        
        <SearchBar
          placeholder="Search by confirmation code, room number, guest name..."
          value={searchQuery}
          onChange={setSearchQuery}
          className="max-w-md"
        />
      </div>
      
      {!filteredReservations || filteredReservations.length === 0 ? (
        <div className="px-4 py-5 sm:p-6 text-center">
          <p className="text-gray-500">
            {searchQuery.trim() ? 'No reservations found matching your search' : 'No reservations found'}
          </p>
        </div>
      ) : (
        <ul className="divide-y divide-gray-200">
          {Array.isArray(filteredReservations) && filteredReservations.map((reservation) => (
            <li key={reservation.id} className="px-4 py-4 sm:px-6">
              <div className="flex items-center justify-between">
                <div className="flex flex-col md:flex-row md:items-center">
                  <p className="text-sm font-medium text-indigo-600 truncate">
                    Confirmation: {reservation.confirmation_code}
                  </p>
                  <p className="md:ml-2 text-sm text-gray-500">
                    Room: {reservation.room?.room_number || "Unknown"}
                  </p>
                  {reservation.user ? (
                    <p className="md:ml-2 text-sm font-medium text-gray-700">
                      Guest: {reservation.user.first_name} {reservation.user.last_name}
                    </p>
                  ) : (
                    <p className="md:ml-2 text-sm font-medium text-yellow-600">
                      Guest information not available
                    </p>
                  )}
                </div>
                <div className="ml-2 flex-shrink-0 flex">
                  <p className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
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
                  </p>
                </div>
              </div>
              <div className="mt-2 sm:flex sm:justify-between">
                <div className="sm:flex">
                  <p className="flex items-center text-sm text-gray-500">
                    <svg className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                    </svg>
                    <span>{reservation.number_of_guests} guests</span>
                  </p>
                  <p className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0 sm:ml-6">
                    <svg className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                    </svg>
                    {reservation.room?.hotel?.name || "Unknown Hotel"}
                  </p>
                </div>
                <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                  <svg className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                  </svg>
                  <p>
                    {formatDate(reservation.check_in)} to {formatDate(reservation.check_out)}
                  </p>
                </div>
              </div>
              <div className="mt-4 flex justify-end space-x-3">
                <button
                  onClick={() => handleViewDetails(reservation.id)}
                  className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  <svg className="h-4 w-4 mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  View Details
                </button>
                
                {(reservation.status === 'confirmed' || reservation.status === 'checked_in') && (
                  <button
                    onClick={() => setSelectedReservation(reservation.id)}
                    className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    <svg className="h-4 w-4 mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                    </svg>
                    Create Digital Key
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
      
      {/* Modal for creating a key */}
      {selectedReservation && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-indigo-100 sm:mx-0 sm:h-10 sm:w-10">
                    <svg className="h-6 w-6 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                    </svg>
                  </div>
                  <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      Create Digital Key
                    </h3>
                    <div className="mt-2">
                      <p className="text-sm text-gray-500">
                        Choose the digital key type and delivery options below.
                      </p>
                    </div>
                    <div className="mt-4 space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">
                          Pass Type
                        </label>
                        <select
                          className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                          value={passType}
                          onChange={(e) => setPassType(e.target.value)}
                        >
                          <option value="apple">Apple Wallet</option>
                          <option value="google">Google Wallet</option>
                        </select>
                      </div>
                      
                      {/* Email Options */}
                      <div className="border-t pt-4">
                        <div className="flex items-start">
                          <div className="flex items-center h-5">
                            <input
                              id="send-email"
                              name="send-email"
                              type="checkbox"
                              className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                              checked={sendEmail}
                              onChange={(e) => {
                                setSendEmail(e.target.checked);
                                if (!e.target.checked) {
                                  setAlternativeEmail('');
                                }
                              }}
                            />
                          </div>
                          <div className="ml-3 text-sm">
                            <label htmlFor="send-email" className="font-medium text-gray-700">
                              Send email with pass
                            </label>
                            <p className="text-gray-500">
                              The digital key will be sent to the guest's email address.
                            </p>
                          </div>
                        </div>
                        
                        {/* Add alternative email field */}
                        {sendEmail && (
                          <div className="mt-3">
                            <label htmlFor="alternative-email" className="block text-sm font-medium text-gray-700">
                              Alternative Email (optional)
                            </label>
                            <div className="mt-1">
                              <input
                                type="email"
                                name="alternative-email"
                                id="alternative-email"
                                className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                                placeholder="Use if guest email is invalid"
                                value={alternativeEmail}
                                onChange={(e) => setAlternativeEmail(e.target.value)}
                              />
                            </div>
                          </div>
                        )}
                      </div>                      
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  className={`w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm ${
                    creatingKey ? 'opacity-75 cursor-not-allowed' : ''
                  }`}
                  onClick={() => handleCreateKey(selectedReservation)}
                >
                  {creatingKey ? 'Creating...' : 'Create Key'}
                </button>
                <button
                  type="button"
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                  onClick={() => setSelectedReservation(null)}
                  disabled={creatingKey}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Reservation Details Modal */}
      {viewingReservationId && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-3xl sm:w-full">
              <ReservationDetails 
                reservationId={viewingReservationId}
                onClose={() => setViewingReservationId(null)}
                onUpdate={onRefresh}
                isStaff={isStaff}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ReservationList;
