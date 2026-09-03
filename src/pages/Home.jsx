import { Link } from "react-router-dom";
import "./Home.css";

function Home() {
  return (
    <div className="home-container">
      <div className="home-content">
        <span className="hero-badge">AI-POWERED MEDICAL ANALYSIS</span>

        <h1>Multi-Modal Medical Image Analysis Platform</h1>

        <p>
          {" "}
          Upload medical images and clinical information to assist in AI-powered
          medical analysis.
        </p>
        <Link to="/upload" className="home-upload-button">
          {" "}
          Upload Chest X-Ray
        </Link>
      </div>
      <section className="features-section">
        <h2>What Our Platform Does</h2>
        <div
          className="feature-container">

            <div className="
          feature-card"
        >
          <div className="feature-icon">🩻</div>
          <h3>Chest X-Ray Analysis</h3>
          <p>Upload chest X-rays for AI-assisted medical image analysis.</p>
        </div>

        <div className="feature-card">
          <div className="feature-icon">📝</div>
          <h3>Clinical Information</h3>
          <p>
            Add relevant clinical information to provide additional context for
            analysis.
          </p>
        </div>
         <div className="feature-card">
                        <div className="feature-icon">🤖</div>
                        <h3>AI-Assisted Analysis</h3>
                        <p>
                            Combine medical images and clinical information
                            for intelligent analysis.
                        </p>
                    </div>

                </div>
      </section>
    </div>
  );
}
export default Home;
