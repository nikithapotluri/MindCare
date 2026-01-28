import { createContext, useState } from "react";

export const AssessmentContext = createContext();

export function AssessmentProvider({ children }) {
  const [assessmentResult, setAssessmentResult] = useState(null);

  return (
    <AssessmentContext.Provider
      value={{ assessmentResult, setAssessmentResult }}
    >
      {children}
    </AssessmentContext.Provider>
  );
}
