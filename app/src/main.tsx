import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles/global.css";

// Note: React.StrictMode removed temporarily to avoid echarts-wordcloud
// double-unmount dispose errors in development. See docs/QA_REPORT.md.
ReactDOM.createRoot(document.getElementById("root")!).render(<App />);
