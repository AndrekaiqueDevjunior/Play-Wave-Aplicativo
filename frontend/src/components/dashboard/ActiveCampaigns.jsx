import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import StatusBadge from "@/components/shared/StatusBadge";
import { Megaphone } from "lucide-react";

export default function ActiveCampaigns({ campaigns = [] }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-semibold">
          Campanhas em Execução
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {campaigns.length === 0 && (
          <p className="text-sm text-muted-foreground py-4">
            Nenhuma campanha ativa no momento.
          </p>
        )}
        {campaigns.map((campaign) => (
          <div
            key={campaign.id}
            className="flex items-center justify-between py-2 border-b border-border last:border-0"
          >
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center">
                <Megaphone className="w-4 h-4 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium">{campaign.name}</p>
                <p className="text-xs text-muted-foreground">
                  {campaign.device_count ?? campaign.device_ids?.length ?? 0} TV(s) ·{" "}
                  {campaign.total_views?.toLocaleString()} exibições
                </p>
              </div>
            </div>
            <StatusBadge status={campaign.status} />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
