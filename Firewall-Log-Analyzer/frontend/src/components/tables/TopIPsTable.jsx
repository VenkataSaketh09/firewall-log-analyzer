import React, { useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  createColumnHelper,
} from '@tanstack/react-table';
import { SEVERITY_COLORS } from '../../utils/constants';
import { formatIP, formatNumber } from '../../utils/formatters';
import { formatRelativeTime } from '../../utils/dateUtils';

const columnHelper = createColumnHelper();

const TopIPsTable = ({ topIPs }) => {
  const columns = useMemo(
    () => [
      columnHelper.accessor('source_ip', {
        header: 'IP Address',
        cell: (info) => (
          <span className="font-mono text-sm font-medium text-gray-900">
            {formatIP(info.getValue())}
          </span>
        ),
      }),
      columnHelper.accessor('total_logs', {
        header: 'Total Logs',
        cell: (info) => (
          <span className="text-sm text-gray-900">{formatNumber(info.getValue())}</span>
        ),
      }),
      columnHelper.accessor('severity_breakdown', {
        header: 'Severity Breakdown',
        cell: (info) => {
          const breakdown = info.getValue() || {};
          return (
            <div className="flex gap-2 flex-wrap">
              {Object.entries(breakdown).map(([severity, count]) => (
                <span
                  key={severity}
                  className="px-2 py-1 rounded text-xs font-medium"
                  style={{
                    backgroundColor: SEVERITY_COLORS[severity] + '20',
                    color: SEVERITY_COLORS[severity],
                  }}
                >
                  {severity}: {count}
                </span>
              ))}
            </div>
          );
        },
      }),
      columnHelper.accessor('last_seen', {
        header: 'Last Seen',
        cell: (info) => (
          <span className="text-sm text-gray-500">
            {info.getValue() ? formatRelativeTime(info.getValue()) : 'N/A'}
          </span>
        ),
      }),
    ],
    []
  );

  const table = useReactTable({
    data: topIPs || [],
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  if (!topIPs || topIPs.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No IP data available
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-neutral-50">
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th
                  key={header.id}
                  className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  {header.isPlaceholder
                    ? null
                    : flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id} className="hover:bg-neutral-50 transition-colors">
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="px-4 py-3 whitespace-nowrap">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TopIPsTable;
