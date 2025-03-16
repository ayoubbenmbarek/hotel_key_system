// frontend/src/components/Header.js
import React from 'react';

function Header({ user, onLogout }) {
  return (
    <header className="bg-white shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <h1 className="text-xl font-bold text-indigo-600">Hotel Virtual Key System</h1>
            </div>
          </div>
          <div className="flex items-center">
            <div className="ml-3 relative">
              <div className="flex items-center">
                <span className="hidden md:inline-block mr-2 text-sm font-medium text-gray-700">
                  {user?.first_name} {user?.last_name}
                </span>
                <button
                  type="button"
                  className="bg-white rounded-full flex text-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  id="user-menu"
                  aria-expanded="false"
                  aria-haspopup="true"
                >
                  <span className="sr-only">Open user menu</span>
                  <div className="h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-800 font-medium">
                    {user?.first_name?.charAt(0)}{user?.last_name?.charAt(0)}
                  </div>
                </button>
              </div>
            </div>
            <button
              onClick={onLogout}
              className="ml-4 px-3 py-1 text-sm font-medium text-gray-700 hover:text-gray-900 focus:outline-none"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;
