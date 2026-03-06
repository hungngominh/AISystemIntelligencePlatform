"""
AI Engine - Data Collector
Thu thập metrics từ Prometheus và logs từ Loki.
Mỗi collector nhận URL động — hỗ trợ nhiều servers.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class PrometheusCollector:
    """Query Prometheus HTTP API."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=15.0)

    async def query(self, promql: str) -> Optional[Any]:
        try:
            resp = await self._client.get(
                f"{self.base_url}/api/v1/query",
                params={"query": promql},
            )
            data = resp.json()
            if data.get("status") == "success":
                return data["data"]["result"]
        except Exception as e:
            logger.warning(f"[{self.base_url}] Prometheus query failed [{promql[:60]}]: {e}")
        return None

    async def get_targets(self) -> list[dict]:
        try:
            resp = await self._client.get(f"{self.base_url}/api/v1/targets")
            data = resp.json()
            if data.get("status") == "success":
                return [
                    {
                        "job": t.get("labels", {}).get("job", "unknown"),
                        "instance": t.get("labels", {}).get("instance", ""),
                        "health": t.get("health", "unknown"),
                        "lastError": t.get("lastError", ""),
                    }
                    for t in data["data"]["activeTargets"]
                ]
        except Exception as e:
            logger.warning(f"[{self.base_url}] Cannot get targets: {e}")
        return []

    async def get_alerts(self) -> list[dict]:
        try:
            resp = await self._client.get(f"{self.base_url}/api/v1/alerts")
            data = resp.json()
            if data.get("status") == "success":
                return data["data"]["alerts"]
        except Exception as e:
            logger.warning(f"[{self.base_url}] Cannot get alerts: {e}")
        return []

    async def check_reachable(self) -> bool:
        try:
            resp = await self._client.get(f"{self.base_url}/-/healthy", timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False


class LokiCollector:
    """Query Loki HTTP API."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=15.0)

    async def query_recent_errors(self, minutes: int = 15, limit: int = 30) -> list[str]:
        end_ns = int(datetime.now(timezone.utc).timestamp() * 1e9)
        start_ns = int((datetime.now(timezone.utc) - timedelta(minutes=minutes)).timestamp() * 1e9)
        try:
            resp = await self._client.get(
                f"{self.base_url}/loki/api/v1/query_range",
                params={
                    "query": '{job=~".+"} |= "error" or {job=~".+"} |= "ERROR" or {job=~".+"} |= "exception"',
                    "start": start_ns,
                    "end": end_ns,
                    "limit": limit,
                    "direction": "backward",
                },
            )
            data = resp.json()
            lines = []
            for stream in data.get("data", {}).get("result", []):
                for _, line in stream.get("values", []):
                    lines.append(line[:500])
            return lines
        except Exception as e:
            logger.warning(f"[{self.base_url}] Loki query failed: {e}")
        return []

    async def query_volume(self, minutes: int = 15) -> dict:
        try:
            resp = await self._client.get(
                f"{self.base_url}/loki/api/v1/query",
                params={
                    "query": f'sum(count_over_time({{job=~".+"}}[{minutes}m]))',
                    "time": int(datetime.now(timezone.utc).timestamp()),
                },
            )
            data = resp.json()
            result = data.get("data", {}).get("result", [])
            if result:
                return {"total_lines": int(result[0]["value"][1])}
        except Exception as e:
            logger.warning(f"[{self.base_url}] Loki volume query failed: {e}")
        return {"total_lines": 0}

    async def check_reachable(self) -> bool:
        try:
            resp = await self._client.get(f"{self.base_url}/ready", timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False


async def collect_all_metrics(prometheus_url: str, loki_url: str) -> dict:
    """
    Thu thập toàn bộ metrics cho một server cụ thể.
    prometheus_url, loki_url truyền vào động.
    """
    prom = PrometheusCollector(prometheus_url)
    loki = LokiCollector(loki_url)

    results = await asyncio.gather(
        prom.query("100 - (avg(rate(node_cpu_seconds_total{mode='idle'}[5m])) * 100)"),
        prom.query("(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100"),
        prom.query("(node_filesystem_size_bytes{mountpoint='/'} - node_filesystem_free_bytes{mountpoint='/'}) / node_filesystem_size_bytes{mountpoint='/'} * 100"),
        prom.query("histogram_quantile(0.95, sum(rate(api_request_duration_seconds_bucket[5m])) by (le))"),
        prom.query("sum(rate(api_requests_total[5m])) by (endpoint)"),
        prom.query("sum(rate(api_requests_total{status=~'5..'}[5m])) / sum(rate(api_requests_total[5m])) * 100"),
        prom.query("sum(queue_backlog_size) by (queue_name)"),
        prom.query("sum(increase(ai_cost_usd_total[1h])) by (model)"),
        prom.query("sum(increase(ai_tokens_total[1h])) by (model, token_type)"),
        prom.query("histogram_quantile(0.95, sum(rate(gpt_inference_seconds_bucket[5m])) by (le))"),
        prom.query("sum(pg_locks_count) by (mode)"),
        prom.get_targets(),
        prom.get_alerts(),
        loki.query_recent_errors(minutes=15, limit=30),
        loki.query_volume(minutes=15),
        prom.query("sum(rate(container_cpu_usage_seconds_total{container!=''}[5m])) by (container_label_com_docker_compose_service)"),
        prom.query("sum(container_memory_usage_bytes{container!=''}) by (container_label_com_docker_compose_service)"),
        return_exceptions=True,
    )

    def safe(val, fallback=None):
        return fallback if isinstance(val, Exception) else val

    def first_value(r) -> Optional[float]:
        if not r:
            return None
        try:
            return float(r[0]["value"][1])
        except Exception:
            return None

    def labeled_values(r) -> dict:
        if not r:
            return {}
        out = {}
        for item in r:
            label = str(item.get("metric", {}))
            try:
                out[label] = float(item["value"][1])
            except Exception:
                pass
        return out

    (
        cpu_r, mem_r, disk_r,
        p95_r, rps_r, err_r,
        queue_r, cost_r, tokens_r,
        gpt_p95_r, dblocks_r,
        targets_r, alerts_r,
        loki_errors_r, loki_vol_r,
        container_cpu_r, container_mem_r,
    ) = [safe(r) for r in results]

    return {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "prometheus_url": prometheus_url,
        "loki_url": loki_url,
        "infrastructure": {
            "cpu_usage_pct": first_value(cpu_r),
            "memory_usage_pct": first_value(mem_r),
            "disk_usage_pct": first_value(disk_r),
        },
        "api": {
            "p95_latency_seconds": first_value(p95_r),
            "requests_per_second": labeled_values(rps_r),
            "error_rate_pct": first_value(err_r),
        },
        "queue": {"backlog": labeled_values(queue_r)},
        "ai_costs": {
            "cost_last_hour_usd": labeled_values(cost_r),
            "tokens_last_hour": labeled_values(tokens_r),
            "gpt_p95_inference_seconds": first_value(gpt_p95_r),
        },
        "database": {"locks": labeled_values(dblocks_r)},
        "targets": targets_r or [],
        "active_alerts": alerts_r or [],
        "logs": {
            "recent_errors": loki_errors_r or [],
            "volume_15m": loki_vol_r or {},
        },
        "containers": {
            "cpu": labeled_values(container_cpu_r),
            "memory_bytes": labeled_values(container_mem_r),
        },
    }


async def check_server_connectivity(prometheus_url: str, loki_url: str) -> dict:
    """Kiểm tra kết nối đến Prometheus và Loki của một server."""
    prom = PrometheusCollector(prometheus_url)
    loki = LokiCollector(loki_url)
    prom_ok, loki_ok = await asyncio.gather(
        prom.check_reachable(),
        loki.check_reachable(),
        return_exceptions=True,
    )
    return {
        "prometheus": prom_ok is True,
        "loki": loki_ok is True,
    }
