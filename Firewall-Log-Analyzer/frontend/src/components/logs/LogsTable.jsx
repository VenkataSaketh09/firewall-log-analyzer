import React, { useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getPaginationRowModel,
  flexRender,
  createColumnHelper,
} from '@tanstack/react-table';
import { FiChevronDown, FiChevronUp, FiEye } from 'react-icons/fi';
import { SEVERITY_COLORS, SEVERITY_BG_COLORS } from '../../utils/constants';
import { formatTimestamp, formatRelativeTime } from '../../utils/dateUtils';
import { formatSeverity, formatIP } from '../../utils/formatters';

const columnHelper = createColumnHelper();

const LogsTable = ({ logs, onSort, sortBy, sortOrder, onViewDetails, selectedLogs, onSelectLog, onSelectAll }) => {
  const getSeverityBadge = (severity) => {
    const severityUpper = severity?.toUpperCase() || 'UNKNOWN';
    const bgColor = SEVERITY_BG_COLORS[severityUpper] || SEVERITY_BG_COLORS.LOW;
    const textColor = SEVERITY_COLORS[severityUpper] || SEVERITY_COLORS.LOW;

    return (
      <span
        className="px-2 py-1 text-xs font-semibold rounded-full"
        style={{ backgroundColor: bgColor, color: textColor }}
      >
        {formatSeverity(severity)}
      </span>
    );
  };

  const columns = useMemo(
    () => [
      ...(onSelectAll
        ? [
            columnHelper.display({
              id: 'select',
              header: ({ table }) => (
                <input
                  type="checkbox"
                  checked={table.getIsAllRowsSelected()}
                  onChange={(e) => {
                    table.toggleAllRowsSelected(e.target.checked);
                    if (onSelectAll) {
                      onSelectAll(e.target.checked);
                    }
                  }}
                  className="rounded border-gray-300 text-primary-500 focus:ring-primary-500"
                />
              ),
              cell: ({ row }) => (
                <input
                  type="checkbox"
                  checked={row.getIsSelected()}
                  onChange={(e) => {
                    row.toggleSelected(e.target.checked);
                    if (onSelectLog) {
                      onSelectLog(row.original.id, e.target.checked);
                    }
                  }}
                  className="rounded border-gray-300 text-primary-500 focus:ring-primary-500"
                />
              ),
              enableSorting: false,
            }),
          ]
        : []),
      columnHelper.accessor('timestamp', {
        header: () => (
          <div className="flex items-center gap-1">
            Timestamp
            {sortBy === 'timestamp' && (
              sortOrder === 'asc' ? (
                <FiChevronUp className="w-4 h-4" />
              ) : (
                <FiChevronDown className="w-4 h-4" />
              )
            )}
          </div>
        ),
        cell: (info) => (
          <div>
            <div className="text-sm text-gray-900">{formatTimestamp(info.getValue())}</div>
            <div className="text-xs text-gray-500">{formatRelativeTime(info.getValue())}</div>
          </div>
        ),
        enableSorting: true,
      }),
      columnHelper.accessor('source_ip', {
        header: () => (
          <div className="flex items-center gap-1">
            Source IP
            {sortBy === 'source_ip' && (
              sortOrder === 'asc' ? (
                <FiChevronUp className="w-4 h-4" />
              ) : (
                <FiChevronDown className="w-4 h-4" />
              )
            )}
          </div>
        ),
        cell: (info) => (
          <span className="text-sm font-medium text-gray-900 font-mono">
            {formatIP(info.getValue())}
          </span>
        ),
        enableSorting: true,
      }),
      columnHelper.accessor('severity', {
        header: () => (
          <div className="flex items-center gap-1">
            Severity
            {sortBy === 'severity' && (
              sortOrder === 'asc' ? (
                <FiChevronUp className="w-4 h-4" />
              ) : (
                <FiChevronDown className="w-4 h-4" />
              )
            )}
          </div>
        ),
        cell: (info) => getSeverityBadge(info.getValue()),
        enableSorting: true,
      }),
      columnHelper.accessor('protocol', {
        header: () => (
          <div className="flex items-center gap-1">
            Protocol
            {sortBy === 'protocol' && (
              sortOrder === 'asc' ? (
                <FiChevronUp className="w-4 h-4" />
              ) : (
                <FiChevronDown className="w-4 h-4" />
              )
            )}
          </div>
        ),
        cell: (info) => <span className="text-sm text-gray-900">{info.getValue() || 'N/A'}</span>,
        enableSorting: true,
      }),
      columnHelper.accessor('destination_port', {
        header: () => (
          <div className="flex items-center gap-1">
            Port
            {sortBy === 'destination_port' && (
              sortOrder === 'asc' ? (
                <FiChevronUp className="w-4 h-4" />
              ) : (
                <FiChevronDown className="w-4 h-4" />
              )
            )}
          </div>
        ),
        cell: (info) => <span className="text-sm text-gray-900">{info.getValue() || 'N/A'}</span>,
        enableSorting: true,
      }),
      columnHelper.display({
        id: 'actions',
        header: 'Action',
        cell: ({ row }) => (
          <button
            onClick={() => onViewDetails(row.original)}
            className="text-primary-600 hover:text-primary-800 flex items-center gap-1 transition-colors"
          >
            <FiEye className="w-4 h-4" />
            View
          </button>
        ),
        enableSorting: false,
      }),
    ],
    [sortBy, sortOrder, onSelectAll, onSelectLog, onViewDetails]
  );

  const table = useReactTable({
    data: logs,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    manualSorting: true,
    state: {
      sorting: [
        {
          id: sortBy,
          desc: sortOrder === 'desc',
        },
      ],
    },
    onSortingChange: (updater) => {
      if (onSort) {
        const newSorting = typeof updater === 'function' ? updater([]) : updater;
        if (newSorting.length > 0) {
          const sort = newSorting[0];
          onSort(sort.id, sort.desc ? 'desc' : 'asc');
        }
      }
    },
  });

  if (!logs || logs.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-12 text-center">
        <p className="text-gray-500">No logs found</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-neutral-50">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className={`px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${
                      header.column.getCanSort() ? 'cursor-pointer hover:bg-neutral-100' : ''
                    }`}
                    onClick={header.column.getToggleSortingHandler()}
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
    </div>
  );
};

export default LogsTable;
