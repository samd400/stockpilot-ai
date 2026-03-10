import React, { useState, useEffect } from 'react';
import { Warehouse, MapPin, Package, AlertTriangle, Plus, Search, Edit, Trash2 } from 'lucide-react';
import { inventoryAPI, productsAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

function Inventory() {
  const { hasPermission } = useAuth();
  const canWrite = hasPermission('inventory_write');
  const [activeTab, setActiveTab] = useState('stock');
  const [inventory, setInventory] = useState([]);
  const [locations, setLocations] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showStockModal, setShowStockModal] = useState(false);
  const [showLocationModal, setShowLocationModal] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [stockForm, setStockForm] = useState({ quantity: 0 });
  const [locationForm, setLocationForm] = useState({ name: '', type: 'warehouse', address: '' });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [invRes, prodRes, locRes] = await Promise.all([
        inventoryAPI.getAll(),
        productsAPI.getAll(),
        inventoryAPI.getLocations(),
      ]);
      setInventory(invRes.data);
      setProducts(prodRes.data);
      setLocations(locRes.data);
    } catch (error) {
      console.error('Error fetching inventory data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatus = (item) => {
    if (item.quantity === 0) return { label: 'Out of Stock', className: 'badge-danger' };
    if (item.quantity <= (item.reorder_level || 10)) return { label: 'Low Stock', className: 'badge-warning' };
    return { label: 'In Stock', className: 'badge-success' };
  };

  const totalProducts = inventory.length;
  const lowStockItems = inventory.filter(i => i.quantity > 0 && i.quantity <= (i.reorder_level || 10)).length;
  const outOfStock = inventory.filter(i => i.quantity === 0).length;
  const totalValue = inventory.reduce((sum, i) => {
    const product = products.find(p => p.id === i.product_id);
    return sum + (i.quantity * (product?.selling_price || 0));
  }, 0);

  const filteredInventory = inventory.filter(item =>
    (item.product_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (item.sku || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (item.location || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  const openStockModal = (item) => {
    setSelectedItem(item);
    setStockForm({ quantity: item.quantity });
    setShowStockModal(true);
  };

  const handleStockUpdate = async (e) => {
    e.preventDefault();
    try {
      await inventoryAPI.update(selectedItem.id, { quantity: Number(stockForm.quantity) });
      fetchData();
    } catch (error) {
      console.error('Error updating stock:', error);
      alert(error.response?.data?.detail || 'Failed to update stock');
    }
    setShowStockModal(false);
    setSelectedItem(null);
  };

  const handleLocationCreate = async (e) => {
    e.preventDefault();
    try {
      await inventoryAPI.createLocation(locationForm);
      fetchData();
    } catch (error) {
      console.error('Error creating location:', error);
      alert(error.response?.data?.detail || 'Failed to create location');
    }
    setShowLocationModal(false);
    setLocationForm({ name: '', type: 'warehouse', address: '' });
  };

  const handleLocationDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this location?')) return;
    try {
      await inventoryAPI.deleteLocation(id);
      fetchData();
    } catch (error) {
      console.error('Error deleting location:', error);
      alert('Failed to delete location');
    }
  };

  if (loading) {
    return <div className="loading">Loading inventory...</div>;
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Inventory</h1>
        <p style={{ color: '#64748b' }}>Track stock levels and manage storage locations</p>
      </div>

      {/* Stats Row */}
      <div className="stats-grid">
        <div className="stat-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <Package size={24} style={{ color: '#2563eb' }} />
            <span className="stat-label" style={{ marginBottom: 0 }}>Total Products</span>
          </div>
          <div className="stat-value">{totalProducts}</div>
        </div>
        <div className="stat-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <AlertTriangle size={24} style={{ color: '#f59e0b' }} />
            <span className="stat-label" style={{ marginBottom: 0 }}>Low Stock Items</span>
          </div>
          <div className="stat-value" style={{ color: '#f59e0b' }}>{lowStockItems}</div>
        </div>
        <div className="stat-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <Package size={24} style={{ color: '#ef4444' }} />
            <span className="stat-label" style={{ marginBottom: 0 }}>Out of Stock</span>
          </div>
          <div className="stat-value" style={{ color: '#ef4444' }}>{outOfStock}</div>
        </div>
        <div className="stat-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <Warehouse size={24} style={{ color: '#22c55e' }} />
            <span className="stat-label" style={{ marginBottom: 0 }}>Total Value</span>
          </div>
          <div className="stat-value">₹{totalValue.toLocaleString()}</div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '4px', marginBottom: '24px', borderBottom: '2px solid var(--border-color)' }}>
        <button
          className="btn"
          style={{
            borderRadius: '8px 8px 0 0',
            borderBottom: activeTab === 'stock' ? '2px solid var(--primary-color)' : '2px solid transparent',
            color: activeTab === 'stock' ? 'var(--primary-color)' : 'var(--text-secondary)',
            fontWeight: activeTab === 'stock' ? 600 : 400,
            background: activeTab === 'stock' ? 'var(--card-background)' : 'transparent',
          }}
          onClick={() => setActiveTab('stock')}
        >
          <Package size={16} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
          Stock Levels
        </button>
        <button
          className="btn"
          style={{
            borderRadius: '8px 8px 0 0',
            borderBottom: activeTab === 'locations' ? '2px solid var(--primary-color)' : '2px solid transparent',
            color: activeTab === 'locations' ? 'var(--primary-color)' : 'var(--text-secondary)',
            fontWeight: activeTab === 'locations' ? 600 : 400,
            background: activeTab === 'locations' ? 'var(--card-background)' : 'transparent',
          }}
          onClick={() => setActiveTab('locations')}
        >
          <MapPin size={16} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
          Locations
        </button>
      </div>

      {/* Stock Levels Tab */}
      {activeTab === 'stock' && (
        <div className="card">
          <div className="card-header">
            <div style={{ position: 'relative', flex: 1, maxWidth: '400px' }}>
              <Search size={20} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
              <input
                type="text"
                placeholder="Search by name, SKU, or location..."
                className="form-input"
                style={{ paddingLeft: '40px' }}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>

          {filteredInventory.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--text-secondary)' }}>
              <Package size={48} style={{ marginBottom: '16px', opacity: 0.4 }} />
              <p style={{ fontSize: '16px' }}>No inventory items found</p>
              <p style={{ fontSize: '14px' }}>Inventory records will appear here once products are stocked.</p>
            </div>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Product Name</th>
                  <th>SKU</th>
                  <th>Location</th>
                  <th>Quantity</th>
                  <th>Reorder Level</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredInventory.map((item) => {
                  const status = getStatus(item);
                  return (
                    <tr key={item.id}>
                      <td style={{ fontWeight: 500 }}>{item.product_name || 'Unknown Product'}</td>
                      <td style={{ color: 'var(--text-secondary)', fontFamily: 'monospace' }}>{item.sku || '-'}</td>
                      <td>
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                          <MapPin size={14} style={{ color: 'var(--text-secondary)' }} />
                          {item.location || '-'}
                        </span>
                      </td>
                      <td style={{ fontWeight: 600 }}>{item.quantity}</td>
                      <td>{item.reorder_level || '-'}</td>
                      <td>
                        <span className={`badge ${status.className}`}>{status.label}</span>
                      </td>
                      <td>
                        <button
                          className="btn btn-primary"
                          style={{ padding: '6px 12px', fontSize: '13px' }}
                          onClick={() => openStockModal(item)}
                        >
                          <Edit size={14} style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                          Update Stock
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Locations Tab */}
      {activeTab === 'locations' && (
        <div>
          {canWrite && (
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '16px' }}>
              <button className="btn btn-primary" onClick={() => setShowLocationModal(true)}>
                <Plus size={20} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
                Add Location
              </button>
            </div>
          )}

          {locations.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: '48px 0', color: 'var(--text-secondary)' }}>
              <MapPin size={48} style={{ marginBottom: '16px', opacity: 0.4 }} />
              <p style={{ fontSize: '16px' }}>No locations configured</p>
              <p style={{ fontSize: '14px' }}>Add a warehouse, store, or bin to start tracking inventory locations.</p>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
              {locations.map((loc) => (
                <div className="card" key={loc.id} style={{ marginBottom: 0 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                      <div style={{
                        width: '40px', height: '40px', borderRadius: '10px', display: 'flex',
                        alignItems: 'center', justifyContent: 'center',
                        background: loc.type === 'warehouse' ? '#dbeafe' : loc.type === 'store' ? '#dcfce7' : '#fef3c7',
                      }}>
                        {loc.type === 'warehouse'
                          ? <Warehouse size={20} style={{ color: '#2563eb' }} />
                          : <MapPin size={20} style={{ color: loc.type === 'store' ? '#22c55e' : '#f59e0b' }} />
                        }
                      </div>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: '16px' }}>{loc.name}</div>
                        <span className={`badge ${loc.type === 'warehouse' ? 'badge-success' : loc.type === 'store' ? 'badge-warning' : 'badge-danger'}`}>
                          {loc.type}
                        </span>
                      </div>
                    </div>
                    {canWrite && (
                      <button
                        className="btn"
                        style={{ padding: '6px', color: '#ef4444' }}
                        onClick={() => handleLocationDelete(loc.id)}
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </div>
                  {loc.address && (
                    <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '12px' }}>{loc.address}</p>
                  )}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)', fontSize: '14px' }}>
                    <Package size={14} />
                    <span><strong style={{ color: 'var(--text-primary)' }}>{loc.item_count ?? 0}</strong> items stored</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Update Stock Modal */}
      {showStockModal && selectedItem && (
        <div className="modal-overlay" onClick={() => setShowStockModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Update Stock</h3>
              <button className="btn" onClick={() => setShowStockModal(false)}>✕</button>
            </div>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '20px' }}>
              Adjusting stock for <strong>{selectedItem.product_name}</strong>
              {selectedItem.sku && <span style={{ fontFamily: 'monospace' }}> ({selectedItem.sku})</span>}
            </p>
            <form onSubmit={handleStockUpdate}>
              <div className="form-group">
                <label className="form-label">New Quantity</label>
                <input
                  type="number"
                  min="0"
                  className="form-input"
                  value={stockForm.quantity}
                  onChange={(e) => setStockForm({ quantity: e.target.value })}
                  required
                />
              </div>
              <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
                  Update Stock
                </button>
                <button type="button" className="btn btn-secondary" onClick={() => setShowStockModal(false)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Location Modal */}
      {showLocationModal && canWrite && (
        <div className="modal-overlay" onClick={() => setShowLocationModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Add Location</h3>
              <button className="btn" onClick={() => setShowLocationModal(false)}>✕</button>
            </div>
            <form onSubmit={handleLocationCreate}>
              <div className="form-group">
                <label className="form-label">Location Name</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Main Warehouse"
                  value={locationForm.name}
                  onChange={(e) => setLocationForm({ ...locationForm, name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Type</label>
                <select
                  className="form-input"
                  value={locationForm.type}
                  onChange={(e) => setLocationForm({ ...locationForm, type: e.target.value })}
                >
                  <option value="warehouse">Warehouse</option>
                  <option value="store">Store</option>
                  <option value="bin">Bin</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Address</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. 123 Industrial Ave"
                  value={locationForm.address}
                  onChange={(e) => setLocationForm({ ...locationForm, address: e.target.value })}
                />
              </div>
              <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
                  Add Location
                </button>
                <button type="button" className="btn btn-secondary" onClick={() => setShowLocationModal(false)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default Inventory;
