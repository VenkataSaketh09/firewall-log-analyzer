import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { SEVERITY_COLORS } from '../../utils/constants';
import { formatDate } from '../../utils/dateUtils';

const IPTimelineChart = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-12 text-center">
        <p className="text-gray-500">No timeline data available</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Activity Timeline</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="timestamp"
            tickFormatter={(value) => formatDate(value, 'MM/DD HH:mm')}
          />
          <YAxis />
          <Tooltip
            labelFormatter={(value) => formatDate(value, 'YYYY-MM-DD HH:mm:ss')}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="count"
            stroke={SEVERITY_COLORS.HIGH}
            strokeWidth={2}
            name="Events"
            dot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default IPTimelineChart;

