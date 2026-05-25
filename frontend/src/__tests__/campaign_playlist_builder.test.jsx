import { describe, expect, it } from "vitest";
import {
  itemsFromApi,
  itemsFromCampaignLegacy,
  normalizeCampaignPlaylistItems,
} from "@/components/campaigns/CampaignPlaylistBuilder";

const mediaList = [
  { id: "media-video", name: "Video institucional", type: "video" },
  { id: "media-image", name: "Banner recepcao", type: "image" },
];

describe("CampaignPlaylistBuilder helpers", () => {
  it("converte media_ids legados em itens ordenados", () => {
    const items = itemsFromCampaignLegacy(
      { media_ids: ["media-image", "media-video"] },
      mediaList,
    );

    expect(items).toHaveLength(2);
    expect(items[0]).toMatchObject({
      media_id: "media-image",
      order_index: 0,
      display_duration_seconds: null,
      starts_at: "",
      ends_at: "",
      is_active: true,
      repeat_count: 1,
      media: mediaList[1],
    });
    expect(items[1]).toMatchObject({
      media_id: "media-video",
      order_index: 10,
      media: mediaList[0],
    });
  });

  it("mapeia itens da API para o formato editavel do frontend", () => {
    const items = itemsFromApi(
      [
        {
          id: "item-1",
          media_id: "media-video",
          order_index: 30,
          display_duration_seconds: 42,
          starts_at: "2026-06-01T08:30:00Z",
          ends_at: "2026-06-30T18:45:00Z",
          is_active: false,
          repeat_count: 2,
        },
      ],
      mediaList,
    );

    expect(items[0]).toMatchObject({
      id: "item-1",
      media_id: "media-video",
      order_index: 30,
      display_duration_seconds: 42,
      starts_at: "2026-06-01T08:30",
      ends_at: "2026-06-30T18:45",
      is_active: false,
      repeat_count: 2,
      media: mediaList[0],
    });
  });

  it("normaliza payload para o contrato de itens da campanha", () => {
    const items = normalizeCampaignPlaylistItems([
      {
        id: "item-existing",
        media_id: "media-image",
        display_duration_seconds: "",
        starts_at: "",
        ends_at: "",
        is_active: false,
        repeat_count: "0",
      },
      {
        local_id: "tmp-item",
        media_id: "media-video",
        display_duration_seconds: "12",
        starts_at: "2026-06-01T08:00",
        ends_at: "2026-06-01T09:00",
        repeat_count: "3",
      },
    ]);

    expect(items[0]).toMatchObject({
      id: "item-existing",
      media_id: "media-image",
      order_index: 0,
      display_duration_seconds: null,
      starts_at: null,
      ends_at: null,
      is_active: false,
      repeat_count: 1,
    });
    expect(items[1]).toMatchObject({
      id: null,
      local_id: "tmp-item",
      media_id: "media-video",
      order_index: 10,
      display_duration_seconds: 12,
      starts_at: "2026-06-01T08:00",
      ends_at: "2026-06-01T09:00",
      is_active: true,
      repeat_count: 3,
    });
  });
});
