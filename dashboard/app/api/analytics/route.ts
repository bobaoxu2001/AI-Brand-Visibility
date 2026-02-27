import { NextRequest, NextResponse } from "next/server";

import { getDb } from "@/lib/db";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type ModelRow = {
  model_name: string;
};

type ShareOfVoiceRow = {
  brand: string;
  win_count: number;
  win_rate_pct: number;
};

type SentimentRow = {
  brand: string;
  avg_sentiment: number;
  sample_size: number;
};

type TopBrandRow = {
  brand: string;
  wins: number;
};

export async function GET(request: NextRequest) {
  try {
    const db = getDb();

    const models = db
      .prepare(
        `
        SELECT DISTINCT model_name
        FROM raw_responses
        WHERE status = 'success'
        ORDER BY model_name
        `
      )
      .all() as ModelRow[];

    const selectedModel = request.nextUrl.searchParams.get("model") || models[0]?.model_name;

    if (!selectedModel) {
      return NextResponse.json({
        models: [],
        selectedModel: null,
        totalAnalyzed: 0,
        topRecommendedBrand: "N/A",
        shareOfVoice: [],
        brandSentiment: [],
      });
    }

    const shareOfVoice = db
      .prepare(
        `
        SELECT brand, win_count, win_rate_pct
        FROM view_share_of_model
        WHERE model_name = ?
        ORDER BY win_rate_pct DESC, win_count DESC, brand ASC
        `
      )
      .all(selectedModel) as ShareOfVoiceRow[];

    const brandSentimentRaw = db
      .prepare(
        `
        SELECT brand, avg_sentiment, sample_size
        FROM view_brand_sentiment
        WHERE model_name = ?
        ORDER BY avg_sentiment DESC, sample_size DESC, brand ASC
        `
      )
      .all(selectedModel) as SentimentRow[];

    const topBrand = db
      .prepare(
        `
        SELECT pm.top_brand AS brand, COUNT(*) AS wins
        FROM parsed_metrics pm
        INNER JOIN raw_responses rr ON rr.id = pm.response_id
        WHERE rr.model_name = ?
          AND rr.status = 'success'
        GROUP BY pm.top_brand
        ORDER BY wins DESC, brand ASC
        LIMIT 1
        `
      )
      .get(selectedModel) as TopBrandRow | undefined;

    const totalAnalyzed = db
      .prepare(
        `
        SELECT COUNT(*) AS total
        FROM parsed_metrics pm
        INNER JOIN raw_responses rr ON rr.id = pm.response_id
        WHERE rr.model_name = ?
          AND rr.status = 'success'
        `
      )
      .get(selectedModel) as { total: number };

    const brandSentiment = brandSentimentRaw.map((row) => ({
      brand: row.brand,
      avgSentiment: row.avg_sentiment,
      sampleSize: row.sample_size,
      sentimentScorePct: Number((((row.avg_sentiment + 1) / 2) * 100).toFixed(2)),
    }));

    return NextResponse.json({
      models: models.map((row) => row.model_name),
      selectedModel,
      totalAnalyzed: totalAnalyzed.total,
      topRecommendedBrand: topBrand?.brand ?? "N/A",
      shareOfVoice: shareOfVoice.map((row) => ({
        brand: row.brand,
        winCount: row.win_count,
        winRatePct: row.win_rate_pct,
      })),
      brandSentiment,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unexpected server error";
    return NextResponse.json(
      { error: "Failed to query analytics data", details: message },
      { status: 500 }
    );
  }
}
