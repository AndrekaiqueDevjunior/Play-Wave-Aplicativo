import React from "react";
import { cn } from "@/lib/utils";

const statusColors = {
  active: "bg-emerald-500 hover:bg-emerald-600",
  draft: "bg-slate-400 hover:bg-slate-500",
  paused: "bg-amber-500 hover:bg-amber-600",
  ended: "bg-slate-300 hover:bg-slate-400",
};

export default function CalendarCell({
  day,
  isToday,
  isSelected,
  campaigns,
  dateStr,
  onDayClick,
  onCampaignClick,
  onDrop,
}) {
  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const campaignId = e.dataTransfer.getData("campaignId");
    if (campaignId && dateStr) {
      onDrop(campaignId, dateStr);
    }
  };

  if (!day) {
    return <div className="bg-muted/30 min-h-[90px]" />;
  }

  return (
    <div
      className={cn(
        "bg-card min-h-[90px] p-1.5 cursor-pointer transition-colors border-b border-r border-border/40",
        isSelected
          ? "ring-2 ring-primary ring-inset bg-primary/5"
          : "hover:bg-muted/40",
      )}
      onClick={() => onDayClick(dateStr)}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      <span
        className={cn(
          "text-xs font-medium inline-flex items-center justify-center w-6 h-6 rounded-full mb-0.5",
          isToday ? "bg-primary text-primary-foreground" : "text-foreground",
        )}
      >
        {day}
      </span>

      <div className="space-y-0.5">
        {campaigns.slice(0, 3).map((c) => (
          <div
            key={c.id}
            draggable
            onDragStart={(e) => {
              e.stopPropagation();
              e.dataTransfer.setData("campaignId", c.id);
            }}
            onClick={(e) => {
              e.stopPropagation();
              onCampaignClick(c);
            }}
            className={cn(
              "text-[10px] px-1.5 py-0.5 rounded text-white cursor-grab active:cursor-grabbing truncate transition-colors select-none",
              statusColors[c.status],
            )}
            title={c.name}
          >
            {c.name}
          </div>
        ))}
        {campaigns.length > 3 && (
          <span className="text-[10px] text-muted-foreground px-1">
            +{campaigns.length - 3}
          </span>
        )}
      </div>
    </div>
  );
}
