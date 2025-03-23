// frontend/src/components/DigitalKeyList.js
import React, { useState, useMemo } from 'react';
import { KeyEventsModal } from './KeyEventsList';
import { toast } from 'react-toastify';
import SearchBar from './SearchBar';

function DigitalKeyList({
  keys,
  loading,
  onActivate,
  onDeactivate,
  onExtend,
  onSendEmail,
  onSendSMS,
  isStaff,
  onRefresh
}) {
  const [selectedKey, setSelectedKey] = useState(null);
  const [viewingKeyId, setViewingKeyId] = useState(null);
  const [isExtendModalOpen, setIsExtendModalOpen] = useState(false);
  const [extendDate, setExtendDate] = useState('');
  const [extendTime, setExtendTime] = useState('12:00');
  const [processingKey, setProcessingKey] = useState(false);
  const [showSMSModal, setShowSMSModal] = useState(false);
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [selectedKeyForSMS, setSelectedKeyForSMS] = useState(null);
  const [selectedKeyForEmail, setSelectedKeyForEmail] = useState(null);
  const [emailInfo, setEmailInfo] = useState(null);
  const [customEmail, setCustomEmail] = useState('');
  const [phoneNumbers, setPhoneNumbers] = useState(['']);
  const [sendingSMS, setSendingSMS] = useState(false);
  const [sendingEmail, setSendingEmail] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Filter keys based on search query
  const filteredKeys = useMemo(() => {
    if (!searchQuery.trim() || !keys) return keys;
    
    const query = searchQuery.toLowerCase();
    return keys.filter(key => {
      const reservation = key.reservation || {};
      const user = reservation.user || {};
      const room = reservation.room || {};
      
      return (
        key.key_uuid?.toLowerCase().includes(query) ||
        key.pass_type?.toLowerCase().includes(query) ||
        room.room_number?.toString().toLowerCase().includes(query) ||
        user.first_name?.toLowerCase().includes(query) ||
        user.last_name?.toLowerCase().includes(query) ||
        user.email?.toLowerCase().includes(query)
      );
    });
  }, [keys, searchQuery]);

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    return new Date(dateString).toLocaleDateString(undefined, options);
  };

  const handleExtendSubmit = async () => {
    if (!extendDate || !selectedKey) return;
    
    setProcessingKey(true);
    try {
      // Combine date and time into a single ISO string
      const combinedDateTime = `${extendDate}T${extendTime}:00`;
      await onExtend(selectedKey, combinedDateTime);
      setIsExtendModalOpen(false);
      setSelectedKey(null);
    } catch (err) {
      console.error('Error extending key:', err);
    } finally {
      setProcessingKey(false);
    }
  };

  const handleActivate = async (keyId) => {
    setProcessingKey(true);
    try {
      await onActivate(keyId);
    } catch (err) {
      console.error('Error activating key:', err);
    } finally {
      setProcessingKey(false);
    }
  };

  const handleDeactivate = async (keyId) => {
    setProcessingKey(true);
    try {
      await onDeactivate(keyId);
    } catch (err) {
      console.error('Error deactivating key:', err);
    } finally {
      setProcessingKey(false);
    }
  };

  const handleSendEmail = async (keyId, alternativeEmail = null) => {
    if (alternativeEmail) {
      setSendingEmail(true);
    } else {
      setProcessingKey(true);
    }
    
    try {
      await onSendEmail(keyId, alternativeEmail);
      if (alternativeEmail) {
        setShowEmailModal(false);
        setCustomEmail('');
        setSelectedKeyForEmail(null);
      } else {
        setShowEmailModal(false);
      }
    } catch (err) {
      console.error('Error sending key email:', err);
    } finally {
      setSendingEmail(false);
      setProcessingKey(false);
    }
  };
  
  const handleOpenEmailModal = async (key) => {
    // Find the current key in the array
    const currentKey = keys.find(k => k.id === key.id);
    
    if (currentKey && currentKey.reservation && currentKey.reservation.user) {
      // If we have the guest info from the key's reservation
      const userInfo = currentKey.reservation.user;
      setEmailInfo({
        name: `${userInfo.first_name} ${userInfo.last_name}`,
        email: userInfo.email
      });
    } else {
      // Otherwise show that we don't have the email info but will use the database email
      setEmailInfo({
        name: "Current guest",
        email: "The email address stored in the database will be used"
      });
    }
    
    setSelectedKeyForEmail(key.id);
    setCustomEmail(''); // Reset custom email field
    setShowEmailModal(true);
  };

  const handleSendSMS = async () => {
    if (!selectedKeyForSMS) return;
    
    const validPhoneNumbers = phoneNumbers.filter(phone => phone.trim() !== '');
    if (validPhoneNumbers.length === 0) {
      toast.error('Please enter at least one phone number');
      return;
    }
    
    setSendingSMS(true);
    try {
      // Send just the array of phone numbers, matching Swagger format
      await onSendSMS(selectedKeyForSMS, validPhoneNumbers);
      // toast.success('SMS sent successfully');
      setShowSMSModal(false);
      setPhoneNumbers(['']);
      setSelectedKeyForSMS(null);
    } catch (err) {
      console.error('Error sending SMS:', err);
      // toast.error('Failed to send SMS: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSendingSMS(false);
    }
  };

  const getDefaultEndDate = (validUntil) => {
    // Create a date from the valid_until value
    const defaultDate = new Date(validUntil);
    // Add one day
    defaultDate.setDate(defaultDate.getDate() + 1);
    // Return in YYYY-MM-DD format
    return defaultDate.toISOString().split('T')[0];
  };

  const getDefaultEndTime = (validUntil) => {
    // Extract the time portion from validUntil
    const defaultTime = new Date(validUntil);
    // Format as HH:MM
    return `${String(defaultTime.getHours()).padStart(2, '0')}:${String(defaultTime.getMinutes()).padStart(2, '0')}`;
  };

  const handleViewKeyEvents = (keyId) => {
    setViewingKeyId(keyId);
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
              Digital Keys
            </h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">
              Your digital room keys
            </p>
          </div>
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
        
        <SearchBar
          placeholder="Search by room number, guest name, or key ID..."
          value={searchQuery}
          onChange={setSearchQuery}
          className="max-w-md"
        />
      </div>
      
      {!filteredKeys || filteredKeys.length === 0 ? (
        <div className="px-4 py-5 sm:p-6 text-center">
          <p className="text-gray-500">
            {searchQuery.trim() ? 'No keys found matching your search' : 'No digital keys found'}
          </p>
        </div>
      ) : (
        <ul className="divide-y divide-gray-200">
          {Array.isArray(filteredKeys) && filteredKeys.map((key) => (
            <li key={key.id} className="px-4 py-4 sm:px-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className={`flex-shrink-0 h-10 w-10 rounded-full ${key.is_active ? 'bg-green-100' : 'bg-gray-100'} flex items-center justify-center`}>
                    <svg className={`h-6 w-6 ${key.is_active ? 'text-green-600' : 'text-gray-600'}`} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                    </svg>
                  </div>
                  <div className="ml-4">
                    <div className="text-sm font-medium text-gray-900">
                      {key.pass_type === 'apple' ? 'Apple Wallet' : 'Google Wallet'} Key
                    </div>
                    <div className="text-sm text-gray-500">
                      ID: {key.key_uuid?.substring(0, 8)}...
                    </div>
                    {key.reservation?.user && (
                      <div className="text-sm text-indigo-600">
                        Guest: {key.reservation.user.first_name} {key.reservation.user.last_name}
                      </div>
                    )}
                  </div>
                </div>
                <div className="ml-2 flex-shrink-0 flex">
                  <p className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    key.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {key.is_active ? 'Active' : 'Inactive'}
                  </p>
                </div>
              </div>
              <div className="mt-2 sm:flex sm:justify-between">
                <div className="sm:flex sm:flex-col">
                  <p className="flex items-center text-sm text-gray-500">
                    <svg className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                    </svg>
                    Valid from {formatDate(key.valid_from)} to {formatDate(key.valid_until)}
                  </p>
                  {key.last_used && (
                    <p className="mt-1 flex items-center text-sm text-gray-500">
                      <svg className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                      </svg>
                      Last used: {formatDate(key.last_used)}
                    </p>
                  )}
                </div>
                <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                  {key.pass_url && (
                    <a
                      href={key.pass_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      Download Pass
                    </a>
                  )}
                </div>
              </div>
              <div className="mt-4 flex flex-wrap justify-end space-x-2">
                {/* View Key History button - For both staff and guests */}
                <button
                  onClick={() => handleViewKeyEvents(key.id)}
                  className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-xs font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  View History
                </button>

                {key.is_active && (
                  <button
                    onClick={() => handleDeactivate(key.id)}
                    disabled={processingKey}
                    className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                  >
                    Deactivate
                  </button>
                )}
                
                {!key.is_active && (
                  <button
                    onClick={() => handleActivate(key.id)}
                    disabled={processingKey}
                    className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-green-700 bg-green-100 hover:bg-green-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                  >
                    Activate
                  </button>
                )}
                
                {isStaff && (
                  <>
                    <button
                      onClick={() => {
                        setSelectedKey(key.id);
                        setIsExtendModalOpen(true);
                        // Set default extended date to 1 day after current valid_until
                        setExtendDate(getDefaultEndDate(key.valid_until));
                        // Set default time from current valid_until
                        setExtendTime(getDefaultEndTime(key.valid_until));
                      }}
                      disabled={processingKey}
                      className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      Extend
                    </button>
                    
                    <button 
                      onClick={() => handleOpenEmailModal(key)}
                      disabled={processingKey || sendingEmail}
                      className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-gray-700 bg-gray-100 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                    >
                      <svg className="mr-1 h-4 w-4 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                      Send Email
                    </button>
                    <button
                      onClick={() => {
                        setSelectedKeyForSMS(key.id);
                        setShowSMSModal(true);
                      }}
                      className="inline-flex items-center px-2 py-1 ml-2 text-xs font-medium text-green-700 bg-green-100 rounded-md hover:bg-green-200"
                    >
                      <svg className="w-4 h-4 mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
                      </svg>
                      SMS
                    </button>
                  </>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
      
      {/* Modal for extending key validity */}
      {isExtendModalOpen && (
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
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      Extend Key Validity
                    </h3>
                    <div className="mt-2">
                      <p className="text-sm text-gray-500">
                        Choose a new end date and time for the key validity.
                      </p>
                    </div>
                    <div className="mt-4 space-y-4">
                      <div>
                        <label htmlFor="extend-date" className="block text-sm font-medium text-gray-700">
                          New End Date
                        </label>
                        <input
                          type="date"
                          id="extend-date"
                          name="extend-date"
                          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                          value={extendDate}
                          onChange={(e) => setExtendDate(e.target.value)}
                          min={new Date().toISOString().split('T')[0]}
                          required
                        />
                      </div>
                      <div>
                        <label htmlFor="extend-time" className="block text-sm font-medium text-gray-700">
                          New End Time
                        </label>
                        <input
                          type="time"
                          id="extend-time"
                          name="extend-time"
                          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                          value={extendTime}
                          onChange={(e) => setExtendTime(e.target.value)}
                          required
                        />
                      </div>
                      <div className="text-sm text-gray-500">
                        The key will be valid until: {extendDate} {extendTime}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  className={`w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm ${
                    processingKey ? 'opacity-75 cursor-not-allowed' : ''
                  }`}
                  onClick={handleExtendSubmit}
                  disabled={processingKey || !extendDate || !extendTime}
                >
                  {processingKey ? 'Processing...' : 'Extend Key'}
                </button>
                <button
                  type="button"
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                  onClick={() => {
                    setIsExtendModalOpen(false);
                    setSelectedKey(null);
                  }}
                  disabled={processingKey}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Key Events Modal */}
      <KeyEventsModal 
        keyId={viewingKeyId} 
        isOpen={viewingKeyId !== null}
        onClose={() => setViewingKeyId(null)} 
      />
      
      {/* SMS Modal */}
      {showSMSModal && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-green-100 sm:mx-0 sm:h-10 sm:w-10">
                    <svg className="h-6 w-6 text-green-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      Send Digital Key via SMS
                    </h3>
                    <div className="mt-2">
                      <p className="text-sm text-gray-500">
                        Enter phone numbers to send the digital key via SMS.
                      </p>
                    </div>
                    <div className="mt-4">
                      <div className="space-y-3">
                        {phoneNumbers.map((phone, index) => (
                          <div key={index} className="flex items-center">
                            <input
                              type="tel"
                              className="shadow-sm focus:ring-green-500 focus:border-green-500 block w-full sm:text-sm border-gray-300 rounded-md"
                              placeholder="Phone number (with country code)"
                              value={phone}
                              onChange={(e) => {
                                const newPhones = [...phoneNumbers];
                                newPhones[index] = e.target.value;
                                setPhoneNumbers(newPhones);
                              }}
                            />
                            
                            {phoneNumbers.length > 1 && (
                              <button
                                type="button"
                                className="ml-2 inline-flex items-center p-1 border border-transparent rounded-full text-red-600 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                                onClick={() => {
                                  const newPhones = phoneNumbers.filter((_, i) => i !== index);
                                  setPhoneNumbers(newPhones);
                                }}
                              >
                                <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                              </button>
                            )}
                          </div>
                        ))}
                        
                        <button
                          type="button"
                          className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                          onClick={() => setPhoneNumbers([...phoneNumbers, ''])}
                        >
                          <svg className="h-4 w-4 mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                          </svg>
                          Add Another Phone Number
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  className={`w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-green-600 text-base font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 sm:ml-3 sm:w-auto sm:text-sm ${
                    sendingSMS ? 'opacity-75 cursor-not-allowed' : ''
                  }`}
                  onClick={handleSendSMS}
                  disabled={sendingSMS}
                >
                  {sendingSMS ? 'Sending...' : 'Send SMS'}
                </button>
                <button
                  type="button"
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                  onClick={() => {
                    setShowSMSModal(false);
                    setSelectedKeyForSMS(null);
                  }}
                  disabled={sendingSMS}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Email Modal */}
      {showEmailModal && (
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
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      Send Digital Key via Email
                    </h3>
                    <div className="mt-2">
                      <p className="text-sm text-gray-500">
                        Send the digital key to the default email or enter a custom email address
                      </p>
                    </div>
                    <div className="mt-4">
                      {emailInfo && (
                        <div className="mb-4 bg-gray-50 p-4 rounded-md">
                          <p className="text-sm font-medium text-gray-700">Guest: {emailInfo.name}</p>
                          <p className="text-sm text-gray-600">Default Email: {emailInfo.email}</p>
                          
                          <div className="mt-3">
                            <button
                              type="button"
                              className="inline-flex items-center px-2.5 py-1.5 border border-transparent text-xs font-medium rounded text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                              onClick={() => handleSendEmail(selectedKeyForEmail)}
                              disabled={processingKey || sendingEmail}
                            >
                              {processingKey || sendingEmail ? 'Sending...' : 'Use Default Email'}
                            </button>
                          </div>
                        </div>
                      )}
                      <div className="space-y-3">
                        <div>
                          <label htmlFor="custom-email" className="block text-sm font-medium text-gray-700">
                            Use Different Email Address:
                          </label>
                          <input
                            type="email"
                            id="custom-email"
                            className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                            placeholder="Enter custom email address"
                            value={customEmail}
                            onChange={(e) => setCustomEmail(e.target.value)}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  className={`w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm ${
                    sendingEmail ? 'opacity-75 cursor-not-allowed' : ''
                  }`}
                  onClick={() => handleSendEmail(selectedKeyForEmail, customEmail)}
                  disabled={sendingEmail || !customEmail}
                >
                  {sendingEmail ? 'Sending...' : 'Send to Custom Email'}
                </button>
                <button
                  type="button"
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                  onClick={() => {
                    setShowEmailModal(false);
                    setSelectedKeyForEmail(null);
                    setCustomEmail('');
                  }}
                  disabled={sendingEmail || processingKey}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default DigitalKeyList;
