/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useState } from "react";
import { uploadXray } from "../services/upload";
import toast from "react-hot-toast";

const PredictionContext = createContext();

export function PredictionProvider({ children }) {
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [patientInfo, setPatientInfo] = useState({
    name: "",
    age: "",
    gender: "",
    patientId: "",
    clinicalHistory: "",
  });
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const clearAll = () => {
    setImage(null);
    if (imagePreview) {
      URL.revokeObjectURL(imagePreview);
    }
    setImagePreview(null);
    setPatientInfo({
      name: "",
      age: "",
      gender: "",
      patientId: "",
      clinicalHistory: "",
    });
    setPrediction(null);
    setUploadProgress(0);
    setLoading(false);
  };

  const setFile = (file) => {
    if (imagePreview) {
      URL.revokeObjectURL(imagePreview);
    }
    if (file) {
      setImage(file);
      setImagePreview(URL.createObjectURL(file));
    } else {
      setImage(null);
      setImagePreview(null);
    }
  };

  const runAnalysis = async () => {
    if (!image) {
      toast.error("Please upload an X-ray image first.");
      return null;
    }
    setLoading(true);
    setUploadProgress(0);
    try {
      // Merge clinical notes from history or other text
      const notes = patientInfo.clinicalHistory || "";
      const result = await uploadXray(image, notes, (progressEvent) => {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        setUploadProgress(percentCompleted);
      });
      setPrediction(result);
      toast.success("Analysis completed successfully!");
      return result;
    } catch (error) {
      console.error("Analysis failed:", error);
      toast.error(error?.response?.data?.detail || "Failed to analyze image. Please check backend connection.");
      throw error;
    } finally {
      setLoading(false);
    }
  };

  return (
    <PredictionContext.Provider
      value={{
        image,
        imagePreview,
        setFile,
        patientInfo,
        setPatientInfo,
        prediction,
        setPrediction,
        loading,
        uploadProgress,
        runAnalysis,
        clearAll,
      }}
    >
      {children}
    </PredictionContext.Provider>
  );
}

export function usePrediction() {
  const context = useContext(PredictionContext);
  if (!context) {
    throw new Error("usePrediction must be used within a PredictionProvider");
  }
  return context;
}
