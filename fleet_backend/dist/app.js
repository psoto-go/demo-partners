const { useState, useEffect } = React;

function FleetDashboard() {
  const [shipments, setShipments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modal Form State for adding new fleet/shipment
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newId, setNewId] = useState('');
  const [newRoute, setNewRoute] = useState('');
  const [newCargo, setNewCargo] = useState('');
  const [newStatus, setNewStatus] = useState('IN TRANSIT');
  const [newReason, setNewReason] = useState('');
  const [formError, setFormError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  // Cargo Inventory Modal State
  const [isCargoModalOpen, setIsCargoModalOpen] = useState(false);
  const [selectedTruck, setSelectedTruck] = useState(null);
  const [cargoDetails, setCargoDetails] = useState([]);
  const [cargoLoading, setCargoLoading] = useState(false);
  const [cargoError, setCargoError] = useState(null);

  // Fetch initial shipments from the backend (GET /api/shipments)
  const fetchShipments = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/shipments');
      if (!response.ok) {
        throw new Error(`Error: ${response.status} ${response.statusText}`);
      }
      const data = await response.json();
      setShipments(data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch shipments:', err);
      setError(err.message || 'Connection error with the server.');
    } finally {
      setLoading(false);
    }
  };

  // Fetch data on mount
  useEffect(() => {
    fetchShipments();
  }, []);

  // Expose state setter to the global window object for external MCP tools or integrations
  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.setShipments = setShipments;
      window.refreshShipments = fetchShipments;
    }
    return () => {
      if (typeof window !== 'undefined') {
        delete window.setShipments;
        delete window.refreshShipments;
      }
    };
  }, []);

  // Resolve a customs hold (PUT /api/shipments/{id}/resolve)
  const handleResolve = async (id) => {
    try {
      const response = await fetch(`/api/shipments/${id}/resolve`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to resolve the customs hold on the server.');
      }

      const updatedShipment = await response.json();

      // Reactive local state update
      setShipments((prevShipments) =>
        prevShipments.map((shipment) => 
          shipment.id === id ? updatedShipment : shipment
        )
      );
    } catch (err) {
      console.error('Error resolving shipment:', err);
      alert(`Resolution Error: ${err.message}`);
    }
  };

  // Create a new shipment (POST /api/shipments)
  const handleAddShipment = async (e) => {
    e.preventDefault();
    setFormError(null);

    // Validation
    if (!newId.trim() || !newRoute.trim() || !newCargo.trim() || !newStatus) {
      setFormError('Please fill in all required fields.');
      return;
    }

    const isHold = newStatus === 'CUSTOMS HOLD';
    if (isHold && !newReason.trim()) {
      setFormError('Please provide a hold reason for CUSTOMS HOLD status.');
      return;
    }

    const payload = {
      id: newId.trim().toUpperCase(),
      route: newRoute.trim(),
      cargo: newCargo.trim(),
      isResolved: !isHold,
      status: newStatus,
      reason: isHold ? newReason.trim() : ""
    };

    try {
      setSubmitting(true);
      const response = await fetch('/api/shipments', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to add the new fleet shipment.');
      }

      const createdShipment = await response.json();

      // Dynamically add the new shipment to local state
      setShipments((prev) => [...prev, createdShipment]);

      // Reset form fields and close modal
      setNewId('');
      setNewRoute('');
      setNewCargo('');
      setNewStatus('IN TRANSIT');
      setNewReason('');
      setIsModalOpen(false);
    } catch (err) {
      console.error('Error adding shipment:', err);
      setFormError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  // View Cargo Inventory for a Truck
  const handleViewCargo = async (truck) => {
    setSelectedTruck(truck);
    setIsCargoModalOpen(true);
    setCargoLoading(true);
    setCargoError(null);
    setCargoDetails([]);

    try {
      const response = await fetch(`/api/shipments/${truck.id}/details`);
      if (!response.ok) {
        throw new Error(`Failed to load cargo details: ${response.status} ${response.statusText}`);
      }
      const data = await response.json();
      setCargoDetails(data);
    } catch (err) {
      console.error('Error fetching cargo:', err);
      setCargoError(err.message || 'Error loading cargo inventory.');
    } finally {
      setCargoLoading(false);
    }
  };

  // Helper to format currency
  const formatCurrency = (val) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'EUR' }).format(val);
  };

  // Helper to format date with readable labels
  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  };

  // Helper to evaluate expiry date status
  const getExpiryStatus = (dateStr) => {
    if (!dateStr) return { color: 'text-slate-400', label: 'Normal' };
    const expDate = new Date(dateStr);
    const today = new Date();
    const diffDays = Math.ceil((expDate - today) / (1000 * 60 * 60 * 24));
    
    if (diffDays <= 0) {
      return { color: 'text-red-500 font-bold bg-red-950/40 border border-red-500/30 px-2 py-0.5 rounded text-[10px]', label: 'EXPIRED' };
    } else if (diffDays <= 90) {
      return { color: 'text-amber-400 font-bold bg-amber-950/40 border border-amber-500/30 px-2 py-0.5 rounded text-[10px]', label: 'CRITICAL EXPIRY' };
    }
    return { color: 'text-emerald-400 font-medium bg-emerald-950/40 border border-emerald-500/20 px-2 py-0.5 rounded text-[10px]', label: 'STABLE' };
  };

  // Theme mode state ('dark' | 'light') with localStorage persistence
  const [theme, setTheme] = useState(() => {
    if (typeof window !== 'undefined' && window.localStorage) {
      return localStorage.getItem('fleet_theme') || 'dark';
    }
    return 'dark';
  });

  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
    if (typeof window !== 'undefined' && window.localStorage) {
      localStorage.setItem('fleet_theme', nextTheme);
    }
  };

  // Metrics calculation
  const totalShipments = shipments.length;
  const activeHolds = shipments.filter((s) => !s.isResolved).length;
  const clearedCount = shipments.filter((s) => s.isResolved).length;

  // Cargo stats
  const totalCargoValue = cargoDetails.reduce((sum, item) => sum + (item.quantity * item.unit_price_eur), 0);
  const totalCargoItems = cargoDetails.reduce((sum, item) => sum + item.quantity, 0);

  const isDark = theme === 'dark';

  return (
    <div className={`min-h-screen font-sans p-6 md:p-8 relative transition-colors duration-300 ${
      isDark ? 'bg-slate-950 text-slate-100 selection:bg-amber-500 selection:text-black' : 'bg-slate-100 text-slate-900 selection:bg-amber-500 selection:text-black'
    }`}>
      
      {/* Premium Glassmorphic Header with KPIs */}
      <header className={`max-w-7xl mx-auto mb-10 p-6 rounded-2xl backdrop-blur-md border transition-colors glass-panel ${
        isDark ? 'bg-slate-900/40 border-slate-800/80 shadow-2xl' : 'bg-white/80 border-slate-200 shadow-xl shadow-slate-200/50'
      }`}>
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <p className="text-[10px] font-bold tracking-widest text-emerald-500 uppercase">Live Operations</p>
            </div>
            <h1 className={`text-3xl font-extrabold tracking-tight ${
              isDark ? 'bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent' : 'text-slate-900'
            }`}>
              Fleet Operations Command Center
            </h1>
            <p className={`text-xs mt-1 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
              Real-time transportation monitoring, customs hold resolution, and cargo audits linked directly to BigQuery
            </p>
          </div>
          
          {/* Performance KPIs & Theme Switcher */}
          <div className="flex flex-wrap items-center gap-4">
            <button
              onClick={toggleTheme}
              title={`Switch to ${isDark ? 'Light' : 'Dark'} mode`}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl border text-xs font-bold transition-all cursor-pointer ${
                isDark
                  ? 'bg-slate-800/80 hover:bg-slate-700/80 border-slate-700 text-amber-300'
                  : 'bg-white hover:bg-slate-50 border-slate-300 text-slate-800 shadow-sm'
              }`}
            >
              {isDark ? (
                <>
                  <svg className="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                  <span>Light Mode</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                  </svg>
                  <span>Dark Mode</span>
                </>
              )}
            </button>
            <div className={`px-4 py-2 rounded-xl border ${isDark ? 'bg-slate-900 border-slate-800/50' : 'bg-slate-50 border-slate-200'}`}>
              <p className={`text-[10px] font-bold uppercase tracking-wider ${isDark ? 'text-slate-500' : 'text-slate-500'}`}>Total Fleet</p>
              <p className={`text-lg font-bold ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>{totalShipments}</p>
            </div>
            <div className={`px-4 py-2 rounded-xl border transition-colors ${
              activeHolds > 0 
                ? (isDark ? 'bg-red-950/20 border-red-500/25' : 'bg-red-50 border-red-200')
                : (isDark ? 'bg-slate-900 border-slate-800/50' : 'bg-slate-50 border-slate-200')
            }`}>
              <p className={`text-[10px] font-bold uppercase tracking-wider ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>On Hold</p>
              <p className={`text-lg font-bold ${activeHolds > 0 ? 'text-red-500' : (isDark ? 'text-slate-300' : 'text-slate-700')}`}>{activeHolds}</p>
            </div>
            <div className={`px-4 py-2 rounded-xl border ${isDark ? 'bg-emerald-950/20 border-emerald-500/25' : 'bg-emerald-50 border-emerald-200'}`}>
              <p className="text-[10px] text-emerald-500 font-bold uppercase tracking-wider">Cleared</p>
              <p className="text-lg font-bold text-emerald-500">{clearedCount}</p>
            </div>
          </div>
        </div>
      </header>

      {/* Grid Header Actions */}
      <div className="max-w-7xl mx-auto flex justify-between items-center mb-6">
        <h2 className={`text-xs font-bold tracking-wider uppercase ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
          Active Logistics Cards
        </h2>
        <button
          onClick={() => {
            setFormError(null);
            setIsModalOpen(true);
          }}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold text-xs uppercase tracking-wider bg-amber-500 hover:bg-amber-400 text-black shadow-lg shadow-amber-500/10 hover:shadow-amber-400/20 transition-all duration-300 cursor-pointer"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" />
          </svg>
          Add Shipment
        </button>
      </div>

      {/* Grid of Cards */}
      <main className="max-w-7xl mx-auto">
        {loading && shipments.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-10 h-10 border-4 border-amber-500/30 border-t-amber-500 rounded-full animate-spin mb-4" />
            <p className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>Loading BigQuery fleet data...</p>
          </div>
        ) : error && shipments.length === 0 ? (
          <div className={`p-8 rounded-2xl border text-center max-w-xl mx-auto ${isDark ? 'bg-red-950/20 border-red-500/30' : 'bg-red-50 border-red-200'}`}>
            <svg className="w-12 h-12 text-red-500 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <h3 className="text-base font-bold text-red-500 mb-1">Connection Error</h3>
            <p className={`text-xs mb-4 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>{error}</p>
            <button 
              onClick={fetchShipments}
              className="px-4 py-2 rounded-xl bg-red-500 hover:bg-red-600 text-xs font-semibold text-white transition-colors animate-pulse"
            >
              Retry Connection
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {shipments.map((truck) => (
              <div
                key={truck.id}
                className={`group relative overflow-hidden rounded-2xl border-y border-r shadow-lg hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 glass-panel ${
                  isDark
                    ? 'bg-slate-900/50 border-slate-800/80 hover:bg-slate-900/80'
                    : 'bg-white border-slate-200 hover:border-slate-300 shadow-slate-200/50'
                } ${
                  !truck.isResolved 
                    ? 'border-l-4 border-l-red-500 glow-card' 
                    : 'border-l-4 border-l-slate-400' 
                }`}
              >
                {/* Subtle backglow for active customs holds */}
                {!truck.isResolved && (
                  <div className="absolute top-0 right-0 w-24 h-24 bg-red-500/5 rounded-full blur-2xl group-hover:bg-red-500/10 transition-colors duration-300" />
                )}

                <div className="p-6">
                  {/* ID and Status Badge */}
                  <div className="flex items-center justify-between mb-4">
                    <span className={`font-mono text-xs font-bold px-2.5 py-1 rounded-md border ${
                      isDark ? 'bg-slate-800 text-slate-200 border-slate-700/50' : 'bg-slate-100 text-slate-800 border-slate-300'
                    }`}>
                      {truck.id}
                    </span>
                    <span
                      className={`text-xs font-extrabold tracking-wide uppercase flex items-center gap-1.5 ${
                        !truck.isResolved ? 'text-red-500' : (isDark ? 'text-slate-400' : 'text-slate-500')
                      }`}
                    >
                      <span className={`w-1.5 h-1.5 rounded-full ${!truck.isResolved ? 'bg-red-500 animate-pulse' : 'bg-slate-400'}`} />
                      {truck.status}
                    </span>
                  </div>

                  {/* Cargo Details */}
                  <div className="space-y-4 mb-6">
                    <div>
                      <p className={`text-[10px] font-bold uppercase tracking-wider ${isDark ? 'text-slate-500' : 'text-slate-500'}`}>Route</p>
                      <p className={`text-sm font-semibold mt-0.5 ${isDark ? 'text-slate-200' : 'text-slate-900'}`}>{truck.route}</p>
                    </div>
                    <div>
                      <p className={`text-[10px] font-bold uppercase tracking-wider ${isDark ? 'text-slate-500' : 'text-slate-500'}`}>Cargo</p>
                      <p className={`text-xs font-medium mt-0.5 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>{truck.cargo}</p>
                    </div>
                  </div>

                  {/* Hold Reason (Displayed ONLY if isResolved is false) */}
                  {!truck.isResolved && truck.reason && (
                    <div className={`mb-6 p-4 rounded-xl border ${isDark ? 'bg-red-950/20 border-red-500/20' : 'bg-red-50 border-red-200'}`}>
                      <p className="text-[10px] font-bold text-red-500 uppercase tracking-wider mb-1">Hold Reason</p>
                      <p className={`text-xs leading-relaxed font-semibold ${isDark ? 'text-red-200/90' : 'text-red-800'}`}>{truck.reason}</p>
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="flex flex-col gap-2">
                    <button
                      onClick={() => handleViewCargo(truck)}
                      className="w-full py-2 px-4 rounded-xl font-bold text-xs uppercase tracking-wider bg-slate-800 hover:bg-slate-700 hover:text-white border border-slate-700/50 text-slate-300 transition-all duration-200 flex items-center justify-center gap-2 cursor-pointer"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                      </svg>
                      View Cargo
                    </button>
                    
                    {!truck.isResolved ? (
                      <button
                        onClick={() => handleResolve(truck.id)}
                        className="w-full py-2.5 px-4 rounded-xl font-bold text-xs uppercase tracking-wider bg-red-500 hover:bg-red-400 text-white shadow-lg shadow-red-500/10 hover:shadow-red-400/20 transition-all duration-300 cursor-pointer"
                      >
                        Resolve Hold
                      </button>
                    ) : (
                      <div className="w-full py-2.5 px-4 rounded-xl bg-slate-900/50 border border-slate-800/40 text-center">
                        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Cleared for Transit</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Premium Cargo Modal for Viewing Truck Medications Cargo */}
      {isCargoModalOpen && selectedTruck && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md animate-fade-in">
          <div className="w-full max-w-4xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 relative overflow-hidden glass-panel max-h-[85vh] flex flex-col">
            
            {/* Background design elements */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-amber-500/5 rounded-full blur-3xl pointer-events-none" />
            
            {/* Modal Header */}
            <div className="flex justify-between items-start mb-6 border-b border-slate-800 pb-4 relative z-10">
              <div>
                <p className="text-[10px] font-bold tracking-widest text-amber-500 uppercase">Cargo Audit Inventory</p>
                <h3 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2 mt-0.5">
                  Shipment: <span className="text-amber-400 font-mono text-xl">{selectedTruck.id}</span>
                </h3>
                <p className="text-xs text-slate-400 mt-1">Route: <span className="text-slate-200 font-semibold">{selectedTruck.route}</span></p>
              </div>
              <button 
                onClick={() => setIsCargoModalOpen(false)}
                className="text-slate-400 hover:text-white p-2 rounded-xl hover:bg-slate-800 border border-slate-800 hover:border-slate-700 transition-all cursor-pointer"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Cargo Loading or Content */}
            <div className="flex-1 overflow-y-auto relative z-10 pr-2">
              {cargoLoading ? (
                <div className="flex flex-col items-center justify-center py-24">
                  <div className="w-10 h-10 border-4 border-amber-500/20 border-t-amber-500 rounded-full animate-spin mb-4" />
                  <p className="text-slate-400 text-sm">Querying medication ledger in BigQuery...</p>
                </div>
              ) : cargoError ? (
                <div className="p-6 rounded-xl bg-red-950/20 border border-red-500/30 text-center my-10 max-w-md mx-auto">
                  <p className="text-sm font-semibold text-red-400 mb-2">Error Loading Cargo</p>
                  <p className="text-xs text-slate-400">{cargoError}</p>
                </div>
              ) : cargoDetails.length === 0 ? (
                <div className="py-20 text-center text-slate-500 text-sm">
                  <svg className="w-12 h-12 mx-auto mb-2 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                  </svg>
                  No medications found registered on this truck.
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Cargo KPIs */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800/80">
                      <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Total Shipment Value</p>
                      <p className="text-xl font-bold text-emerald-400 mt-1">{formatCurrency(totalCargoValue)}</p>
                    </div>
                    <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800/80">
                      <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Total Package Load</p>
                      <p className="text-xl font-bold text-slate-200 mt-1">{totalCargoItems.toLocaleString('en-US')} units</p>
                    </div>
                    <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800/80">
                      <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Medication Batches</p>
                      <p className="text-xl font-bold text-slate-200 mt-1">{cargoDetails.length} distinct types</p>
                    </div>
                  </div>

                  {/* Detailed Table */}
                  <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-950/20">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="bg-slate-900 border-b border-slate-800 text-slate-400 font-semibold">
                          <th className="p-4">Product ID</th>
                          <th className="p-4">Medication Name</th>
                          <th className="p-4">Category</th>
                          <th className="p-4 text-right">Quantity</th>
                          <th className="p-4 text-right">Unit Price</th>
                          <th className="p-4 text-right">Total Value</th>
                          <th className="p-4">Expiry Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 font-medium text-slate-300">
                        {cargoDetails.map((item) => {
                          const expiry = getExpiryStatus(item.expiry_date);
                          const totalItemVal = item.quantity * item.unit_price_eur;
                          return (
                            <tr key={item.product_id} className="hover:bg-slate-900/30 transition-colors">
                              <td className="p-4 font-mono text-slate-400">{item.product_id}</td>
                              <td className="p-4 font-bold text-slate-100">{item.name}</td>
                              <td className="p-4 text-slate-400">{item.category}</td>
                              <td className="p-4 text-right font-semibold">{item.quantity.toLocaleString('en-US')}</td>
                              <td className="p-4 text-right text-slate-400">{formatCurrency(item.unit_price_eur)}</td>
                              <td className="p-4 text-right font-bold text-emerald-400">{formatCurrency(totalItemVal)}</td>
                              <td className="p-4">
                                <div className="flex flex-col gap-1">
                                  <span className={expiry.color}>{expiry.label}</span>
                                  <span className="text-[10px] text-slate-500">Exp: {formatDate(item.expiry_date)}</span>
                                </div>
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

            {/* Modal Footer */}
            <div className="mt-6 border-t border-slate-800 pt-4 flex justify-end relative z-10">
              <button 
                onClick={() => setIsCargoModalOpen(false)}
                className="px-6 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs uppercase tracking-wider transition-colors cursor-pointer"
              >
                Close Audit
              </button>
            </div>

          </div>
        </div>
      )}

      {/* Premium Modal for Adding a New Shipment */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 relative overflow-hidden glass-panel">
            
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-extrabold text-white tracking-tight">Add New Shipment</h3>
              <button 
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors cursor-pointer"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {formError && (
              <div className="mb-4 p-3.5 rounded-xl bg-red-950/30 border border-red-500/20 text-xs text-red-400 font-medium">
                {formError}
              </div>
            )}

            <form onSubmit={handleAddShipment} className="space-y-4">
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Fleet / Truck ID</label>
                <input 
                  type="text" 
                  value={newId}
                  onChange={(e) => setNewId(e.target.value)}
                  placeholder="e.g. TRK-011"
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 focus:border-amber-500 focus:ring-1 focus:ring-amber-500 text-slate-100 text-sm placeholder-slate-600 outline-none transition-all"
                  required
                />
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Route (City to City)</label>
                <input 
                  type="text" 
                  value={newRoute}
                  onChange={(e) => setNewRoute(e.target.value)}
                  placeholder="e.g. Barcelona -> Lisbon"
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 focus:border-amber-500 focus:ring-1 focus:ring-amber-500 text-slate-100 text-sm placeholder-slate-600 outline-none transition-all"
                  required
                />
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Cargo Details (Main Medications)</label>
                <input 
                  type="text" 
                  value={newCargo}
                  onChange={(e) => setNewCargo(e.target.value)}
                  placeholder="e.g. Paracetamol & Amoxicillin"
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-amber-500 focus:border-amber-500 focus:ring-1 focus:ring-amber-500 text-slate-100 text-sm placeholder-slate-600 outline-none transition-all"
                  required
                />
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Initial Status</label>
                <select 
                  value={newStatus}
                  onChange={(e) => {
                    setNewStatus(e.target.value);
                    if (e.target.value === 'IN TRANSIT') setNewReason('');
                  }}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 focus:border-amber-500 focus:ring-1 focus:ring-amber-500 text-slate-100 text-sm outline-none transition-all cursor-pointer"
                >
                  <option value="IN TRANSIT">IN TRANSIT (Standard, Active)</option>
                  <option value="CUSTOMS HOLD">CUSTOMS HOLD (On Hold)</option>
                </select>
              </div>

              {newStatus === 'CUSTOMS HOLD' && (
                <div className="animate-fade-in">
                  <label className="block text-[10px] font-bold text-red-400 uppercase tracking-wider mb-1">Customs Hold Reason</label>
                  <textarea 
                    value={newReason}
                    onChange={(e) => setNewReason(e.target.value)}
                    placeholder="Provide details of the customs blockage..."
                    rows="2"
                    className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-red-500/20 focus:border-red-500 focus:ring-1 focus:ring-red-500 text-slate-100 text-sm placeholder-slate-600 outline-none transition-all"
                    required
                  />
                </div>
              )}

              <div className="flex gap-3 pt-4">
                <button 
                  type="button" 
                  onClick={() => setIsModalOpen(false)}
                  className="w-1/2 py-2.5 px-4 rounded-xl border border-slate-800 text-slate-300 hover:bg-slate-800 font-bold text-xs uppercase tracking-wider transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  disabled={submitting}
                  className="w-1/2 py-2.5 px-4 rounded-xl bg-amber-500 hover:bg-amber-400 disabled:bg-amber-800 text-black font-bold text-xs uppercase tracking-wider transition-colors cursor-pointer"
                >
                  {submitting ? 'Adding...' : 'Add Fleet'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}


const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<FleetDashboard />);
