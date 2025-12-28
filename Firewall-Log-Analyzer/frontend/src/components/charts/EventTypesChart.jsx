import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { CHART_COLORS } from '../../utils/constants';

const EventTypesChart = ({ data }) => {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No data available
      </div>
    );
  }

  // Transform data for chart
  const chartData = Object.entries(data)
    .map(([eventType, count]) => ({
      name: eventType.replace(/_/g, ' '),
      count: count,
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10); // Top 10 event types

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData} layout="vertical">
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis type="number" />
        <YAxis dataKey="name" type="category" width={150} />
        <Tooltip />
        <Legend />
        <Bar dataKey="count" fill={CHART_COLORS[0]} name="Event Count" />
      </BarChart>
    </ResponsiveContainer>
  );
};

export default EventTypesChart;

