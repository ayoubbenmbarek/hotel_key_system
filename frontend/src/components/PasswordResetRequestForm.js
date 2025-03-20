// src/components/PasswordResetRequestForm.js
import React, { useState } from 'react';
import axios from 'axios';
import { API_URL } from '../config';

function PasswordResetRequestForm({ onCancel }) {
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  // Helper function to safely convert any error to a string
  const formatError = (err) => {
    if (typeof err === 'string') return err;
    if (err === null || err === undefined) return 'An unknown error occurred';
    if (typeof err === 'object') {
      // Try specific error object formats
      if (err.message) return err.message;
      if (err.msg) return err.msg;
      if (err.detail) {
        if (typeof err.detail === 'string') return err.detail;
        if (Array.isArray(err.detail)) return err.detail.map(d => formatError(d)).join(', ');
        return formatError(err.detail);
      }
      // Last resort: stringify the object
      try {
        return JSON.stringify(err);
      } catch (e) {
        return 'Error object could not be formatted';
      }
    }
    return String(err);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError('');
    setMessage('');

    try {
      const response = await axios.post(
        `${API_URL}/auth/password-reset-request?email=${encodeURIComponent(email)}`,
        {}, // Empty body
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );
      
      setMessage(response.data.message || 'Password reset instructions have been sent to your email if it exists in our system.');
    } catch (err) {
      console.error('Password reset request error:', err);
      
      let errorMessage;
      
      if (err.response && err.response.data) {
        errorMessage = formatError(err.response.data);
      } else if (err.request) {
        errorMessage = 'No response received from server. Please check your connection.';
      } else {
        errorMessage = err.message || 'An error occurred while processing your request.';
      }
      
      setError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mt-8 space-y-6">
      <div>
        <h2 className="mt-6 text-center text-2xl font-bold text-gray-900">Reset Your Password</h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Enter your email address and we'll send you instructions to reset your password.
        </p>
      </div>

      {message && (
        <div className="bg-green-50 p-4 rounded-md">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-green-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-green-800">{message}</p>
            </div>
          </div>
        </div>
      )}

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

      <form className="space-y-6" onSubmit={handleSubmit}>
        <div>
          <label htmlFor="email" className="sr-only">Email address</label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            className="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
            placeholder="Email address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={onCancel}
            className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
          >
            Back to Login
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="group relative w-40 flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            {isSubmitting ? 'Sending...' : 'Reset Password'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default PasswordResetRequestForm;
