import React from 'react';

const LOG_SOURCES = [
  { id: 'all', label: 'All Logs', color: 'gray' },
  { id: 'auth', label: 'Auth', color: 'blue' },
  { id: 'ufw', label: 'UFW', color: 'green' },
  { id: 'kern', label: 'Kern', color: 'purple' },
  { id: 'syslog', label: 'Syslog', color: 'orange' },
  { id: 'messages', label: 'Messages', color: 'indigo' },
];

const LogSourceTabs = ({ activeSource, onSourceChange }) => {
  const getTabClasses = (source) => {
    const baseClasses = "px-4 py-2 font-medium text-sm transition-colors border-b-2 -mb-px";
    if (activeSource === source.id) {
      // Active tab - use specific color classes
      const colorMap = {
        gray: "border-gray-600 text-gray-600",
        blue: "border-blue-600 text-blue-600",
        green: "border-green-600 text-green-600",
        purple: "border-purple-600 text-purple-600",
        orange: "border-orange-600 text-orange-600",
        indigo: "border-indigo-600 text-indigo-600",
      };
      return `${baseClasses} ${colorMap[source.color] || colorMap.gray}`;
    }
    return `${baseClasses} border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300`;
  };

  return (
    <div className="flex items-center gap-2 mb-4 border-b border-gray-200">
      {LOG_SOURCES.map((source) => (
        <button
          key={source.id}
          onClick={() => onSourceChange(source.id)}
          className={getTabClasses(source)}
        >
          {source.label}
        </button>
      ))}
    </div>
  );
};

export default LogSourceTabs;

