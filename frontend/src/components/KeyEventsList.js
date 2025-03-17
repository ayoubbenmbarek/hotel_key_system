// TODO continue this
// // frontend/src/components/KeyEventsList.js
// import React, { useState, useEffect } from 'react';
// import axios from 'axios';
// import { API_URL } from '../config';

// function KeyEventsList({ keyId }) {
//   const [events, setEvents] = useState([]);
//   const [loading, setLoading] = useState(true);
//   const [error, setError] = useState('');
  
//   useEffect(() => {
//     const fetchKeyEvents = async () => {
//       setLoading(true);
//       const token = localStorage.getItem('token');
      
//       try {
//         const response = await axios.get(`${API_URL}/keys/${keyId}/events`, {
//           headers: { 'Authorization': `Bearer ${token}` }
//         });
        
//         setEvents(Array.isArray(response.data) ? response.data : []);
//       } catch (err) {
//         console.error('Error fetching key events:', err);
//         setError(err.response?.data?.detail || 'Failed to load key events');
//       } finally {
//         setLoading(false);
//       }
//     };
    
//     if (keyId) {
//       fetchKeyEvents();
//     }
//   }, [keyId]);

//   const formatTimestamp = (timestamp) => {
//     const options = { 
//       year: 'numeric', 
//       month: 'short', 
//       day: 'numeric', 
//       hour: '2-digit', 
//       minute: '2-digit',
//       second: '2-digit'
//     };
//     return new Date(timestamp).toLocaleDateString(undefined, options);
//   };

//   const getEventStatusClass = (status) => {
//     switch (status.toLowerCase()) {
//       case 'success':
//         return 'bg-green-100 text-green-800';
//       case 'failure':
//       case 'error':
//         return 'bg-red-100 text-red-800';
//       case 'pending':
//         return 'bg-yellow-100 text-yellow-800';
//       default:
//         return 'bg-gray-100 text-gray-800';
//     }
//   };

//   const getEventTypeIcon = (eventType) => {
//     switch (eventType) {
//       case 'key_created':
//         return (
//           <svg className="h-5 w-5 text-blue-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
//             <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
//           </svg>
//         );
//       case 'key_activated':
//         return (
//           <svg className="h-5 w-5 text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
//             <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
//           </svg>
//         );
//       case 'key_deactivated':
//       case 'key_revoked':
//         return (
//           <svg className="h-5 w-5 text-red-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
//             <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
//           </svg>
//         );
//       case 'key_extended':
//         return (
//           <svg className="h-5 w-5 text-purple-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
//             <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.414-1.414L11 9.586V6z" clipRule="evenodd" />
//           </svg>
//         );
//       case 'access_attempt':
//         return (
//           <svg className="h-5 w-5 text-yellow-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
//             <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
//           </svg>
//         );
//       case 'key_email_sent':
//         return (
//           <svg className="h-5 w-5 text-indigo-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
//             <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
//             <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
//           </svg>
//         );
//       default:
//         return (
//           <svg className="h-5 w-5 text-gray-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
//             <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
//           </svg>
//         );
//     }
//   };

//   if (loading) {
//     return (
//       <div className="bg-white shadow sm:rounded-lg animate-pulse">
//         <div className="px-4 py-5 sm:p-6">
//           <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
//           <div className="space-y-3">
//             <div className="h-4 bg-gray-200 rounded w-full"></div>
//             <div className="h-4 bg-gray-200 rounded w-full"></div>
//             <div className="h-4 bg-gray-200 rounded w-5/6"></div>
//           </div>
//         </div>
//       </div>
//     );
//   }

//   if (error) {
//     return (
//       <div className="bg-white shadow sm:rounded-lg">
//         <div className="px-4 py-5 sm:p-6">
//           <div className="bg-red-50 p-4 rounded-md">
//             <div className="flex">
//               <div className="