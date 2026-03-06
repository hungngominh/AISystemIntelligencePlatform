using OpenTelemetry;
using OpenTelemetry.Metrics;
using OpenTelemetry.Trace;
using OpenTelemetry.Resources;
using OpenTelemetry.Logs;
using Prometheus;

public static class ObservabilityExtensions
{
    public static IServiceCollection AddObservability(
        this IServiceCollection services,
        IConfiguration config,
        string serviceName)
    {
        var otlpEndpoint = config["OTEL_EXPORTER_OTLP_ENDPOINT"] ?? "http://localhost:4317";

        services.AddOpenTelemetry()
            .ConfigureResource(r => r
                .AddService(serviceName)
                .AddAttributes(new Dictionary<string, object>
                {
                    ["environment"] = config["ASPNETCORE_ENVIRONMENT"] ?? "production"
                }))
            .WithTracing(tracing => tracing
                .AddAspNetCoreInstrumentation(opts =>
                {
                    opts.RecordException = true;
                    opts.Filter = ctx => !ctx.Request.Path.StartsWithSegments("/health");
                })
                .AddEntityFrameworkCoreInstrumentation(opts =>
                {
                    opts.SetDbStatementForText = true;
                })
                .AddHttpClientInstrumentation()
                .AddSource(PipelineMetrics.ActivitySourceName)
                .AddOtlpExporter(opts => opts.Endpoint = new Uri(otlpEndpoint)))
            .WithMetrics(metrics => metrics
                .AddAspNetCoreInstrumentation()
                .AddHttpClientInstrumentation()
                .AddRuntimeInstrumentation()
                .AddPrometheusExporter()  // exposes /metrics
                .AddOtlpExporter(opts => opts.Endpoint = new Uri(otlpEndpoint)));

        return services;
    }
}
