// frontend/src/components/DigitalKeyList.js
import React, { useState } from 'react';

function DigitalKeyList({ keys, loading, onActivate, onDeactivate, onExtend, onSendEmail, isStaff, onRefresh }) {
  const [expandedId, setExpandedId] = useState(null);
  const [selectedKey, setSelectedKey] = useState(null);
  const [showExtendModal, setShowExtendModal] = useState(false);
  const [newEndDate, setNewEndDate] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const handleExtendKey = async () => {
    if (!selectedKey || !newEndDate) return;
    
    setIsProcessing(true);
    try {
      await onExtend(selectedKey.id, newEndDate);
      setShowExtendModal(false);
      setSelectedKey(null);
    } catch (err) {
      console.error('Error extending key validity:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  const openExtendModal = (key) => {
    setSelectedKey(key);
    // Set default new end date to current valid_until + 1 day
    const currentEndDate = new Date(key.valid_until);
    currentEndDate.setDate(currentEndDate.getDate() + 1);
    setNewEndDate(currentEndDate.toISOString().split('T')[0]);
    setShowExtendModal(true);
  };

  // Get key status label and color
  const getStatusLabel = (status, isActive) => {
    if (!isActive) {
      return { text: 'Inactive', color: 'bg-gray-100 text-gray-800' };
    }
    
    switch (status) {
      case 'created':
        return { text: 'Created', color: 'bg-blue-100 text-blue-800' };
      case 'active':
        return { text: 'Active', color: 'bg-green-100 text-green-800' };
      case 'expired':
        return { text: 'Expired', color: 'bg-red-100 text-red-800' };
      case 'revoked':
        return { text: 'Revoked', color: 'bg-red-100 text-red-800' };
      default:
        return { text: status, color: 'bg-gray-100 text-gray-800' };
    }
  };

  // Format date for display
  const formatDate = (dateString) => {
    const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    return new Date(dateString).toLocaleDateString(undefined, options);
  };

  // Get pass type badge
  const getPassTypeBadge = (passType) => {
    switch (passType) {
      case 'apple':
        return { 
          text: 'Apple Wallet', 
          color: 'bg-black text-white',
          icon: (
            <svg className="h-3 w-3 mr-1" viewBox="0 0 15 18" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
              <path d="M12.6281 9.41766C12.6509 7.96766 13.4701 6.63184 14.7568 5.82209C13.8946 4.56432 12.4375 3.78432 10.9053 3.71578C9.2839 3.65072 7.6132 4.77899 6.79584 4.77899C5.96167 4.77899 4.55686 3.73578 3.23584 3.73578C1.25011 3.76935 -0.773095 5.28395 -0.773095 8.37899C-0.773095 9.43899 -0.59486 10.535 -0.238328 11.6672C0.254115 13.2117 2.01206 17.1 3.83852 16.9905C4.70624 16.9445 5.31281 16.3266 6.48852 16.3266C7.63738 16.3266 8.19584 16.9905 9.19281 16.9905C11.0351 16.9539 12.6224 13.4398 13.0896 11.8898C10.7886 10.6188 10.6281 9.5094 10.6281 9.41766H12.6281Z" />
              <path d="M8.71424 2.62578C9.42138 1.78148 9.82138 0.66899 9.71424 -0.437988C8.7085 -0.303267 7.76999 0.190858 7.0685 0.9906C6.40279 1.74984 5.92565 2.87328 6.04279 3.95634C7.10714 4.04148 8.0285 3.54634 8.71424 2.62578V2.62578Z" />
            </svg>
          )
        };
      case 'google':
        return { 
          text: 'Google Wallet', 
          color: 'bg-blue-600 text-white',
          icon: (
            <svg className="h-3 w-3 mr-1" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
              <path d="M21.64 11.2c0-.63-.06-1.25-.16-1.84H12v3.49h5.38a4.66 4.66 0 0 1-2 3.01v2.5h3.2c1.88-1.73 2.95-4.29 2.95-7.16z"/>
              <path d="M12 22c2.67 0 4.93-.89 6.57-2.4l-3.2-2.5c-.89.6-2.01.95-3.37.95-2.6 0-4.8-1.75-5.59-4.11H3.06v2.58A9.97 9.97 0 0 0 12 22z"/>
              <path d="M6.41 13.94A6 6 0 0 1 6.14 12c0-.67.1-1.32.27-1.94V7.48H3.06A9.97 9.97 0 0 0 2 12c0 1.62.39 3.15 1.06 4.52l3.35-2.58z"/>
              <path d="M12 5.94c1.47 0 2.8.5 3.83 1.5l2.84-2.84C16.95 2.94 14.7 2 12 2 8.13 2 4.77 4.05 3.06 7.48l3.35 2.58c.79-2.36 2.99-4.12 5.59-4.12z"/>
            </svg>
          )
        };
      default:
        return { text: passType, color: 'bg-gray-100 text-gray-800', icon: null };
    }
  };

  // Check if key is active
  const isKeyActive = (key) => {
    return key.is_active;
  };

  // Check if key is currently valid based on dates
  const isKeyCurrentlyValid = (key) => {
    const now = new Date();
    const validFrom = new Date(key.valid_from);
    const validUntil = new Date(key.valid_until);
    
    return now >= validFrom && now <= validUntil;
  };

  return (
    <div className="bg-white shadow overflow-hidden sm:rounded-md">
      <div className="px-4 py-5 sm:px-6 flex justify-between items-center">
        <h3 className="text-lg leading-6 font-medium text-gray-900">Digital Keys</h3>
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
          <p className="mt-2 text-gray-500">Loading digital keys...</p>
        </div>
      ) : keys.length === 0 ? (
        <div className="text-center py-10">
          <p className="text-gray-500">No digital keys found.</p>
        </div>
      ) : (
        <ul className="divide-y divide-gray-200">
          {keys.map((key) => {
            const statusLabel = getStatusLabel(key.status, key.is_active);
            const passTypeBadge = getPassTypeBadge(key.pass_type);
            const isActive = isKeyActive(key);
            const isValid = isKeyCurrentlyValid(key);
            
            return (
              <li key={key.id}>
                <div 
                  className="block hover:bg-gray-50 cursor-pointer transition duration-150 ease-in-out"
                  onClick={() => setExpandedId(expandedId === key.id ? null : key.id)}
                >
                  <div className="px-4 py-4 sm:px-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <p className="text-sm font-medium text-indigo-600 truncate">
                          Key {key.key_uuid.substring(0, 8)}...
                        </p>
                        <div className={`ml-2 flex-shrink-0 flex`}>
                          <p className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${statusLabel.color}`}>
                            {statusLabel.text}
                          </p>
                        </div>
                        <div className={`ml-2 flex-shrink-0 flex`}>
                          <p className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full flex items-center ${passTypeBadge.color}`}>
                            {passTypeBadge.icon}
                            {passTypeBadge.text}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        {key.pass_url && (
                          <a
                            href={key.pass_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="inline-flex items-center px-2.5 py-1.5 border border-gray-300 text-xs leading-4 font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:border-blue-300 focus:shadow-outline-blue"
                          >
                            <svg className="mr-1 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                            </svg>
                            Download
                          </a>
                        )}
                        
                        {isStaff && (
                          <>
                            {!isActive && isValid && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onActivate(key.id);
                                }}
                                className="inline-flex items-center px-2.5 py-1.5 border border-transparent text-xs leading-4 font-medium rounded text-white bg-green-600 hover:bg-green-500 focus:outline-none focus:border-green-700 focus:shadow-outline-green"
                              >
                                Activate
                              </button>
                            )}
                            
                            {isActive && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onDeactivate(key.id);
                                }}
                                className="inline-flex items-center px-2.5 py-1.5 border border-transparent text-xs leading-4 font-medium rounded text-white bg-red-600 hover:bg-red-500 focus:outline-none focus:border-red-700 focus:shadow-outline-red"
                              >
                                Deactivate
                              </button>
                            )}
                            
                            {isActive && isValid && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  openExtendModal(key);
                                }}
                                className="inline-flex items-center px-2.5 py-1.5 border border-transparent text-xs leading-4 font-medium rounded text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:border-indigo-700 focus:shadow-outline-indigo"
                              >
                                Extend
                              </button>
                            )}
                          </>
                        )}
                        
                        {isStaff && key.pass_url && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onSendEmail(key.id);
                            }}
                            className="inline-flex items-center px-2.5 py-1.5 border border-gray-300 text-xs leading-4 font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:border-blue-300 focus:shadow-outline-blue"
                          >
                            <svg className="mr-1 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                            </svg>
                            Email
                          </button>
                        )}
                        
                        <svg 
                          className={`h-5 w-5 text-gray-400 transition-transform duration-200 ${expandedId === key.id ? 'transform rotate-180' : ''}`} 
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
                          {key.reservation?.user?.first_name} {key.reservation?.user?.last_name}
                        </p>
                        <p className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0 sm:ml-6">
                          <svg className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                          </svg>
                          Room {key.reservation?.room?.room_number}
                        </p>
                      </div>
                      <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                        <svg className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                        </svg>
                        <p>
                          Valid from {formatDate(key.valid_from)} to {formatDate(key.valid_until)}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Expanded details */}
                {expandedId === key.id && (
                  <div className="px-4 py-4 sm:px-6 bg-gray-50 border-t border-gray-200">
                    <dl className="grid grid-cols-1 gap-x-4 gap-y-4 sm:grid-cols-2">
                      <div className="sm:col-span-1">
                        <dt className="text-sm font-medium text-gray-500">Key UUID</dt>
                        <dd className="mt-1 text-sm text-gray-900 font-mono">{key.key_uuid}</dd>
                      </div>
                      <div className="sm:col-span-1">
                        <dt className="text-sm font-medium text-gray-500">Status</dt>
                        <dd className="mt-1 text-sm text-gray-900">{key.status} ({key.is_active ? 'Active' : 'Inactive'})</dd>
                      </div>
                      <div className="sm:col-span-1">
                        <dt className="text-sm font-medium text-gray-500">Valid From</dt>
                        <dd className="mt-1 text-sm text-gray-900">{formatDate(key.valid_from)}</dd>
                      </div>
                      <div className="sm:col-span-1">
                        <dt className="text-sm font-medium text-gray-500">Valid Until</dt>
                        <dd className="mt-1 text-sm text-gray-900">{formatDate(key.valid_until)}</dd>
                      </div>
                      <div className="sm:col-span-1">
                        <dt className="text-sm font-medium text-gray-500">Created At</dt>
                        <dd className="mt-1 text-sm text-gray-900">{formatDate(key.created_at)}</dd>
                      </div>
                      <div className="sm:col-span-1">
                        <dt className="text-sm font-medium text-gray-500">Last Used</dt>
                        <dd className="mt-1 text-sm text-gray-900">{key.last_used ? formatDate(key.last_used) : 'Never'}</dd>
                      </div>
                      <div className="sm:col-span-1">
                        <dt className="text-sm font-medium text-gray-500">Access Count</dt>
                        <dd className="mt-1 text-sm text-gray-900">{key.access_count || 0} times</dd>
                      </div>
                      <div className="sm:col-span-1">
                        <dt className="text-sm font-medium text-gray-500">Pass Type</dt>
                        <dd className="mt-1 text-sm text-gray-900">{key.pass_type}</dd>
                      </div>
                      {key.pass_url && (
                        <div className="sm:col-span-2">
                          <dt className="text-sm font-medium text-gray-500">Pass URL</dt>
                          <dd className="mt-1 text-sm text-gray-900">
                            <a 
                              href={key.pass_url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-indigo-600 hover:text-indigo-500 break-all"
                            >
                              {key.pass_url}
                            </a>
                          </dd>
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
      
      {/* Extend Key Modal */}
      {showExtendModal && selectedKey && (
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
                    Extend Key Validity
                  </h3>
                  <div className="mt-2">
                    <p className="text-sm text-gray-500">
                      Extend the validity period for the digital key {selectedKey.key_uuid.substring(0, 8)}...
                    </p>
                  </div>
                </div>
                
                <div className="mt-5 sm:mt-6 space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Current Valid Until</label>
                    <p className="mt-1 text-sm text-gray-900">{formatDate(selectedKey.valid_until)}</p>
                  </div>
                  
                  <div>
                    <label htmlFor="new-end-date" className="block text-sm font-medium text-gray-700">New End Date</label>
                    <div className="mt-1">
                      <input
                        type="date"
                        id="new-end-date"
                        name="new-end-date"
                        className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                        value={newEndDate}
                        onChange={(e) => setNewEndDate(e.target.value)}
                        min={new Date().toISOString().split('T')[0]}
                      />
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="mt-5 sm:mt-6 grid grid-cols-2 gap-3">
                <button
                  type="button"
                  className="w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:text-sm"
                  onClick={() => setShowExtendModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:text-sm"
                  onClick={handleExtendKey}
                  disabled={isProcessing || !newEndDate}
                >
                  {isProcessing ? 'Extending...' : 'Extend Key'}
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
