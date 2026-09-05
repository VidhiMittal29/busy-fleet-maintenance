import { useEffect, useState } from "react";
import axios from "axios";
import {
  LayoutDashboard,
  Car,
  Wrench,
  Bell,
  LogOut,
  RefreshCw,
  Plus,
  Archive,
  RotateCcw,
  Eye,
  Search,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const API = "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API,
});

function App() {
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [user, setUser] = useState(null);
  const [page, setPage] = useState("dashboard");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const [dashboard, setDashboard] = useState(null);
  const [vehicles, setVehicles] = useState([]);
  const [services, setServices] = useState([]);
  const [serviceTotal, setServiceTotal] = useState(0);
  const [alerts, setAlerts] = useState([]);
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [history, setHistory] = useState([]);

  const [search, setSearch] = useState("");
  const [serviceStatus, setServiceStatus] = useState("");
  const [vehicleFilter, setVehicleFilter] = useState("");
  const [servicePage, setServicePage] = useState(1);
  const [selectedService, setSelectedService] = useState(null);
  const [serviceTimeline, setServiceTimeline] = useState([]);

  useEffect(() => {
    if (token) {
      loadUser();
    }
  }, [token]);

  useEffect(() => {
    if (token && user) {
      loadInitialData();
    }
  }, [token, user]);

  async function loadUser() {
    try {
      const response = await api.get("/auth/me", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setUser(response.data);
    } catch {
      localStorage.removeItem("token");
      setToken(null);
    }
  }

  async function loadInitialData() {
    setError("");

    try {
      await Promise.all([
        loadVehicles(),
        loadServices(),
        ...(user.role === "MANAGER" ? [loadDashboard(), loadAlerts()] : []),
      ]);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load data");
    }
  }

  async function loadDashboard() {
    const response = await api.get("/dashboard", {
      headers: { Authorization: `Bearer ${token}` },
    });
    setDashboard(response.data);
  }

  async function loadVehicles(showArchived = false) {
    const response = await api.get("/vehicles", {
      params: {
        is_archived: showArchived,
      },
      headers: { Authorization: `Bearer ${token}` },
    });

    setVehicles(response.data.items || response.data);
  }

  async function loadServices() {
    const params = {
      page: servicePage,
      page_size: 10,
      sort_by: "updated_at",
    };

    if (search) params.search = search;
    if (serviceStatus) params.service_status = serviceStatus;
    if (vehicleFilter) params.vehicle_id = vehicleFilter;

    const response = await api.get("/services", {
      params,
      headers: { Authorization: `Bearer ${token}` },
    });

    setServices(response.data.items || []);
    setServiceTotal(response.data.total || 0);
  }

  async function loadAlerts() {
    const response = await api.get("/alerts", {
      headers: { Authorization: `Bearer ${token}` },
    });
    setAlerts(response.data.items || []);
  }

  async function viewHistory(vehicle) {
    try {
      setSelectedVehicle(vehicle);

      const response = await api.get(
        `/vehicles/${vehicle.id}/services`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      setHistory(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to load history");
    }
  }

  async function viewService(service) {
    try {
      setError("");
      setSelectedService(service);

      const response = await api.get(
        `/services/${service.id}/timeline`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      setServiceTimeline(response.data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to load service timeline"
      );
    }
  }
  async function refreshServiceTimeline() {
    if (!selectedService) return;

    try {
      const response = await api.get(
        `/services/${selectedService.id}/timeline`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setServiceTimeline(response.data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to refresh service timeline"
      );
    }
  }

  async function dismissAlert(vehicleId) {
    try {
      await api.post(
        `/alerts/${vehicleId}/dismiss`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      await loadAlerts();
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to dismiss alert");
    }
  }

  function logout() {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  }

  if (!token) {
    return <Login onLogin={(newToken) => setToken(newToken)} />;
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="logo">
          <Wrench size={22} />
          FleetOps
        </div>

        <div className="nav-section">
          {user?.role === "MANAGER" && (
            <NavButton
              active={page === "dashboard"}
              onClick={() => setPage("dashboard")}
              icon={<LayoutDashboard size={18} />}
              text="Dashboard"
            />
          )}

          {user?.role === "MANAGER" && (
            <NavButton
              active={page === "vehicles"}
              onClick={() => setPage("vehicles")}
              icon={<Car size={18} />}
              text="Vehicles"
            />
          )}

          <NavButton
            active={page === "services"}
            onClick={() => setPage("services")}
            icon={<Wrench size={18} />}
            text="Services"
          />

          {user?.role === "MANAGER" && (
            <NavButton
              active={page === "alerts"}
              onClick={() => setPage("alerts")}
              icon={<Bell size={18} />}
              text={
                <span className="nav-alert">
                  Alerts
                  {alerts.length > 0 && (
                    <span className="badge">{alerts.length}</span>
                  )}
                </span>
              }
            />
          )}
        </div>

        <div className="sidebar-bottom">
          <div className="user-card">
            <div className="avatar">
              {user?.email?.charAt(0).toUpperCase()}
            </div>

            <div>
              <strong>{user?.email}</strong>
              <small>{user?.role}</small>
            </div>
          </div>

          <button className="logout-btn" onClick={logout}>
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </aside>

      <main className="main-content">
        {error && (
          <div className="error-banner">
            {error}
            <button onClick={() => setError("")}>×</button>
          </div>
        )}

        {page === "dashboard" && user?.role === "MANAGER" && (
          <Dashboard
            dashboard={dashboard}
            refresh={async () => {
              setLoading(true);
              await loadDashboard();
              setLoading(false);
            }}
            loading={loading}
          />
        )}

        {page === "vehicles" && user?.role === "MANAGER" && (
          <Vehicles
            vehicles={vehicles}
            token={token}
            user={user}
            refresh={loadVehicles}
            onHistory={viewHistory}
          />
        )}

        {page === "services" && (
          <Services
            services={services}
            total={serviceTotal}
            page={servicePage}
            setPage={setServicePage}
            search={search}
            setSearch={setSearch}
            status={serviceStatus}
            setStatus={setServiceStatus}
            vehicleFilter={vehicleFilter}
            setVehicleFilter={setVehicleFilter}
            vehicles={vehicles}
            reload={loadServices}
            token={token}
            user={user}
            onServiceClick={viewService}
          />
        )}

        {page === "alerts" && user?.role === "MANAGER" && (
          <Alerts
            alerts={alerts}
            dismiss={dismissAlert}
            refresh={loadAlerts}
          />
        )}

        {selectedVehicle && (
          <HistoryModal
            vehicle={selectedVehicle}
            history={history}
            onClose={() => setSelectedVehicle(null)}
          />
        )}
        {selectedService && (
          <ServiceModal
            service={selectedService}
            timeline={serviceTimeline}
            token={token}
            onTimelineRefresh={refreshServiceTimeline}
            onClose={() => setSelectedService(null)}
          />
        )}
      </main>
    </div>
  );
}

function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function submit(e) {
    e.preventDefault();
    setError("");

    try {
      const response = await axios.post(`${API}/auth/login`, {
        email,
        password,
      });

      localStorage.setItem("token", response.data.access_token);
      onLogin(response.data.access_token);
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed");
    }
  }

  return (
    <div className="login-screen">
      <div className="login-box">
        <div className="login-logo">
          <Wrench size={28} />
        </div>

        <h1>FleetOps</h1>
        <p>Fleet maintenance management</p>

        <form onSubmit={submit}>
          <label>Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            required
          />

          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
          />

          <button className="primary-btn">Sign in</button>
        </form>

        {error && <div className="login-error">{error}</div>}
      </div>
    </div>
  );
}

function NavButton({ active, onClick, icon, text }) {
  return (
    <button
      className={`nav-btn ${active ? "active" : ""}`}
      onClick={onClick}
    >
      {icon}
      {text}
    </button>
  );
}

function Dashboard({ dashboard, refresh, loading }) {
  if (!dashboard) {
    return (
      <PageHeader
        title="Dashboard"
        subtitle="Fleet maintenance overview"
      />
    );
  }

  return (
    <>
      <PageHeader
        title="Dashboard"
        subtitle="Fleet maintenance overview"
        action={
          <button className="secondary-btn" onClick={refresh}>
            <RefreshCw size={16} />
            {loading ? "Refreshing..." : "Refresh"}
          </button>
        }
      />

      <div className="metric-grid">
        <Metric
          title="Vehicles Due"
          value={dashboard.headline.vehicles_due}
        />
        <Metric
          title="In Service"
          value={dashboard.headline.vehicles_in_service}
        />
        <Metric
          title="Completed This Week"
          value={dashboard.headline.services_completed_this_week}
        />
        <Metric
          title="Overdue"
          value={dashboard.headline.vehicles_overdue}
          danger
        />
      </div>

      <div className="dashboard-grid">
        <div className="panel">
          <div className="panel-header">
            <h2>Service Status</h2>
          </div>

          {Object.entries(dashboard.status_breakdown).map(
            ([status, count]) => (
              <div className="data-row" key={status}>
                <span>{status}</span>
                <strong>{count}</strong>
              </div>
            )
          )}
        </div>

        <div className="panel">
          <div className="panel-header">
            <h2>Technicians</h2>
          </div>

          {dashboard.technician_breakdown.map((tech) => (
            <div className="data-row" key={tech.technician_id}>
              <span>{tech.technician_email}</span>
              <strong>{tech.service_count}</strong>
            </div>
          ))}
        </div>
      </div>

      <div className="panel chart-panel">
        <div className="panel-header">
          <div>
            <h2>8-Week Completion</h2>
            <p>Services completed each week</p>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={dashboard.eight_week_completion}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="week_start" />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Bar dataKey="completed" name="Completed" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </>
  );
}

function Metric({ title, value, danger }) {
  return (
    <div className="metric-card">
      <span>{title}</span>
      <strong className={danger ? "danger-text" : ""}>
        {value}
      </strong>
    </div>
  );
}

function PageHeader({ title, subtitle, action }) {
  return (
    <div className="page-header">
      <div>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>

      {action}
    </div>
  );
}

function Vehicles({ vehicles, token, user, refresh, onHistory }) {
  const [showForm, setShowForm] = useState(false);
  const [editingVehicle, setEditingVehicle] = useState(null);
  const [showArchived, setShowArchived] = useState(false);

  async function archiveVehicle(vehicleId) {
    try {
      await api.post(
        `/vehicles/${vehicleId}/archive`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      await refresh(showArchived);
    } catch (err) {
      alert(
        err.response?.data?.detail ||
        "Unable to archive vehicle"
      );
    }
  }

  async function restoreVehicle(vehicleId) {
    try {
      await api.post(
        `/vehicles/${vehicleId}/unarchive`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      await refresh(showArchived);
    } catch (err) {
      alert(
        err.response?.data?.detail ||
        "Unable to restore vehicle"
      );
    }
  }

  async function exportServiceHistory() {
    try {
      const response = await api.get("/vehicles/services/export", {
        responseType: "blob",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const url = window.URL.createObjectURL(
        new Blob([response.data])
      );

      const link = document.createElement("a");
      link.href = url;
      link.download = "service_history.csv";
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(
        err.response?.data?.detail ||
        "Unable to export service history"
      );
    }
  }
  async function importOdometerCsv(e) {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await api.post(
        "/vehicles/odometer/bulk",
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "multipart/form-data",
          },
        }
      );

      await refresh(showArchived);

      const results = response.data.results || response.data;
      const items = Array.isArray(results) ? results : [];

      const successCount = items.filter(
        (item) => item.success === true || item.status === "success"
      ).length;

      const rejectedCount = items.length - successCount;

      alert(
        `CSV processed successfully.\n\nSuccessful: ${successCount}\nRejected: ${rejectedCount}`
      );
    } catch (err) {
      alert(
        err.response?.data?.detail ||
        "Unable to import odometer CSV"
      );
    }

    e.target.value = "";
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Vehicles</h1>
          <p>Manage the fleet and maintenance intervals</p>
        </div>

        <button
          className="primary-button"
          onClick={() => setShowForm(true)}
        >
          <Plus size={16} />
          Add Vehicle
        </button>
        <label className="secondary-btn" style={{ cursor: "pointer" }}>
          Import Odometer CSV
          <input
            type="file"
            accept=".csv"
            onChange={importOdometerCsv}
            style={{ display: "none" }}
          />
        </label>
        <button
          className="secondary-btn"
          onClick={exportServiceHistory}
        >
          Export Service History
        </button>
      </div>

      <div className="vehicle-tabs">
        <button
          className={!showArchived ? "vehicle-tab active" : "vehicle-tab"}
          onClick={async () => {
            setShowArchived(false);
            await refresh(false);
          }}
        >
          Active Vehicles
        </button>

        <button
          className={showArchived ? "vehicle-tab active" : "vehicle-tab"}
          onClick={async () => {
            setShowArchived(true);
            await refresh(true);
          }}
        >
          Archived Vehicles
        </button>
      </div>

      {showForm && (
        <VehicleForm
          token={token}
          onCreated={async () => {
            setShowForm(false);
            await refresh(showArchived);
          }}
        />
      )}

      {editingVehicle && (
        <EditVehicleForm
          vehicle={editingVehicle}
          token={token}
          onUpdated={async () => {
            setEditingVehicle(null);
            await refresh(showArchived);
          }}
          onCancel={() => setEditingVehicle(null)}
        />
      )}

      <div className="panel table-panel">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Registration</th>
                <th>Vehicle</th>
                <th>Odometer</th>
                <th>Date Interval</th>
                <th>Mileage Interval</th>
                <th>State</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody>
              {vehicles.map((vehicle) => (
                <tr key={vehicle.id}>
                  <td>
                    <strong>{vehicle.registration_number}</strong>
                  </td>

                  <td>
                    {vehicle.make} {vehicle.model}
                  </td>

                  <td>
                    {vehicle.current_odometer.toLocaleString()}
                  </td>

                  <td>
                    {vehicle.service_date_interval_days} days
                  </td>

                  <td>
                    {vehicle.service_mileage_interval.toLocaleString()}
                  </td>

                  <td>
                    <span
                      className={
                        vehicle.is_archived
                          ? "status-pill archived"
                          : "status-pill active"
                      }
                    >
                      {vehicle.is_archived ? "Archived" : "Active"}
                    </span>
                  </td>

                  <td>
                    <div
                      style={{
                        display: "flex",
                        gap: "6px",
                      }}
                    >
                      <button
                        className="icon-btn"
                        onClick={() => onHistory(vehicle)}
                        title="View history"
                      >
                        <Eye size={17} />
                      </button>

                      {user?.role === "MANAGER" && (
                        <>
                          <button
                            className="icon-btn"
                            onClick={() =>
                              setEditingVehicle(vehicle)
                            }
                            title="Edit vehicle"
                          >
                            Edit
                          </button>

                          {vehicle.is_archived ? (
                            <button
                              className="icon-btn"
                              onClick={() =>
                                restoreVehicle(vehicle.id)
                              }
                              title="Restore vehicle"
                            >
                              <RotateCcw size={16} />
                            </button>
                          ) : (
                            <button
                              className="icon-btn"
                              onClick={() =>
                                archiveVehicle(vehicle.id)
                              }
                              title="Archive vehicle"
                            >
                              <Archive size={16} />
                            </button>
                          )}
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {vehicles.length === 0 && (
            <div className="empty-state">
              No vehicles found.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function VehicleForm({ token, onCreated }) {
  const [form, setForm] = useState({
    registration_number: "",
    make: "",
    model: "",
    current_odometer: 0,
    service_date_interval_days: 180,
    service_mileage_interval: 10000,
  });

  const [error, setError] = useState("");

  function change(e) {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });
  }

  async function submit(e) {
    e.preventDefault();
    setError("");

    try {
      await api.post("/vehicles", {
        ...form,
        current_odometer: Number(form.current_odometer),
        service_date_interval_days: Number(
          form.service_date_interval_days
        ),
        service_mileage_interval: Number(
          form.service_mileage_interval
        ),
      }, {
        headers: { Authorization: `Bearer ${token}` },
      });

      await onCreated();
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to create vehicle");
    }
  }

  return (
    <div className="panel form-panel">
      <h2>Add Vehicle</h2>

      <form className="vehicle-form" onSubmit={submit}>
        <input
          name="registration_number"
          placeholder="Registration number"
          value={form.registration_number}
          onChange={change}
          required
        />

        <input
          name="make"
          placeholder="Make"
          value={form.make}
          onChange={change}
          required
        />

        <input
          name="model"
          placeholder="Model"
          value={form.model}
          onChange={change}
          required
        />

        <input
          name="current_odometer"
          type="number"
          placeholder="Current odometer"
          value={form.current_odometer}
          onChange={change}
        />

        <input
          name="service_date_interval_days"
          type="number"
          placeholder="Date interval"
          value={form.service_date_interval_days}
          onChange={change}
          required
        />

        <input
          name="service_mileage_interval"
          type="number"
          placeholder="Mileage interval"
          value={form.service_mileage_interval}
          onChange={change}
          required
        />

        <button className="primary-btn" type="submit">
          Create Vehicle
        </button>
      </form>

      {error && <div className="login-error">{error}</div>}
    </div>
  );
}

function Services({
  services,
  total,
  page,
  setPage,
  search,
  setSearch,
  status,
  setStatus,
  vehicleFilter,
  setVehicleFilter,
  vehicles,
  reload,
  token,
  user,
  onServiceClick,
}) {
  const [showCreateForm, setShowCreateForm] = useState(false);

  async function bookService(serviceId) {
    const scheduledDate = window.prompt(
      "Scheduled date (YYYY-MM-DD):"
    );

    if (!scheduledDate) return;

    const technicianIdsInput = window.prompt(
      "Technician IDs (comma-separated):"
    );

    if (!technicianIdsInput) return;

    const technicianIds = technicianIdsInput
      .split(",")
      .map((id) => Number(id.trim()))
      .filter((id) => !Number.isNaN(id));

    if (technicianIds.length === 0) {
      alert("Enter at least one valid technician ID.");
      return;
    }

    try {
      await api.post(
        `/services/${serviceId}/book`,
        {
          scheduled_date: scheduledDate,
          technician_ids: technicianIds,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      await reload();
    } catch (err) {
      alert(
        err.response?.data?.detail ||
        "Unable to book service"
      );
    }
  }

  async function searchServices() {
    setPage(1);
    await reload();
  }

  const totalPages = Math.max(1, Math.ceil(total / 10));

  return (
    <>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "20px",
        }}
      >
        <PageHeader
          title="Service Records"
          subtitle={`${total} matching service records`}
        />

        {user?.role === "MANAGER" && (
          <button
            className="primary-button"
            onClick={() => setShowCreateForm(true)}
          >
            + Add Service
          </button>
        )}
      </div>
      {showCreateForm && (
        <ServiceForm
          token={token}
          vehicles={vehicles}
          onCreated={async () => {
            setShowCreateForm(false);
            await reload();
          }}
          onCancel={() => setShowCreateForm(false)}
        />
      )}

      <div className="panel filters-panel">
        <div className="search-box">
          <Search size={17} />
          <input
            placeholder="Search description..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") searchServices();
            }}
          />
        </div>

        <select
          value={vehicleFilter}
          onChange={(e) => {
            setVehicleFilter(e.target.value);
            setPage(1);
            setTimeout(reload, 0);
          }}
        >
          <option value="">All vehicles</option>
          {vehicles.map((vehicle) => (
            <option key={vehicle.id} value={vehicle.id}>
              {vehicle.registration_number}
            </option>
          ))}
        </select>

        <select
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            setPage(1);
            setTimeout(reload, 0);
          }}
        >
          <option value="">All statuses</option>
          <option value="DUE">Due</option>
          <option value="BOOKED">Booked</option>
          <option value="IN_SERVICE">In Service</option>
          <option value="COMPLETED">Completed</option>
        </select>

        <button className="secondary-btn" onClick={searchServices}>
          Apply
        </button>
      </div>

      <div className="panel table-panel">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Vehicle</th>
                <th>Description</th>
                <th>Status</th>
                <th>Scheduled</th>
                <th>Updated</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody>
              {services.map((service) => (
                <tr
                  key={service.id}
                  onClick={() => onServiceClick(service)}
                  className="clickable-row"
                >
                  <td>#{service.id}</td>
                  <td>Vehicle #{service.vehicle_id}</td>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <span>{service.description}</span>

                      {(service.status !== "COMPLETED") && (
                        <button
                          className="secondary-btn"
                          onClick={async (e) => {
                            e.stopPropagation();

                            const description = window.prompt(
                              "Update service description:",
                              service.description
                            );

                            if (!description || description === service.description) return;

                            try {
                              await api.patch(
                                `/services/${service.id}`,
                                null,
                                {
                                  params: { description },
                                  headers: {
                                    Authorization: `Bearer ${token}`,
                                  },
                                }
                              );

                              await reload();
                            } catch (err) {
                              alert(
                                err.response?.data?.detail ||
                                "Unable to update description"
                              );
                            }
                          }}
                        >
                          Edit
                        </button>
                      )}
                    </div>
                  </td>
                  <td>
                    <span className={`status-pill ${service.status.toLowerCase()}`}>
                      {service.status.replace("_", " ")}
                    </span>
                  </td>
                  <td>{service.scheduled_date || "—"}</td>
                  <td>
                    {new Date(service.updated_at).toLocaleDateString()}
                  </td>
                  <td>
                    {user?.role === "MANAGER" &&
                      service.status === "DUE" && (
                        <button
                          className="primary-btn"
                          onClick={() => bookService(service.id)}
                        >
                          Book
                        </button>
                      )}

                    {service.status === "BOOKED" && (
                      <button
                        className="secondary-btn"
                        onClick={async () => {
                          try {
                            await api.patch(
                              `/services/${service.id}/status`,
                              { status: "IN_SERVICE" },
                              {
                                headers: {
                                  Authorization: `Bearer ${token}`,
                                },
                              }
                            );

                            await reload();
                          } catch (err) {
                            alert(
                              err.response?.data?.detail ||
                              "Unable to start service"
                            );
                          }
                        }}
                      >
                        Start
                      </button>
                    )}
                    {service.status === "IN_SERVICE" && (
                      <button
                        className="primary-btn"
                        onClick={async () => {
                          try {
                            await api.patch(
                              `/services/${service.id}/status`,
                              { status: "COMPLETED" },
                              {
                                headers: {
                                  Authorization: `Bearer ${token}`,
                                },
                              }
                            );

                            await reload();
                          } catch (err) {
                            alert(
                              err.response?.data?.detail ||
                              "Unable to complete service"
                            );
                          }
                        }}
                      >
                        Complete
                      </button>
                    )}
                    {user?.role === "MANAGER" && service.status !== "COMPLETED" && (
                      <button
                        className="secondary-btn"
                        onClick={async () => {
                          const technicianId = window.prompt(
                            "Technician ID:"
                          );

                          if (!technicianId) return;

                          try {
                            await api.post(
                              `/services/${service.id}/technician`,
                              {
                                technician_id: Number(technicianId),
                              },
                              {
                                headers: {
                                  Authorization: `Bearer ${token}`,
                                },
                              }
                            );

                            await reload();
                            alert("Technician assigned");
                          } catch (err) {
                            alert(
                              err.response?.data?.detail ||
                              "Unable to assign technician"
                            );
                          }
                        }}
                      >
                        Assign
                      </button>
                    )}

                    {user?.role === "MANAGER" && service.status !== "COMPLETED" && (
                      <button
                        className="secondary-btn"
                        onClick={async () => {
                          const technicianId = window.prompt(
                            "Technician ID to unassign:"
                          );

                          if (!technicianId) return;

                          try {
                            await api.delete(
                              `/services/${service.id}/technician/${Number(technicianId)}`,
                              {
                                headers: {
                                  Authorization: `Bearer ${token}`,
                                },
                              }
                            );

                            await reload();
                            alert("Technician unassigned");
                          } catch (err) {
                            alert(
                              err.response?.data?.detail ||
                              "Unable to unassign technician"
                            );
                          }
                        }}
                      >
                        Unassign
                      </button>
                    )}
                  </td>

                </tr>
              ))}
            </tbody>
          </table>

          {services.length === 0 && (
            <div className="empty-state">No service records found.</div>
          )}
        </div>

        <div className="pagination">
          <button
            disabled={page <= 1}
            onClick={() => {
              setPage(page - 1);
              setTimeout(reload, 0);
            }}
          >
            Previous
          </button>

          <span>
            Page {page} of {totalPages}
          </span>

          <button
            disabled={page >= totalPages}
            onClick={() => {
              setPage(page + 1);
              setTimeout(reload, 0);
            }}
          >
            Next
          </button>
        </div>
      </div>
    </>
  );
}

function ServiceForm({ token, vehicles, onCreated, onCancel }) {
  const [form, setForm] = useState({
    vehicle_id: "",
    description: "",
    scheduled_date: "",
  });

  const [error, setError] = useState("");

  function change(e) {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });
  }

  async function submit(e) {
    e.preventDefault();
    setError("");

    try {
      await api.post(
        "/services",
        {
          vehicle_id: Number(form.vehicle_id),
          description: form.description,
          scheduled_date: form.scheduled_date || null,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      await onCreated();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to create service record"
      );
    }
  }

  return (
    <div className="panel form-panel">
      <h2>Create Service Record</h2>

      <form className="vehicle-form" onSubmit={submit}>
        <select
          name="vehicle_id"
          value={form.vehicle_id}
          onChange={change}
          required
        >
          <option value="">Select vehicle</option>

          {vehicles
            .filter((vehicle) => !vehicle.is_archived)
            .map((vehicle) => (
              <option key={vehicle.id} value={vehicle.id}>
                {vehicle.registration_number}
              </option>
            ))}
        </select>

        <input
          name="description"
          placeholder="Service description"
          value={form.description}
          onChange={change}
          required
        />

        <input
          type="date"
          name="scheduled_date"
          value={form.scheduled_date}
          onChange={change}
        />

        {error && <div className="form-error">{error}</div>}

        <div style={{ display: "flex", gap: "8px" }}>
          <button className="primary-button" type="submit">
            Create Service
          </button>

          <button
            className="secondary-btn"
            type="button"
            onClick={onCancel}
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

function Alerts({ alerts, dismiss, refresh }) {
  return (
    <>
      <PageHeader
        title="Overdue Alerts"
        subtitle={`${alerts.length} active alerts`}
        action={
          <button className="secondary-btn" onClick={refresh}>
            <RefreshCw size={16} />
            Refresh
          </button>
        }
      />

      <div className="panel">
        {alerts.length === 0 ? (
          <div className="empty-state">
            <Bell size={32} />
            <h3>No active alerts</h3>
            <p>Your fleet is currently within its alert limits.</p>
          </div>
        ) : (
          alerts.map((alert) => (
            <div className="alert-card" key={alert.vehicle_id}>
              <div>
                <strong>{alert.registration_number}</strong>
                <p>
                  Overdue since {alert.service_due_since}
                </p>
              </div>

              <button
                className="secondary-btn"
                onClick={() => dismiss(alert.vehicle_id)}
              >
                Dismiss
              </button>
            </div>
          ))
        )}
      </div>
    </>
  );
}

function HistoryModal({ vehicle, history, onClose }) {
  return (
    <div className="modal-backdrop">
      <div className="modal">
        <div className="modal-header">
          <div>
            <h2>{vehicle.registration_number} — Service History</h2>
            <p>
              {vehicle.make} {vehicle.model}
            </p>
          </div>

          <button className="icon-btn" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="history-list">
          {history.map((service) => (
            <div className="history-item" key={service.id}>
              <div className="history-top">
                <strong>#{service.id}</strong>
                <span className={`status-pill ${service.status.toLowerCase()}`}>
                  {service.status.replace("_", " ")}
                </span>
              </div>

              <p>{service.description}</p>

              <small>
                Created{" "}
                {new Date(service.created_at).toLocaleString()}
              </small>
            </div>
          ))}

          {history.length === 0 && (
            <div className="empty-state">
              No service history available.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function EditVehicleForm({
  vehicle,
  token,
  onUpdated,
  onCancel,
}) {
  const [form, setForm] = useState({
    registration_number: vehicle.registration_number,
    make: vehicle.make,
    model: vehicle.model,
    current_odometer: vehicle.current_odometer,
    service_date_interval_days:
      vehicle.service_date_interval_days,
    service_mileage_interval:
      vehicle.service_mileage_interval,
  });

  const [error, setError] = useState("");

  function change(e) {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });
  }

  async function submit(e) {
    e.preventDefault();
    setError("");

    try {
      await api.patch(`/vehicles/${vehicle.id}`, {
        registration_number: form.registration_number,
        make: form.make,
        model: form.model,
        current_odometer: Number(form.current_odometer),
        service_date_interval_days: Number(
          form.service_date_interval_days
        ),
        service_mileage_interval: Number(
          form.service_mileage_interval
        ),
      }, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      await onUpdated();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to update vehicle"
      );
    }
  }

  return (
    <div className="panel form-panel">
      <h2>Edit Vehicle</h2>

      <form className="vehicle-form" onSubmit={submit}>
        <input
          name="registration_number"
          value={form.registration_number}
          onChange={change}
          required
        />

        <input
          name="make"
          value={form.make}
          onChange={change}
          required
        />

        <input
          name="model"
          value={form.model}
          onChange={change}
          required
        />

        <input
          name="current_odometer"
          type="number"
          value={form.current_odometer}
          onChange={change}
        />

        <input
          name="service_date_interval_days"
          type="number"
          value={form.service_date_interval_days}
          onChange={change}
          required
        />

        <input
          name="service_mileage_interval"
          type="number"
          value={form.service_mileage_interval}
          onChange={change}
          required
        />

        <div style={{ display: "flex", gap: "10px" }}>
          <button className="primary-btn" type="submit">
            Save Changes
          </button>

          <button
            className="secondary-btn"
            type="button"
            onClick={onCancel}
          >
            Cancel
          </button>
        </div>
      </form>

      {error && <div className="login-error">{error}</div>}
    </div>
  );
}

function ServiceModal({
  service,
  timeline,
  onClose,
  token,
  onTimelineRefresh,
}) {
  const [note, setNote] = useState("");
  const [savingNote, setSavingNote] = useState(false);
  const [noteError, setNoteError] = useState("");
  async function addNote() {
    if (!note.trim()) {
      setNoteError("Note cannot be empty");
      return;
    }

    setSavingNote(true);
    setNoteError("");

    try {
      await api.post(
        `/services/${service.id}/notes`,
        { note: note.trim() },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setNote("");
      await onTimelineRefresh();

    } catch (err) {
      setNoteError(
        err.response?.data?.detail ||
        "Unable to add note"
      );
    } finally {
      setSavingNote(false);
    }
  }
  return (
    <div className="modal-backdrop">
      <div className="modal">
        <div className="modal-header">
          <div>
            <h2>Service #{service.id}</h2>
            <p>Vehicle #{service.vehicle_id}</p>
          </div>

          <button className="icon-btn" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="service-detail">
          <div>
            <strong>Description</strong>
            <p>{service.description}</p>
          </div>

          <div>
            <strong>Status</strong>
            <p>
              <span
                className={`status-pill ${service.status.toLowerCase()}`}
              >
                {service.status.replace("_", " ")}
              </span>
            </p>
          </div>

          <div>
            <strong>Scheduled Date</strong>
            <p>{service.scheduled_date || "Not scheduled"}</p>
          </div>
        </div>

        <div className="note-box">
          <strong>Add Note</strong>

          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Write a service note..."
            rows={3}
          />

          <button
            className="primary-btn"
            onClick={addNote}
            disabled={savingNote}
          >
            {savingNote ? "Saving..." : "Add Note"}
          </button>

          {noteError && (
            <div className="login-error">
              {noteError}
            </div>
          )}
        </div>

        <h3>Timeline</h3>

        <div className="timeline">
          {timeline.length === 0 ? (
            <div className="empty-state">
              No timeline events.
            </div>
          ) : (
            timeline.map((event) => (
              <div className="timeline-item" key={event.id}>
                <div className="timeline-dot" />

                <div>
                  <strong>{event.event_type}</strong>

                  {event.old_status && event.new_status && (
                    <p>
                      {event.old_status} → {event.new_status}
                    </p>
                  )}

                  {event.note && <p>{event.note}</p>}

                  <small>
                    {new Date(event.created_at).toLocaleString()}
                  </small>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

export default App;