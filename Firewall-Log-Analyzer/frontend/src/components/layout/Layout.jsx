import React from 'react';
import Sidebar from './Sidebar';

const Layout = ({ children }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-neutral-50 to-primary-50/20">
      <Sidebar />
      <main className="ml-64 transition-all duration-300 ease-in-out">
        <div className="p-4 lg:p-6 xl:p-8">
          {children}
        </div>
      </main>
    </div>
  );
};

export default Layout;

