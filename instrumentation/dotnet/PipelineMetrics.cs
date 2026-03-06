using System.Diagnostics;
using System.Diagnostics.Metrics;

public static class PipelineMetrics
{
    public const string ActivitySourceName = "AIProjectMiddleware.Pipeline";

    private static readonly ActivitySource ActivitySource = new(ActivitySourceName);
    private static readonly Meter Meter = new("AIProjectMiddleware.Pipeline", "1.0.0");

    public static readonly Histogram<double> OcrDuration =
        Meter.CreateHistogram<double>("ocr_processing_seconds", unit: "s");

    public static readonly Histogram<double> GptDuration =
        Meter.CreateHistogram<double>("gpt_inference_seconds", unit: "s");

    public static readonly Histogram<double> PipelineStageDuration =
        Meter.CreateHistogram<double>("pipeline_processing_seconds", unit: "s");

    public static readonly Counter<long> AiTokens =
        Meter.CreateCounter<long>("ai_tokens_total");

    public static readonly Counter<double> AiCost =
        Meter.CreateCounter<double>("ai_cost_usd_total");

    public static readonly UpDownCounter<long> QueueBacklog =
        Meter.CreateUpDownCounter<long>("queue_backlog_size");

    public static Activity? StartPipelineStage(string stageName, string documentType)
    {
        return ActivitySource.StartActivity(
            $"pipeline.{stageName}",
            ActivityKind.Internal,
            tags: new ActivityTagsCollection
            {
                ["pipeline.stage"] = stageName,
                ["document.type"] = documentType
            });
    }
}
