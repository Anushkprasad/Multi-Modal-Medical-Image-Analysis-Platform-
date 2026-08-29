import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "react-hot-toast";

// Contexts
import { AuthProvider } from "./contexts/AuthContext";
import { ThemeProvider } from "./contexts/ThemeContext";
import { PredictionProvider } from "./contexts/PredictionContext";

// Components & Layouts
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";

// Pages
import Home from "./pages/Home";
import Login from "./pages/Login";
import Upload from "./pages/Upload";
import PatientInfo from "./pages/PatientInfo";
import Dashboard from "./pages/Dashboard";
import History from "./pages/History";
import NotFound from "./pages/NotFound";

// Styles
import "./App.css";
import "./styles/theme.css";

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <PredictionProvider>
          <BrowserRouter>
            <div className="app-layout">
              <Navbar />
              <main className="app-main-content">
                <Routes>
                  {/* Public Routes */}
                  <Route path="/" element={<Home />} />
                  <Route path="/login" element={<Login />} />

                  {/* Protected Clinical Flow Routes */}
                  <Route element={<ProtectedRoute />}>
                    <Route path="/upload" element={<Upload />} />
                    <Route path="/patient-info" element={<PatientInfo />} />
                    <Route path="/analysis" element={<Dashboard />} />
                    <Route path="/history" element={<History />} />
                  </Route>

                  {/* Fallback Route */}
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </main>
            </div>
            <Toaster
              position="top-right"
              toastOptions={{
                style: {
                  background: "#0f172a",
                  color: "#fff",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                },
                success: {
                  iconTheme: {
                    primary: "#22c55e",
                    secondary: "#fff",
                  },
                },
                error: {
                  iconTheme: {
                    primary: "#ef4444",
                    secondary: "#fff",
                  },
                },
              }}
            />
          </BrowserRouter>
        </PredictionProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
