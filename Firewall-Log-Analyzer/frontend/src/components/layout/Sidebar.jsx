import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  FiLayout, 
  FiFileText, 
  FiAlertTriangle, 
  FiBarChart2, 
  FiShield,
  FiChevronLeft,
  FiChevronRight,
  FiActivity,
  FiSettings
} from 'react-icons/fi';

const Sidebar = () => {
  const location = useLocation();
  const [isCollapsed, setIsCollapsed] = useState(false);

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: FiLayout },
    { path: '/logs', label: 'Logs', icon: FiFileText },
    { path: '/threats', label: 'Threats', icon: FiAlertTriangle },
    { path: '/reports', label: 'Reports', icon: FiBarChart2 },
  ];

  const isActive = (path) => {
    return location.pathname === path;
  };

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <div className={`fixed left-0 top-0 h-full bg-primary-500 text-white shadow-2xl transition-all duration-300 ease-in-out z-50 ${
      isCollapsed ? 'w-16' : 'w-64'
    }`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-primary-600/50">
        <div className={`flex items-center gap-3 transition-all duration-300 ${isCollapsed ? 'opacity-0 w-0' : 'opacity-100'}`}>
          <div className="w-10 h-10 bg-accent-500 rounded-xl flex items-center justify-center shadow-lg">
            <FiShield className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">
              FirewallAnalyzer
            </h1>
            <p className="text-xs text-neutral-300">Security Dashboard</p>
          </div>
        </div>
        <button
          onClick={toggleSidebar}
          className="p-2 rounded-lg hover:bg-primary-600/50 transition-colors focus-ring text-neutral-200 hover:text-white"
        >
          {isCollapsed ? (
            <FiChevronRight className="w-4 h-4" />
          ) : (
            <FiChevronLeft className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="mt-6 px-3">
        <ul className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            return (
              <li key={item.path}>
                <Link
                  to={item.path}
                  className={`flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 group relative ${
                    active
                      ? 'bg-accent-500 text-white shadow-lg shadow-accent-500/30'
                      : 'text-neutral-200 hover:bg-primary-600/50 hover:text-white'
                  }`}
                  title={isCollapsed ? item.label : ''}
                >
                  {active && (
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-white rounded-r-full" />
                  )}
                  <Icon className={`w-5 h-5 flex-shrink-0 ${active ? 'animate-bounce-subtle' : 'group-hover:scale-110'} transition-transform duration-200`} />
                  <span className={`font-medium transition-all duration-300 ${
                    isCollapsed ? 'opacity-0 w-0 overflow-hidden' : 'opacity-100'
                  }`}>
                    {item.label}
                  </span>
                  {active && !isCollapsed && (
                    <div className="ml-auto w-2 h-2 rounded-full bg-white animate-pulse" />
                  )}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Quick Stats */}
      {!isCollapsed && (
        <div className="mt-8 mx-3 p-4 bg-primary-600/30 backdrop-blur-sm rounded-xl border border-primary-400/20 animate-fade-in">
          <div className="flex items-center gap-2 mb-3">
            <FiActivity className="w-4 h-4 text-accent-400 animate-pulse" />
            <span className="text-sm font-medium text-neutral-200">System Status</span>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-neutral-300">Security Score</span>
              <span className="text-accent-300 font-semibold">95/100</span>
            </div>
            <div className="w-full bg-primary-700/50 rounded-full h-1.5 overflow-hidden">
              <div className="bg-accent-500 h-1.5 rounded-full w-[95%] animate-pulse-slow"></div>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-neutral-300">Active Threats</span>
              <span className="text-light-400 font-semibold">3</span>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="absolute bottom-4 left-0 right-0 px-3">
        <div className={`flex items-center gap-3 p-3 rounded-xl bg-primary-600/30 backdrop-blur-sm border border-primary-400/20 ${isCollapsed ? 'justify-center' : ''}`}>
          <div className="w-8 h-8 rounded-full bg-accent-500 flex items-center justify-center shadow-md">
            <FiSettings className="w-4 h-4 text-white" />
          </div>
          {!isCollapsed && (
            <div className="flex-1">
              <p className="text-sm font-medium text-white">Admin</p>
              <p className="text-xs text-neutral-300">System Administrator</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
