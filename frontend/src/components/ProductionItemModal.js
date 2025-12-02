import React from 'react';

const ProductionItemModal = ({ item, isOpen, onClose }) => {
  if (!isOpen || !item) return null;

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'in_production':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'delayed':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getTimelineStageColor = (stage, hasDate) => {
    if (!hasDate) return 'bg-gray-100 text-gray-500';
    
    switch (stage) {
      case 'fabric':
        return 'bg-purple-100 text-purple-800';
      case 'cutting':
        return 'bg-orange-100 text-orange-800';
      case 'sewing':
        return 'bg-blue-100 text-blue-800';
      case 'shipping':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              {item.order_number || 'Production Item'}
            </h2>
            <p className="text-gray-500 mt-1">{item.style || 'No style specified'}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Status Badge */}
          <div className="mb-6">
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(item.status)}`}>
              <div className="w-2 h-2 bg-current rounded-full mr-2"></div>
              {item.status?.replace('_', ' ')?.toUpperCase() || 'UNKNOWN'}
            </span>
          </div>

          {/* Main Details Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            {/* Product Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 border-b border-gray-200 pb-2">
                Product Information
              </h3>
              
              <div className="space-y-3">
                <div>
                  <label className="text-sm font-medium text-gray-500">Fabric</label>
                  <p className="text-gray-900 mt-1">{item.fabric || 'Not specified'}</p>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-500">Color</label>
                  <p className="text-gray-900 mt-1">{item.color || 'Not specified'}</p>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-500">Quantity</label>
                  <p className="text-gray-900 mt-1 text-xl font-semibold">
                    {item.quantity ? item.quantity.toLocaleString() : 'N/A'} pieces
                  </p>
                </div>

                {item.brand && (
                  <div>
                    <label className="text-sm font-medium text-gray-500">Brand</label>
                    <p className="text-gray-900 mt-1">{item.brand}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Metadata */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 border-b border-gray-200 pb-2">
                Details
              </h3>
              
              <div className="space-y-3">
                {item.source_file && (
                  <div>
                    <label className="text-sm font-medium text-gray-500">Source File</label>
                    <p className="text-gray-900 mt-1 font-mono text-sm bg-gray-50 px-2 py-1 rounded">
                      {item.source_file}
                    </p>
                  </div>
                )}
                
                {item.created_at && (
                  <div>
                    <label className="text-sm font-medium text-gray-500">Created</label>
                    <p className="text-gray-900 mt-1">{formatDate(item.created_at)}</p>
                  </div>
                )}
                
                <div>
                  <label className="text-sm font-medium text-gray-500">Item ID</label>
                  <p className="text-gray-900 mt-1 font-mono text-sm">{item.id}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Timeline */}
          {item.dates && Object.keys(item.dates).length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 border-b border-gray-200 pb-2 mb-4">
                Production Timeline
              </h3>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {Object.entries(item.dates).map(([stage, date]) => (
                  <div key={stage} className="text-center">
                    <div className={`inline-flex items-center justify-center w-12 h-12 rounded-full text-sm font-medium ${getTimelineStageColor(stage, date)}`}>
                      {stage === 'fabric' && '🧵'}
                      {stage === 'cutting' && '✂️'}
                      {stage === 'sewing' && '🪡'}
                      {stage === 'shipping' && '📦'}
                    </div>
                    <h4 className="mt-2 text-sm font-medium text-gray-900 capitalize">{stage}</h4>
                    <p className="text-xs text-gray-500 mt-1">
                      {formatDate(date)}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Close
          </button>
          <button className="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500">
            Edit Item
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProductionItemModal;