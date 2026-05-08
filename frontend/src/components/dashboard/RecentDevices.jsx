import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import StatusBadge from "@/components/shared/StatusBadge";
import { Monitor } from "lucide-react";
import moment from "moment";

export default function RecentDevices({ devices = [] }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-semibold">TVs Recentes</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {devices.length === 0 && (
          <p className="text-sm text-muted-foreground py-4">
            Nenhuma TV cadastrada ainda.
          </p>
        )}
        {devices.slice(0, 5).map((device) => (
          <div
            key={device.id}
            className="flex items-center justify-between py-2 border-b border-border last:border-0"
          >
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-muted flex items-center justify-center">
                <Monitor className="w-4 h-4 text-muted-foreground" />
              </div>
              <div>
                <p className="text-sm font-medium">{device.name}</p>
                <p className="text-xs text-muted-foreground">
                  {device.location}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-muted-foreground hidden sm:block">
                {device.last_connection || device.last_seen_at
                  ? moment(device.last_connection || device.last_seen_at).fromNow()
                  : "Sem ping"}
              </span>
              <StatusBadge status={device.status} />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
