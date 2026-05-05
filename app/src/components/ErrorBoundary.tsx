import React from "react";

interface Props {
  children: React.ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("[ErrorBoundary]", error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      const title = this.props.fallbackTitle ?? "组件渲染出错";
      return (
        <div style={{
          padding: 24,
          margin: 16,
          borderRadius: 16,
          border: "1px solid rgba(217, 92, 74, 0.3)",
          background: "rgba(255, 252, 246, 0.92)",
          color: "#2B2118"
        }}>
          <h3 style={{ margin: "0 0 8px", color: "#D95C4A" }}>{title}</h3>
          <pre style={{
            margin: 0,
            padding: 12,
            borderRadius: 8,
            background: "rgba(120, 82, 45, 0.06)",
            fontSize: 12,
            lineHeight: 1.5,
            whiteSpace: "pre-wrap",
            wordBreak: "break-all",
            color: "#6F5C4B"
          }}>
            {this.state.error?.message ?? "Unknown error"}
            {"\n\n"}
            {this.state.error?.stack ?? ""}
          </pre>
        </div>
      );
    }
    return this.props.children;
  }
}
