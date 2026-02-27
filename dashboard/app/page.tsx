"use client";

import { useEffect, useMemo, useState } from "react";
import {
  BarChart,
  Card,
  DonutChart,
  Grid,
  Metric,
  Select,
  SelectItem,
  Text,
  Title,
} from "@tremor/react";

type ShareOfVoiceItem = {
  brand: string;
  winCount: number;
  winRatePct: number;
};

type BrandSentimentItem = {
  brand: string;
  avgSentiment: number;
  sampleSize: number;
  sentimentScorePct: number;
};

type AnalyticsPayload = {
  models: string[];
  selectedModel: string | null;
  totalAnalyzed: number;
  topRecommendedBrand: string;
  shareOfVoice: ShareOfVoiceItem[];
  brandSentiment: BrandSentimentItem[];
};

const formatPercent = (value: number) => `${value.toFixed(2)}%`;
const formatSigned = (value: number) => value.toFixed(2);

export default function Home() {
  const [analytics, setAnalytics] = useState<AnalyticsPayload | null>(null);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function fetchAnalytics(model?: string) {
      setIsLoading(true);
      setError(null);
      try {
        const query = model ? `?model=${encodeURIComponent(model)}` : "";
        const response = await fetch(`/api/analytics${query}`, {
          signal: controller.signal,
        });

        if (!response.ok) {
          const payload = (await response.json().catch(() => null)) as
            | { details?: string; error?: string }
            | null;
          throw new Error(payload?.details || payload?.error || "Request failed");
        }

        const payload = (await response.json()) as AnalyticsPayload;
        setAnalytics(payload);

        if (!model && payload.selectedModel) {
          setSelectedModel(payload.selectedModel);
        }
      } catch (fetchError) {
        if (controller.signal.aborted) {
          return;
        }
        setError(fetchError instanceof Error ? fetchError.message : "Failed to load analytics");
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      }
    }

    fetchAnalytics(selectedModel || undefined);

    return () => controller.abort();
  }, [selectedModel]);

  const hasData = Boolean(analytics && analytics.shareOfVoice.length > 0);

  const sentimentChartData = useMemo(
    () =>
      (analytics?.brandSentiment || []).map((row) => ({
        brand: row.brand,
        score: row.sentimentScorePct,
      })),
    [analytics]
  );

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-8 text-slate-100 md:px-12">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="flex flex-col gap-4 rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-2xl md:flex-row md:items-end md:justify-between">
          <div>
            <Text className="text-cyan-300">AI Visibility Explorer</Text>
            <Title className="mt-1 text-3xl font-semibold text-white">
              EV Brand Share of Model Tracker
            </Title>
            <Text className="mt-2 text-slate-300">
              Track how different LLMs recommend Tesla, Rivian, and Lucid.
            </Text>
          </div>
          <div className="w-full md:max-w-sm">
            <Text className="mb-2 text-sm text-slate-300">Model Selector</Text>
            <Select
              value={selectedModel}
              onValueChange={setSelectedModel}
              placeholder="Choose an LLM model"
            >
              {(analytics?.models || []).map((modelName) => (
                <SelectItem key={modelName} value={modelName}>
                  {modelName}
                </SelectItem>
              ))}
            </Select>
          </div>
        </header>

        {error ? (
          <Card className="border border-rose-400/40 bg-rose-950/60">
            <Title className="text-rose-200">Data Load Error</Title>
            <Text className="mt-2 text-rose-100">{error}</Text>
          </Card>
        ) : null}

        <Grid numItems={1} numItemsMd={2} className="gap-6">
          <Card className="border border-slate-800 bg-slate-900/70">
            <Text className="text-slate-300">Total Analyzed</Text>
            <Metric className="mt-2 text-cyan-300">
              {isLoading ? "…" : analytics?.totalAnalyzed ?? 0}
            </Metric>
          </Card>
          <Card className="border border-slate-800 bg-slate-900/70">
            <Text className="text-slate-300">Top Recommended Brand</Text>
            <Metric className="mt-2 text-emerald-300">
              {isLoading ? "…" : analytics?.topRecommendedBrand ?? "N/A"}
            </Metric>
          </Card>
        </Grid>

        <Grid numItems={1} numItemsMd={2} className="gap-6">
          <Card className="border border-slate-800 bg-slate-900/70">
            <Title className="text-white">Share of Voice %</Title>
            <Text className="text-slate-300">
              Brand win-rate for the selected model.
            </Text>
            <BarChart
              className="mt-6 h-80"
              data={analytics?.shareOfVoice || []}
              index="brand"
              categories={["winRatePct"]}
              colors={["cyan"]}
              valueFormatter={formatPercent}
              yAxisWidth={56}
              showLegend={false}
            />
          </Card>

          <Card className="border border-slate-800 bg-slate-900/70">
            <Title className="text-white">Brand Sentiment</Title>
            <Text className="text-slate-300">
              Donut shows positivity index (normalized from average sentiment).
            </Text>
            <DonutChart
              className="mt-6 h-80"
              data={sentimentChartData}
              index="brand"
              category="score"
              valueFormatter={formatPercent}
              colors={["emerald", "cyan", "violet", "amber", "rose"]}
            />
            <div className="mt-4 space-y-2">
              {(analytics?.brandSentiment || []).map((row) => (
                <div
                  key={`${row.brand}-${row.sampleSize}`}
                  className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/70 px-3 py-2"
                >
                  <Text className="text-slate-200">{row.brand}</Text>
                  <Text className="text-slate-400">
                    avg sentiment {formatSigned(row.avgSentiment)} · n={row.sampleSize}
                  </Text>
                </div>
              ))}
            </div>
          </Card>
        </Grid>

        {!isLoading && !hasData ? (
          <Card className="border border-amber-400/40 bg-amber-950/60">
            <Title className="text-amber-100">No analytics data yet</Title>
            <Text className="mt-2 text-amber-200">
              Run the response fetch + evaluation scripts, then recreate SQL views.
            </Text>
          </Card>
        ) : null}
      </div>
    </main>
  );
}
