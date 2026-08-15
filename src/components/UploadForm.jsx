import "./UploadForm.css";
import { useState } from "react";
function UploadForm() {
  const [image, setImage] = useState(null);
  const [description, setDescription] = useState("");
  const handleAnalyze = () => {
    alert("Backend is not connected yet.");
  };

  return (
    <div className="upload-container">
      <div className="upload-card">
        <h2 className="upload-title">Upload Chest X-Ray</h2>

        <input
          className="file-input"
          type="file"
          accept="image/*"
          onChange={(e) => setImage(e.target.files[0])}
        />
        {image && (
          <div className="image-preview">
            <img src={URL.createObjectURL(image)} alt="X-Ray Preview" />
          </div>
        )}

        <textarea
          className="description-input"
          placeholder="Enter Description"
          onChange={(e) => setDescription(e.target.value)}
        ></textarea>

        <button className="analyze-button" onClick={handleAnalyze}>
          Analyse X-Ray
        </button>
      </div>
    </div>
  );
}

export default UploadForm;
