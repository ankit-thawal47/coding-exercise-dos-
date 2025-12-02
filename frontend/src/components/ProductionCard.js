import React, { useState } from 'react';
import ProductionItemModal from './ProductionItemModal';

const ProductionCard = ({ item }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleViewDetails = async () => {
    setIsLoading(true);
    try {
      const apiUrl = process.env.REACT_APP_API_URL || '';
      const response = await fetch(`${apiUrl}/api/production-items/${item.id}`);
      if (response.ok) {
        const itemDetails = await response.json();
        setSelectedItem(itemDetails);
        setIsModalOpen(true);
      } else {
        console.error('Failed to fetch item details');
        alert('Failed to load item details');
      }
    } catch (error) {
      console.error('Error fetching item details:', error);
      alert('Error loading item details');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedItem(null);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'in_production':
        return 'bg-blue-100 text-blue-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'delayed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  return (
    <>
    <div className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6">
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            {item.order_number || 'N/A'}
          </h3>
          <p className="text-sm text-gray-500">{item.style || 'No style'}</p>
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(item.status)}`}>
          {item.status?.replace('_', ' ') || 'Unknown'}
        </span>
      </div>

      {/* Details */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Fabric:</span>
          <span className="text-gray-900 font-medium">{item.fabric || 'N/A'}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Color:</span>
          <span className="text-gray-900 font-medium">{item.color || 'N/A'}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Quantity:</span>
          <span className="text-gray-900 font-medium">
            {item.quantity ? item.quantity.toLocaleString() : 'N/A'}
          </span>
        </div>
      </div>

      {/* Timeline */}
      {item.dates && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2">
            Timeline
          </h4>
          <div className="space-y-1">
            {Object.entries(item.dates).map(([stage, date]) => (
              <div key={stage} className="flex justify-between text-xs">
                <span className="text-gray-500 capitalize">{stage}:</span>
                <span className="text-gray-700">{formatDate(date)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <button 
          onClick={handleViewDetails}
          disabled={isLoading}
          className="w-full text-sm text-primary-600 hover:text-primary-500 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Loading...' : 'View Details →'}
        </button>
      </div>
    </div>
    
    {/* Modal */}
    <ProductionItemModal 
      item={selectedItem}
      isOpen={isModalOpen}
      onClose={handleCloseModal}
    />
    </>
  );
};

export default ProductionCard;