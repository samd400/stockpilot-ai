import React, { useState, useEffect } from 'react';
import { Package, Plus, Search, Edit, Trash2 } from 'lucide-react';
import { productsAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

function Products() {
  const { hasPermission } = useAuth();
  const canWrite = hasPermission('inventory_write');
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [formData, setFormData] = useState({
    product_name: '',
    brand: '',
    category: '',
    purchase_price: 0,
    selling_price: 0,
    stock_quantity: 0,
    gst_percentage: 18,
  });

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await productsAPI.getAll();
      setProducts(response.data);
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingId) {
        await productsAPI.update(editingId, formData);
      } else {
        await productsAPI.create(formData);
      }
      fetchProducts();
      setShowModal(false);
      setEditingId(null);
      setFormData({
        product_name: '',
        brand: '',
        category: '',
        purchase_price: 0,
        selling_price: 0,
        stock_quantity: 0,
        gst_percentage: 18,
      });
    } catch (error) {
      console.error('Error saving product:', error);
      alert(error.response?.data?.detail || 'Failed to save product');
    }
  };

  const openEditModal = (product) => {
    setEditingId(product.id);
    setFormData({
      product_name: product.product_name || '',
      brand: product.brand || '',
      category: product.category || '',
      purchase_price: product.purchase_price || 0,
      selling_price: product.selling_price || 0,
      stock_quantity: product.stock_quantity || 0,
      gst_percentage: product.gst_percentage || 18,
    });
    setShowModal(true);
  };

  const openCreateModal = () => {
    setEditingId(null);
    setFormData({ product_name: '', brand: '', category: '', purchase_price: 0, selling_price: 0, stock_quantity: 0, gst_percentage: 18 });
    setShowModal(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this product?')) {
      try {
        await productsAPI.delete(id);
        fetchProducts();
      } catch (error) {
        console.error('Error deleting product:', error);
      }
    }
  };

  const filteredProducts = products.filter(product =>
    product.product_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    product.brand?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    product.category?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return <div className="loading">Loading products...</div>;
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Products</h1>
        <p style={{ color: '#64748b' }}>Manage your product inventory</p>
      </div>

      <div className="card">
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1 }}>
            <div style={{ position: 'relative', flex: 1, maxWidth: '400px' }}>
              <Search size={20} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
              <input
                type="text"
                placeholder="Search products..."
                className="form-input"
                style={{ paddingLeft: '40px' }}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
          {canWrite && (
            <button className="btn btn-primary" onClick={openCreateModal}>
              <Plus size={20} style={{ marginRight: '8px' }} />
              Add Product
            </button>
          )}
        </div>

        <table className="table">
          <thead>
            <tr>
              <th>Product Name</th>
              <th>Brand</th>
              <th>Category</th>
              <th>Purchase Price</th>
              <th>Selling Price</th>
              <th>Stock</th>
              <th>GST %</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredProducts.map((product) => (
              <tr key={product.id}>
                <td>{product.product_name}</td>
                <td>{product.brand || '-'}</td>
                <td>{product.category || '-'}</td>
                <td>₹{product.purchase_price?.toLocaleString() || 0}</td>
                <td>₹{product.selling_price?.toLocaleString() || 0}</td>
                <td>
                  <span className={`badge ${product.stock_quantity > 10 ? 'badge-success' : product.stock_quantity > 0 ? 'badge-warning' : 'badge-danger'}`}>
                    {product.stock_quantity}
                  </span>
                </td>
                <td>{product.gst_percentage || 18}%</td>
                <td>
                  {canWrite && (
                    <>
                      <button className="btn" style={{ padding: '6px', marginRight: '4px' }} onClick={() => openEditModal(product)}>
                        <Edit size={16} />
                      </button>
                      <button className="btn" style={{ padding: '6px', color: '#ef4444' }} onClick={() => handleDelete(product.id)}>
                        <Trash2 size={16} />
                      </button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showModal && canWrite && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">{editingId ? 'Edit Product' : 'Add New Product'}</h3>
              <button className="btn" onClick={() => setShowModal(false)}>✕</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">Product Name</label>
                <input
                  type="text"
                  name="product_name"
                  className="form-input"
                  value={formData.product_name}
                  onChange={handleChange}
                  required
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div className="form-group">
                  <label className="form-label">Brand</label>
                  <input
                    type="text"
                    name="brand"
                    className="form-input"
                    value={formData.brand}
                    onChange={handleChange}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Category</label>
                  <input
                    type="text"
                    name="category"
                    className="form-input"
                    value={formData.category}
                    onChange={handleChange}
                  />
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div className="form-group">
                  <label className="form-label">Purchase Price</label>
                  <input
                    type="number"
                    name="purchase_price"
                    className="form-input"
                    value={formData.purchase_price}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Selling Price</label>
                  <input
                    type="number"
                    name="selling_price"
                    className="form-input"
                    value={formData.selling_price}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div className="form-group">
                  <label className="form-label">Stock Quantity</label>
                  <input
                    type="number"
                    name="stock_quantity"
                    className="form-input"
                    value={formData.stock_quantity}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">GST Percentage</label>
                  <input
                    type="number"
                    name="gst_percentage"
                    className="form-input"
                    value={formData.gst_percentage}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>
              <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
                  {editingId ? 'Save Changes' : 'Add Product'}
                </button>
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
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

export default Products;
