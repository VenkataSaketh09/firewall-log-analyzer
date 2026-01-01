import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const LogsOverTimeChart = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No data available
      </div>
    );
  }

  // Transform data for chart
  const chartData = data
    .filter((item) => item && item.hour) // Filter out invalid items
    .map((item) => ({
    time: new Date(item.hour).toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    }),
      count: item.count || 0,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="time" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line 
          type="monotone" 
          dataKey="count" 
          stroke="#3b82f6" 
          strokeWidth={2}
          name="Log Count"
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default LogsOverTimeChart;

