import React from "react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { AlertTriangle, Home, RefreshCw } from "lucide-react";

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error("[ErrorBoundary] Erro capturado:", error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = "/";
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center p-6 bg-background">
          <div className="max-w-2xl w-full space-y-6">
            <Alert variant="destructive" className="border-2">
              <AlertTriangle className="h-5 w-5" />
              <AlertTitle className="text-lg font-bold">
                Erro ao carregar a página
              </AlertTitle>
              <AlertDescription className="mt-3 space-y-3">
                <p className="text-sm">
                  Ocorreu um erro inesperado ao renderizar esta página.
                </p>
                
                {this.state.error && (
                  <div className="mt-4 p-3 bg-destructive/10 rounded-md border border-destructive/20">
                    <p className="text-xs font-mono text-destructive">
                      {this.state.error.toString()}
                    </p>
                  </div>
                )}

                {process.env.NODE_ENV === "development" && this.state.errorInfo && (
                  <details className="mt-4">
                    <summary className="cursor-pointer text-xs font-semibold">
                      Stack trace (desenvolvimento)
                    </summary>
                    <pre className="mt-2 p-3 bg-muted rounded text-xs overflow-auto max-h-60">
                      {this.state.errorInfo.componentStack}
                    </pre>
                  </details>
                )}
              </AlertDescription>
            </Alert>

            <div className="flex gap-3 justify-center">
              <Button
                variant="outline"
                onClick={this.handleGoHome}
                className="gap-2"
              >
                <Home className="w-4 h-4" />
                Voltar ao início
              </Button>
              <Button
                onClick={this.handleReset}
                className="gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Recarregar página
              </Button>
            </div>

            {process.env.NODE_ENV === "development" && (
              <div className="text-center text-xs text-muted-foreground">
                <p>Verifique o console do navegador para mais detalhes.</p>
                <p className="mt-1">
                  Pressione <kbd className="px-1 bg-muted rounded">F12</kbd> para abrir DevTools.
                </p>
              </div>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
