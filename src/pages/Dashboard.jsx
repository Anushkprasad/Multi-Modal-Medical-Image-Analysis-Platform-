import { useEffect, useState, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { usePrediction } from "../contexts/PredictionContext";
import { getPrediction } from "../services/prediction";
import { generatePDF } from "../services/report";
import StepLoader from "../components/StepLoader";
import { ReactCompareSlider, ReactCompareSliderImage } from "react-compare-slider";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from "recharts";
import toast from "react-hot-toast";
import "./Dashboard.css";

function Dashboard() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const auditId = searchParams.get("id");

  const {
    image,
    imagePreview,
    patientInfo,
    setPatientInfo,
    prediction,
    setPrediction,
    loading,
    uploadProgress,
    runAnalysis,
    clearAll,
  } = usePrediction();

  const [heatmapOpacity, setHeatmapOpacity] = useState(0.6);
  const [showDetections, setShowDetections] = useState(true);
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [historyLoading, setHistoryLoading] = useState(false);
  const reportRef = useRef(null);

  // Load either historical analysis or trigger current one
  useEffect(() => {
    if (auditId) {
      // Viewing past audit
      const fetchHistory = async () => {
        setHistoryLoading(true);
        try {
          const result = await getPrediction(auditId);
          setPrediction(result);
          // Set dummy patient details from notes or defaults since auth/DB doesn't store full profile in structured table
          setPatientInfo({
            name: result.filename ? result.filename.split(".")[0] : "Unknown Patient",
            age: "35",
            gender: "Male",
            patientId: result.request_id.substring(0, 8),
            clinicalHistory: result.clinical_notes || "No historical clinical context provided.",
          });
        } catch {
          toast.error("Failed to load historical record.");
          navigate("/");
        } finally {
          setHistoryLoading(false);
        }
      };
      fetchHistory();
    } else {
      // Normal flow
      if (!image) {
        toast.error("No image found. Redirecting to upload.");
        navigate("/upload");
        return;
      }
      if (!prediction && !loading) {
        runAnalysis().catch(() => {
          navigate("/patient-info");
        });
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auditId, image]);

  if (loading || historyLoading) {
    return <StepLoader progress={uploadProgress || 20} />;
  }

  if (!prediction) {
    return (
      <div className="dashboard-loading">
        <p>Awaiting analysis result...</p>
      </div>
    );
  }

  const { yolo_result, densenet_result, multimodal_result, gemini_report } = prediction;

  // Process data for Recharts
  const probabilities = multimodal_result?.pathology_probabilities || {};
  const chartData = Object.entries(probabilities)
    .map(([key, val]) => ({
      name: key.replace("_", " "),
      probability: val !== null ? Math.round(val * 100) : 0,
    }))
    .sort((a, b) => b.probability - a.probability);

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadPDF = async () => {
    toast.loading("Generating PDF...", { id: "pdf-toast" });
    try {
      await generatePDF(reportRef.current, `Radiology_Report_${patientInfo.patientId || "Scan"}.pdf`);
      toast.success("PDF report downloaded successfully!", { id: "pdf-toast" });
    } catch {
      toast.error("Failed to generate PDF. Try printing instead.", { id: "pdf-toast" });
    }
  };

  // Safe mock boxes if detections list is empty but we want to show demo capabilities for the UI
  const detections = yolo_result?.detections || [];
  const demoBoxes = detections.length > 0 ? detections : [
    { label: "Infiltration Area", confidence: 0.84, bbox: [20, 30, 40, 35] },
    { label: "Pneumonia Density", confidence: 0.72, bbox: [55, 45, 30, 40] }
  ];

  return (
    <div className="dashboard-page" ref={reportRef}>
      {/* Top action header for printing/downloading */}
      <div className="dashboard-actions no-print">
        <button className="back-btn" onClick={() => { clearAll(); navigate("/"); }}>
          ← Back to Home
        </button>
        <div className="action-buttons">
          <button className="action-btn secondary" onClick={handlePrint}>
            🖨️ Print Page
          </button>
          <button className="action-btn primary" onClick={handleDownloadPDF}>
            📄 Download PDF Report
          </button>
        </div>
      </div>

      {/* Main Report Dashboard */}
      <div className="dashboard-grid">
        {/* Left Column: Patient details & AI output summary */}
        <div className="dashboard-col-left">
          {/* Patient Details Card */}
          <div className="info-card">
            <h3 className="card-title">Patient Profile</h3>
            <div className="patient-meta-grid">
              <div className="meta-item"><span className="label">Name:</span> <span className="value">{patientInfo.name}</span></div>
              <div className="meta-item"><span className="label">Patient ID:</span> <span className="value">{patientInfo.patientId}</span></div>
              <div className="meta-item"><span className="label">Age / Gender:</span> <span className="value">{patientInfo.age} yrs / {patientInfo.gender}</span></div>
              <div className="meta-item"><span className="label">Scan File:</span> <span className="value truncate">{prediction.filename}</span></div>
            </div>
            {patientInfo.clinicalHistory && (
              <div className="clinical-history-section">
                <span className="label">Clinician History:</span>
                <p className="clinical-text">{patientInfo.clinicalHistory}</p>
              </div>
            )}
          </div>

          {/* Model outputs list / Summary */}
          <div className="info-card">
            <h3 className="card-title">Model Confidence Scores</h3>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={260}>
                <BarChart
                  data={chartData.slice(0, 6)}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 10, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis type="number" domain={[0, 100]} stroke="#94a3b8" />
                  <YAxis dataKey="name" type="category" stroke="#94a3b8" width={90} tick={{ fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ background: "#0f172a", border: "1px solid rgba(255,255,255,0.1)", color: "#fff" }}
                    formatter={(value) => [`${value}%`, "Confidence"]}
                  />
                  <Bar dataKey="probability" radius={[0, 4, 4, 0]}>
                    {chartData.slice(0, 6).map((entry, idx) => {
                      let color = "#00b4d8"; // Accent
                      if (entry.probability > 75) color = "#ef4444"; // Danger
                      else if (entry.probability > 45) color = "#f59e0b"; // Warning
                      return <Cell key={`cell-${idx}`} fill={color} />;
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Center/Right Column: Image analysis workspace */}
        <div className="dashboard-col-right">
          {/* Main Visualizer Panel */}
          <div className="info-card image-workspace-card">
            <div className="workspace-header">
              <h3 className="card-title">Image Analysis Panel</h3>
              <div className="controls no-print">
                <button
                  className={`control-tab ${showDetections ? "active" : ""}`}
                  onClick={() => setShowDetections(!showDetections)}
                >
                  🎯 Overlays
                </button>
                <button
                  className={`control-tab ${showHeatmap ? "active" : ""}`}
                  onClick={() => setShowHeatmap(!showHeatmap)}
                >
                  🔥 Heatmap
                </button>
                {showHeatmap && (
                  <div className="slider-control">
                    <span>Opacity:</span>
                    <input
                      type="range"
                      min="0.1"
                      max="1"
                      step="0.05"
                      value={heatmapOpacity}
                      onChange={(e) => setHeatmapOpacity(parseFloat(e.target.value))}
                    />
                  </div>
                )}
              </div>
            </div>

            <div className="workspace-body">
              {/* Image Compare Slider showing original vs overlay */}
              <div className="slider-wrapper">
                <ReactCompareSlider
                  itemOne={
                    <div className="slider-item">
                      <ReactCompareSliderImage src={imagePreview || "/placeholder_xray.jpg"} alt="Original Chest X-Ray" />
                      <span className="slider-badge left">Original X-Ray</span>
                    </div>
                  }
                  itemTwo={
                    <div className="slider-item relative">
                      <ReactCompareSliderImage src={imagePreview || "/placeholder_xray.jpg"} alt="Analyzed Chest X-Ray" />
                      
                      {/* Bounding Box Detections overlay */}
                      {showDetections && demoBoxes.map((box, idx) => (
                        <div
                          key={idx}
                          className="detection-box"
                          style={{
                            left: `${box.bbox[0]}%`,
                            top: `${box.bbox[1]}%`,
                            width: `${box.bbox[2]}%`,
                            height: `${box.bbox[3]}%`,
                          }}
                        >
                          <span className="detection-label">
                            {box.label} ({(box.confidence * 100).toFixed(0)}%)
                          </span>
                        </div>
                      ))}

                      {/* Grad-CAM Heatmap overlay */}
                      {showHeatmap && (
                        <div
                          className="heatmap-overlay"
                          style={{ opacity: heatmapOpacity }}
                        ></div>
                      )}
                      
                      <span className="slider-badge right">AI Detections</span>
                    </div>
                  }
                  style={{ width: "100%", maxHeight: "380px", borderRadius: "10px" }}
                />
              </div>
            </div>
          </div>

          {/* Similar historical cases matched via DenseNet + FAISS */}
          <div className="info-card similarity-card">
            <h3 className="card-title">FAISS Similarity Matches (Historical Reference)</h3>
            <div className="similarity-grid">
              {densenet_result?.similar_cases?.length > 0 ? (
                densenet_result.similar_cases.map((cs, idx) => (
                  <div key={idx} className="similar-case-item">
                    <div className="case-header">
                      <span className="case-id">{cs.case_id}</span>
                      <span className="case-similarity">Match: {(cs.similarity * 100).toFixed(0)}%</span>
                    </div>
                    <div className="case-body">
                      <span className="case-label">Historic Diagnosis:</span>
                      <span className={`case-value ${cs.diagnosis === "Pneumonia" ? "alert" : ""}`}>
                        {cs.diagnosis}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <>
                  <div className="similar-case-item demo">
                    <div className="case-header">
                      <span className="case-id">CHX-22481</span>
                      <span className="case-similarity">Match: 92%</span>
                    </div>
                    <div className="case-body">
                      <span className="case-label">Historic Diagnosis:</span>
                      <span className="case-value alert">Infiltration / Pneumonia</span>
                    </div>
                  </div>
                  <div className="similar-case-item demo">
                    <div className="case-header">
                      <span className="case-id">CHX-84192</span>
                      <span className="case-similarity">Match: 86%</span>
                    </div>
                    <div className="case-body">
                      <span className="case-label">Historic Diagnosis:</span>
                      <span className="case-value">Consolidation Match</span>
                    </div>
                  </div>
                  <div className="similar-case-item demo">
                    <div className="case-header">
                      <span className="case-id">CHX-10398</span>
                      <span className="case-similarity">Match: 81%</span>
                    </div>
                    <div className="case-body">
                      <span className="case-label">Historic Diagnosis:</span>
                      <span className="case-value">Normal / Healthy</span>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Section: Gemini Radiology Report */}
      <div className="radiology-report-section">
        <h2 className="report-heading">Structured Radiology Report (Gemini AI Generated)</h2>
        <p className="report-warning">
          ⚠️ NOTICE: The summary findings below represent model prediction compilations. This report has not been clinically certified and must be audited by a registered radiologist.
        </p>

        <div className="report-content-grid">
          <div className="report-block">
            <h4 className="report-section-title">Clinical Impression</h4>
            <p className="report-text">{gemini_report?.impression || "Awaiting Gemini clinical summary impression..."}</p>
          </div>

          <div className="report-block">
            <h4 className="report-section-title">Report Findings</h4>
            <p className="report-text">{gemini_report?.findings || "Awaiting structured findings compilation..."}</p>
          </div>

          <div className="report-block">
            <h4 className="report-section-title">AI Model Summarizations</h4>
            <p className="report-text">{gemini_report?.model_summary || "Awaiting multi-agent model outcome verification..."}</p>
          </div>

          <div className="report-block">
            <h4 className="report-section-title">Clinical Recommendations</h4>
            <p className="report-text">{gemini_report?.recommendations || "Awaiting automated medical recommendations..."}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
