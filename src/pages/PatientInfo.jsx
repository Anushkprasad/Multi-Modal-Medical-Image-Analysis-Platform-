import { useNavigate } from "react-router-dom";
import { usePrediction } from "../contexts/PredictionContext";
import "./PatientInfo.css";

function PatientInfo() {
  const navigate = useNavigate();
  const { patientInfo, setPatientInfo } = usePrediction();

  const handleChange = (e) => {
    setPatientInfo({
      ...patientInfo,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    navigate("/analysis");
  };

  return (
    <div className="patient-page">
      <div className="patient-card">
        <div className="patient-header">
          <span className="patient-badge">PATIENT INFORMATION</span>
          <h1>Patient Details</h1>
          <p>
            Enter the patient's basic information and clinical history before
            starting the AI-assisted analysis.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="patient-form">
          <div className="form-grid">
            <div className="form-group">
              <label>Patient Name</label>
              <input
                type="text"
                name="name"
                placeholder="Enter patient name"
                value={patientInfo.name}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label>Patient ID</label>
              <input
                type="text"
                name="patientId"
                placeholder="Enter patient ID"
                value={patientInfo.patientId}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label>Age</label>
              <input
                type="number"
                name="age"
                placeholder="Enter age"
                min="1"
                max="120"
                value={patientInfo.age}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label>Gender</label>
              <select
                name="gender"
                value={patientInfo.gender}
                onChange={handleChange}
                required
              >
                <option value="">Select gender</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Clinical History</label>
            <textarea
              name="clinicalHistory"
              placeholder="Enter symptoms, medical history, previous findings, or other relevant clinical information..."
              value={patientInfo.clinicalHistory}
              onChange={handleChange}
              rows="6"
              required
            />
          </div>

          <div className="form-actions">
            <button
              type="button"
              className="back-button"
              onClick={() => navigate("/upload")}
            >
              ← Back
            </button>

            <button type="submit" className="continue-button">
              Start AI Analysis →
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default PatientInfo;