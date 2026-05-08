import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { AlertTriangle, WifiOff, Clock } from "lucide-react";
import { cn } from "@/lib/utils";
import moment from "moment";

const severityStyles = {
  critical: "border-l-4 border-l-red-600 bg-red-50",
  error: "border-l-4 border-l-red-500 bg-red-50",
  warning: "border-l-4 border-l-amber-500 bg-amber-50",
  info: "border-l-4 border-l-blue-500 bg-blue-50",
};

const iconMap = {
  offline_detected: WifiOff,
  sync: Clock,
  media_error: AlertTriangle,
  network_error: WifiOff,
};

export default function AlertsList({ alerts = [] }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-semibold">
          Alertas Importantes
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {alerts.length === 0 && (
          <p className="text-sm text-muted-foreground py-4">
            Nenhum alerta crítico recente.
          </p>
        )}
        {alerts.map((alert) => {
          const AlertIcon = iconMap[alert.type] || AlertTriangle;
          return (
            <div
              key={alert.id}
              className={cn(
                "rounded-lg p-3 flex items-start gap-3",
                severityStyles[alert.severity] || severityStyles.info,
              )}
            >
              <AlertIcon className="w-4 h-4 mt-0.5 text-foreground/70 shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground/90">
                  {alert.message}
                </p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {alert.created_at ? moment(alert.created_at).fromNow() : ""}
                </p>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
