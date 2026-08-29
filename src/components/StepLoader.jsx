import "./StepLoader.css";

const STEPS = [
  { id: 1, text: "Preprocessing X-Ray image", threshold: 15 },
  { id: 2, text: "Running YOLO lesion detection", threshold: 40 },
  { id: 3, text: "Retrieving similar cases via DenseNet & FAISS", threshold: 70 },
  { id: 4, text: "Synthesizing multimodal fusion prediction", threshold: 85 },
  { id: 5, text: "Generating radiology report summary with Gemini", threshold: 100 },
];

function StepLoader({ progress }) {
  // Determine active step based on progress
  const activeStep = STEPS.find((step) => progress <= step.threshold) || STEPS[STEPS.length - 1];
  const currentStepId = activeStep.id;

  return (
    <div className="step-loader-container">
      <div className="step-loader-card">
        <div className="loader-icon-container">
          <div className="pulse-ring"></div>
          <span className="loader-icon">🤖</span>
        </div>

        <h2 className="loader-title">Processing Request</h2>
        <p className="loader-subtitle">AI models are analyzing the inputs. Please stand by.</p>

        {/* Progress Bar */}
        <div className="progress-track">
          <div className="progress-fill" style={{ width: `${progress}%` }}></div>
          <span className="progress-badge">{progress}%</span>
        </div>

        {/* Multi-step Status List */}
        <div className="steps-list">
          {STEPS.map((step) => {
            const isCompleted = currentStepId > step.id;
            const isActive = currentStepId === step.id;
            const isPending = currentStepId < step.id;

            let stepClass = "step-item";
            if (isCompleted) stepClass += " completed";
            if (isActive) stepClass += " active";
            if (isPending) stepClass += " pending";

            return (
              <div key={step.id} className={stepClass}>
                <div className="step-bullet">
                  {isCompleted ? "✓" : isActive ? "●" : step.id}
                </div>
                <span className="step-text">{step.text}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default StepLoader;
