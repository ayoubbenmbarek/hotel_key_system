// frontend/src/pages/NFCSimulatorPage.js
import React from 'react';
import { Link } from 'react-router-dom';
import NFCSimulator from '../components/NFCSimulator';

function NFCSimulatorPage() {
  return (
    <div className="min-h-screen bg-gray-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md mx-auto">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-extrabold text-gray-900">NFC Door Lock Simulator</h1>
          <p className="mt-2 text-sm text-gray-600">
            Simulate NFC authentication to test digital keys
          </p>
        </div>

        <NFCSimulator />

        <div className="mt-8 text-center">
          <Link
            to="/"
            className="text-indigo-600 hover:text-indigo-500 font-medium"
          >
            ← Back to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}

export default NFCSimulatorPage;
