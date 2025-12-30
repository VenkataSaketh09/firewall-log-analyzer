import React from 'react';

const SummaryCard = ({ title, value, icon: Icon, color = 'blue', subtitle, trend }) => {
  const colorClasses = {
    blue: {
      bg: 'bg-gradient-to-br from-blue-50 to-blue-100/50',
      border: 'border-blue-200/60',
      text: 'text-blue-700',
      icon: 'text-blue-600',
      gradient: 'from-blue-500 to-blue-600'
    },
    green: {
      bg: 'bg-gradient-to-br from-green-50 to-green-100/50',
      border: 'border-green-200/60',
      text: 'text-green-700',
      icon: 'text-green-600',
      gradient: 'from-green-500 to-green-600'
    },
    red: {
      bg: 'bg-gradient-to-br from-red-50 to-red-100/50',
      border: 'border-red-200/60',
      text: 'text-red-700',
      icon: 'text-red-600',
      gradient: 'from-red-500 to-red-600'
    },
    yellow: {
      bg: 'bg-gradient-to-br from-yellow-50 to-yellow-100/50',
      border: 'border-yellow-200/60',
      text: 'text-yellow-700',
      icon: 'text-yellow-600',
      gradient: 'from-yellow-500 to-yellow-600'
    },
    purple: {
      bg: 'bg-gradient-to-br from-purple-50 to-purple-100/50',
      border: 'border-purple-200/60',
      text: 'text-purple-700',
      icon: 'text-purple-600',
      gradient: 'from-purple-500 to-purple-600'
    },
  };

  const colorClass = colorClasses[color] || colorClasses.blue;

  return (
    <div className={`relative group rounded-xl border backdrop-blur-sm p-6 card-hover animate-fade-in-up ${
      colorClass.bg
    } ${colorClass.border} ${colorClass.text} shadow-card hover:shadow-card-hover transition-all duration-300 hover:z-10`}>
      {/* Subtle gradient overlay */}
      <div className={`absolute inset-0 bg-gradient-to-r ${colorClass.gradient} opacity-0 group-hover:opacity-5 rounded-xl transition-opacity duration-300`} />
      
      <div className="relative flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-semibold opacity-75 tracking-wide uppercase">{title}</p>
          <div className="flex items-baseline gap-2 mt-3">
            <p className="text-3xl font-bold tracking-tight">{value}</p>
            {trend && (
              <span className={`text-sm font-medium px-2 py-1 rounded-full ${
                trend > 0 ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
              }`}>
                {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}%
              </span>
            )}
          </div>
          {subtitle && (
            <p className="text-sm mt-2 opacity-70 font-medium">{subtitle}</p>
          )}
        </div>
        {Icon && (
          <div className="ml-4 relative">
            <div className={`p-3 rounded-xl bg-gradient-to-r ${colorClass.gradient} bg-opacity-10 group-hover:bg-opacity-20 transition-all duration-300`}>
              <Icon className={`w-6 h-6 ${colorClass.icon} group-hover:scale-110 transition-transform duration-200`} />
            </div>
          </div>
        )}
      </div>
      
      {/* Animated border on hover */}
      <div className={`absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-gradient-to-r ${colorClass.gradient} p-[1px]`}>
        <div className={`w-full h-full rounded-xl ${colorClass.bg}`} />
      </div>
    </div>
  );
};

export default SummaryCard;

