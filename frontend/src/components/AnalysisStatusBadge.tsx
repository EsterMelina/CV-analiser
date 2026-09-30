import { analysisPresentation, type AnalysisOverview } from "@/lib/analysisPresentation";

export function AnalysisStatusBadge({ value }: { value: AnalysisOverview }) {
  return <span title={value.analysis_error ?? undefined} className="inline-flex rounded-sm bg-ink/5 text-ink-soft px-2 py-0.5 text-sm">
    {analysisPresentation(value).label}
  </span>;
}
