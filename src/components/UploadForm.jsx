import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { usePrediction } from "../contexts/PredictionContext";
import "./UploadForm.css";

function UploadForm() {
  const { image, imagePreview, setFile } = usePrediction();
  const navigate = useNavigate();

  const onDrop = useCallback((acceptedFiles, fileRejections) => {
    if (fileRejections.length > 0) {
      const error = fileRejections[0].errors[0];
      if (error.code === "file-too-large") {
        toast.error("File is too large. Maximum size allowed is 10MB.");
      } else if (error.code === "file-invalid-type") {
        toast.error("Invalid file type. Please upload a JPEG or PNG image.");
      } else {
        toast.error(error.message);
      }
      return;
    }

    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      toast.success("Image loaded successfully!");
    }
  }, [setFile]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "image/jpeg": [],
      "image/jpg": [],
      "image/png": [],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    multiple: false,
  });

  const handleContinue = () => {
    if (!image) {
      toast.error("Please upload or drag a chest X-Ray image first.");
      return;
    }
    navigate("/patient-info");
  };

  return (
    <div className="upload-container">
      <div className="upload-card">
        <h2 className="upload-title">Upload Chest X-Ray</h2>

        <div
          {...getRootProps()}
          className={`dropzone-container ${isDragActive ? "active" : ""} ${
            image ? "has-file" : ""
          }`}
        >
          <input {...getInputProps()} />
          {imagePreview ? (
            <div className="image-preview-container">
              <img src={imagePreview} alt="X-Ray Preview" className="dropzone-preview" />
              <div className="preview-overlay">
                <p>Drag new image or click to replace</p>
              </div>
            </div>
          ) : (
            <div className="dropzone-placeholder">
              <div className="dropzone-icon">🩻</div>
              {isDragActive ? (
                <p className="dropzone-text">Drop the X-Ray here...</p>
              ) : (
                <>
                  <p className="dropzone-text">Drag & drop chest X-Ray here</p>
                  <span className="dropzone-subtext">or click to browse files</span>
                  <span className="dropzone-limits">Supported: JPEG, PNG (max 10MB)</span>
                </>
              )}
            </div>
          )}
        </div>

        <button className="analyze-button" onClick={handleContinue}>
          Continue to Patient Details →
        </button>
      </div>
    </div>
  );
}

export default UploadForm;
