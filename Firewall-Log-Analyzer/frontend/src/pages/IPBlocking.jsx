import React, { useState } from 'react';
import { FiRefreshCw, FiX, FiShield, FiShieldOff, FiAlertCircle, FiCheckCircle, FiClock, FiZap } from 'react-icons/fi';
import { useBlockedIPs, useBlockIP, useUnblockIP } from '../hooks/useIPBlockingQueries';
import dayjs from 'dayjs';

const IPBlocking = () => {
  const [activeOnly, setActiveOnly] = useState(true);
  const [blockIPAddress, setBlockIPAddress] = useState('');
  const [blockReason, setBlockReason] = useState('');
  const [showBlockForm, setShowBlockForm] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Fetch all blocks (both active and inactive)
  const { data: blockedIPsData, isLoading, refetch } = useBlockedIPs(false);
  const blockMutation = useBlockIP();
  const unblockMutation = useUnblockIP();

  // Filter based on activeOnly state
  const allBlockedIPs = blockedIPsData?.blocked_ips || [];
  const activeBlockedIPs = allBlockedIPs.filter(ip => ip.is_active);
  const blockedIPs = activeOnly ? activeBlockedIPs : allBlockedIPs;
  const totalActiveCount = activeBlockedIPs.length;
  const totalAllCount = allBlockedIPs.length;

  const handleBlockIP = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!blockIPAddress.trim()) {
      setError('Please enter an IP address');
      return;
    }

    // Basic IP validation
    const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (!ipRegex.test(blockIPAddress.trim())) {
      setError('Please enter a valid IPv4 address (e.g., 192.168.1.1)');
      return;
    }

    try {
      await blockMutation.mutateAsync({
        ipAddress: blockIPAddress.trim(),
        reason: blockReason.trim() || null,
      });
      setSuccess(`IP ${blockIPAddress.trim()} blocked successfully`);
      setBlockIPAddress('');
      setBlockReason('');
      setShowBlockForm(false);
      refetch();
    } catch (err) {
      const errorMessage = err?.response?.data?.detail || err?.userMessage || err?.message || 'Failed to block IP';
      setError(errorMessage);
    }
  };

  const handleUnblockIP = async (ipAddress) => {
    if (!window.confirm(`Are you sure you want to unblock ${ipAddress}?`)) {
      return;
    }

    setError(null);
    setSuccess(null);

    try {
      await unblockMutation.mutateAsync({ ipAddress });
      setSuccess(`IP ${ipAddress} unblocked successfully`);
      refetch();
    } catch (err) {
      const errorMessage = err?.response?.data?.detail || err?.userMessage || err?.message || 'Failed to unblock IP';
      setError(errorMessage);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return dayjs(dateString).format('YYYY-MM-DD HH:mm:ss');
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4 sm:p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">IP Blocking</h1>
            <p className="text-gray-600 mt-1 text-sm sm:text-base">Manage blocked IP addresses and firewall rules</p>
          </div>
          <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
            <button
              onClick={() => refetch()}
              disabled={isLoading}
              className="px-3 sm:px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50 flex items-center gap-2 text-sm transition-colors"
            >
              <FiRefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">Refresh</span>
            </button>
            <button
              onClick={() => setShowBlockForm(true)}
              className="px-3 sm:px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 flex items-center gap-2 text-sm transition-colors"
            >
              <FiShield className="w-4 h-4" />
              <span className="hidden sm:inline">Block IP</span>
              <span className="sm:hidden">Block</span>
            </button>
          </div>
        </div>

        {/* Success/Error Messages */}
        {success && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md flex items-center gap-2 text-green-800">
            <FiCheckCircle className="w-5 h-5" />
            <span>{success}</span>
            <button onClick={() => setSuccess(null)} className="ml-auto">
              <FiX className="w-5 h-5" />
            </button>
          </div>
        )}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md flex items-center gap-2 text-red-800">
            <FiAlertCircle className="w-5 h-5" />
            <span>{error}</span>
            <button onClick={() => setError(null)} className="ml-auto">
              <FiX className="w-5 h-5" />
            </button>
          </div>
        )}

        {/* Block IP Form Modal */}
        {showBlockForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">Block IP Address</h2>
                <button
                  onClick={() => {
                    setShowBlockForm(false);
                    setBlockIPAddress('');
                    setBlockReason('');
                    setError(null);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <FiX className="w-6 h-6" />
                </button>
              </div>
              <form onSubmit={handleBlockIP}>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    IP Address <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={blockIPAddress}
                    onChange={(e) => setBlockIPAddress(e.target.value)}
                    placeholder="192.168.1.1"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Reason (Optional)
                  </label>
                  <textarea
                    value={blockReason}
                    onChange={(e) => setBlockReason(e.target.value)}
                    placeholder="e.g., Brute force attack detected"
                    rows="3"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => {
                      setShowBlockForm(false);
                      setBlockIPAddress('');
                      setBlockReason('');
                      setError(null);
                    }}
                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={blockMutation.isPending}
                    className="flex-1 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {blockMutation.isPending ? (
                      <>
                        <FiRefreshCw className="w-4 h-4 animate-spin" />
                        Blocking...
                      </>
                    ) : (
                      <>
                        <FiShield className="w-4 h-4" />
                        Block IP
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Filter Tabs */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveOnly(true)}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeOnly
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Active Blocks ({totalActiveCount})
            </button>
            <button
              onClick={() => setActiveOnly(false)}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                !activeOnly
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              All Blocks ({totalAllCount})
            </button>
          </nav>
        </div>

        {/* Blocked IPs Table */}
        {isLoading ? (
          <div className="text-center py-12">
            <FiRefreshCw className="w-8 h-8 animate-spin mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">Loading blocked IPs...</p>
          </div>
        ) : blockedIPs.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
            <FiShield className="w-12 h-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500 text-lg">No blocked IPs found</p>
            <p className="text-gray-400 mt-2">Click "Block IP" to add an IP address to the blacklist</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      IP Address
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[300px]">
                      Reason
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Blocked At
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Blocked By
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Unblocked At
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {blockedIPs.map((ip, index) => {
                    const isAutoBlocked = ip.blocked_by === 'auto_blocking_service' || (ip.reason && ip.reason.includes('AUTO-BLOCK'));
                    const reasonText = ip.reason 
                      ? (isAutoBlocked ? ip.reason.replace('AUTO-BLOCK: ', '') : ip.reason)
                      : 'N/A';
                    return (
                    <tr key={ip.ip_address || index} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900 font-mono">{ip.ip_address}</div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        {ip.is_active ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            <FiShield className="w-3 h-3 mr-1" />
                            Blocked
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            <FiShieldOff className="w-3 h-3 mr-1" />
                            Unblocked
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        {isAutoBlocked ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800" title="Automatically blocked by threat detection system">
                            <FiZap className="w-3 h-3 mr-1" />
                            Auto-Blocked
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            <FiShield className="w-3 h-3 mr-1" />
                            Manual
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-4">
                        <div className="text-sm text-gray-700 max-w-md">
                          {ip.reason ? (
                            <div 
                              className="break-words leading-relaxed"
                              title={reasonText}
                            >
                              {reasonText}
                            </div>
                          ) : (
                            <span className="text-gray-400">N/A</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-500 flex items-center gap-1.5">
                          <FiClock className="w-3.5 h-3.5 text-gray-400" />
                          <span className="font-mono text-xs">{formatDate(ip.blocked_at)}</span>
                        </div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-500">
                          <span className="font-medium">{ip.blocked_by || 'System'}</span>
                        </div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-500">
                          {ip.unblocked_at ? (
                            <span className="font-mono text-xs">{formatDate(ip.unblocked_at)}</span>
                          ) : (
                            <span className="text-gray-400">N/A</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-right text-sm font-medium">
                        {ip.is_active && (
                          <button
                            onClick={() => handleUnblockIP(ip.ip_address)}
                            disabled={unblockMutation.isPending}
                            className="text-blue-600 hover:text-blue-900 hover:underline flex items-center gap-1.5 ml-auto transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            title={`Unblock ${ip.ip_address}`}
                          >
                            <FiShieldOff className="w-4 h-4" />
                            <span>Unblock</span>
                          </button>
                        )}
                      </td>
                    </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default IPBlocking;

