import React from "react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export default function StatsCard({
  title,
  value,
  icon: Icon,
  trend,
  trendLabel,
  className,
  iconClassName,
}) {
  return (
    <Card
      className={cn(
        "p-5 relative overflow-hidden group hover:shadow-md transition-shadow",
        className,
      )}
    >
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className="text-2xl font-bold tracking-tight">{value}</p>
          {trend !== undefined && (
            <p
              className={cn(
                "text-xs font-medium",
                trend >= 0 ? "text-emerald-600" : "text-destructive",
              )}
            >
              {trend >= 0 ? "↑" : "↓"} {Math.abs(trend)}% {trendLabel}
            </p>
          )}
        </div>
        {Icon && (
          <div className={cn("p-2.5 rounded-xl bg-primary/10", iconClassName)}>
            <Icon className="w-5 h-5 text-primary" />
          </div>
        )}
      </div>
    </Card>
  );
}
