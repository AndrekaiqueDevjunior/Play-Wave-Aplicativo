import { describe, expect, it } from "vitest";
import { spotScheduleResolver } from "@/player-core/spotScheduleResolver";

const baseSchedule = {
  id: "schedule-1",
  spot_id: "spot-1",
  file_url: "https://example.com/spot.mp3",
  interval_seconds: 1800,
  priority: 100,
  is_active: true,
};

describe("spotScheduleResolver", () => {
  it("accepts a normal same-day time window", () => {
    const schedule = {
      ...baseSchedule,
      start_time: "08:00",
      end_time: "18:00",
    };

    expect(
      spotScheduleResolver.isActive(schedule, new Date("2026-06-06T12:00:00")),
    ).toBe(true);
    expect(
      spotScheduleResolver.isActive(schedule, new Date("2026-06-06T19:00:00")),
    ).toBe(false);
  });

  it("accepts a time window that crosses midnight", () => {
    const schedule = {
      ...baseSchedule,
      start_time: "18:49",
      end_time: "18:29",
    };

    expect(
      spotScheduleResolver.isActive(schedule, new Date("2026-06-06T19:00:00")),
    ).toBe(true);
    expect(
      spotScheduleResolver.isActive(schedule, new Date("2026-06-07T10:00:00")),
    ).toBe(true);
    expect(
      spotScheduleResolver.isActive(schedule, new Date("2026-06-07T18:35:00")),
    ).toBe(false);
  });

  it("returns eligible spots ordered by priority", () => {
    const schedules = [
      { ...baseSchedule, id: "low", priority: 1 },
      { ...baseSchedule, id: "high", priority: 10 },
    ];

    expect(
      spotScheduleResolver
        .getEligibleSpots(schedules, new Date("2026-06-06T12:00:00"))
        .map((item) => item.id),
    ).toEqual(["high", "low"]);
  });
});
