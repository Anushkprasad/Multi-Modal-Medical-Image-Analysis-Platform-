import { useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import "./History.css";

const DEMO_HISTORY = [
  {
    request_id: "77a83d4c-6cf0-4db9-8b89-a2927f15e06e",
    patientId: "PT-84201",
    name: "John Doe",
    date: "2026-08-28T14:32:00.000Z",
    prediction: "Pneumonia",
    confidence: 87,
    filename: "chest_xray_john.jpg",
  },
  {
    request_id: "c0b48e74-ef8b-470a-93f4-96a87085b1f1",
    patientId: "PT-10398",
    name: "Alice Smith",
    date: "2026-08-27T09:15:00.000Z",
    prediction: "Infiltration",
    confidence: 64,
    filename: "xray_alice.png",
  },
  {
    request_id: "1ef783a9-1cb8-46a5-8898-7f15e06eb099",
    patientId: "PT-20419",
    name: "Robert Johnson",
    date: "2026-08-26T11:45:00.000Z",
    prediction: "No Findings (Normal)",
    confidence: 96,
    filename: "robert_normal.jpg",
  },
];

function History() {
  const navigate = useNavigate();
  const [historyList, setHistoryList] = useState(() => {
    const savedHistory = localStorage.getItem("med_history");
    if (savedHistory) {
      try {
        return JSON.parse(savedHistory);
      } catch {
        return DEMO_HISTORY;
      }
    } else {
      localStorage.setItem("med_history", JSON.stringify(DEMO_HISTORY));
      return DEMO_HISTORY;
    }
  });
  const [searchTerm, setSearchTerm] = useState("");
  const [filterDate, setFilterDate] = useState("");

  const handleDelete = (id, e) => {
    e.stopPropagation(); // Stop navigation click
    if (window.confirm("Are you sure you want to delete this scan from history?")) {
      const updated = historyList.filter((item) => item.request_id !== id);
      localStorage.setItem("med_history", JSON.stringify(updated));
      setHistoryList(updated);
      toast.success("Scan removed from history.");
    }
  };

  const handleRowClick = (id) => {
    navigate(`/analysis?id=${id}`);
  };

  // Filter logic
  const filteredHistory = historyList.filter((item) => {
    const matchesSearch =
      item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.patientId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.prediction.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesDate = filterDate
      ? new Date(item.date).toLocaleDateString().includes(new Date(filterDate).toLocaleDateString())
      : true;

    return matchesSearch && matchesDate;
  });

  return (
    <div className="history-page">
      <div className="history-card">
        <div className="history-header">
          <span className="history-badge">RECORDS LOG</span>
          <h1>Analysis History</h1>
          <p>Retrieve, review, and print past X-ray scan outcomes and generated reports.</p>
        </div>

        {/* Filter Controls */}
        <div className="filters-bar">
          <div className="search-group">
            <label className="filter-label">Search Scans</label>
            <input
              type="text"
              placeholder="Search by Patient Name, ID, or Diagnosis..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="filter-input-field"
            />
          </div>

          <div className="date-group">
            <label className="filter-label">Filter by Date</label>
            <input
              type="date"
              value={filterDate}
              onChange={(e) => setFilterDate(e.target.value)}
              className="filter-input-field"
            />
          </div>
        </div>

        {/* Records Table */}
        <div className="table-responsive">
          {filteredHistory.length > 0 ? (
            <table className="history-table">
              <thead>
                <tr>
                  <th>Patient Info</th>
                  <th>Scan Date</th>
                  <th>Primary Diagnosis</th>
                  <th>Confidence</th>
                  <th>Source File</th>
                  <th className="action-col">Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredHistory.map((item) => (
                  <tr
                    key={item.request_id}
                    onClick={() => handleRowClick(item.request_id)}
                    className="history-row"
                  >
                    <td>
                      <div className="patient-info-cell">
                        <span className="patient-name">{item.name}</span>
                        <span className="patient-id-sub">{item.patientId}</span>
                      </div>
                    </td>
                    <td>{new Date(item.date).toLocaleString()}</td>
                    <td>
                      <span className={`diagnosis-tag ${item.prediction.toLowerCase().includes("normal") ? "healthy" : "abnormal"}`}>
                        {item.prediction}
                      </span>
                    </td>
                    <td>
                      <div className="confidence-cell">
                        <div className="progress-bar-mini">
                          <div
                            className="progress-bar-mini-fill"
                            style={{
                              width: `${item.confidence}%`,
                              background: item.confidence > 75 ? "#ef4444" : item.confidence > 45 ? "#f59e0b" : "#22c55e"
                            }}
                          ></div>
                        </div>
                        <span className="confidence-text">{item.confidence}%</span>
                      </div>
                    </td>
                    <td className="filename-cell">{item.filename}</td>
                    <td className="action-col">
                      <button
                        className="delete-record-btn"
                        onClick={(e) => handleDelete(item.request_id, e)}
                      >
                        🗑️ Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="empty-history-state">
              <span className="empty-icon">📂</span>
              <h3>No matching records found</h3>
              <p>Try refining your search terms or perform a new scan on the Upload page.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default History;
