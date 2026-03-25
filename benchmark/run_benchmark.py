import argparse
import json
import math
import statistics
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


SCRIPT_DIR = Path(__file__).resolve().parent
REQUIRED_TOP_LEVEL_FIELDS = [
    "city",
    "start_date",
    "end_date",
    "days",
    "weather_info",
    "overall_suggestions",
    "budget",
]


def resolve_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    cwd_candidate = Path.cwd() / path
    if cwd_candidate.exists():
        return cwd_candidate
    script_candidate = SCRIPT_DIR / path
    if script_candidate.exists():
        return script_candidate
    if path.parts and path.parts[0] == "benchmark":
        trimmed = Path(*path.parts[1:])
        trimmed_candidate = SCRIPT_DIR / trimmed
        if trimmed_candidate.exists():
            return trimmed_candidate
    return script_candidate


def load_cases(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def derive_health_url(endpoint: str) -> str:
    parsed = urlparse(endpoint)
    path = parsed.path
    if path.endswith("/plan"):
        path = path[: -len("/plan")] + "/health"
    elif not path.endswith("/health"):
        if path.endswith("/"):
            path = path[:-1]
        path = path + "/health"
    return parsed._replace(path=path, params="", query="", fragment="").geturl()


def check_backend_ready(endpoint: str, timeout: float) -> tuple[bool, str]:
    health_url = derive_health_url(endpoint)
    req = urllib.request.Request(health_url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=min(timeout, 5.0)) as resp:
            if 200 <= resp.status < 300:
                return True, health_url
            return False, f"Health check returned HTTP {resp.status}: {health_url}"
    except Exception as exc:
        return False, f"Cannot reach backend health endpoint {health_url}: {exc}"


def post_json_once(url: str, payload: dict, timeout: float) -> tuple[dict | None, str | None, float]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = time.perf_counter() - start
            data = json.loads(resp.read().decode("utf-8"))
            return data, None, elapsed
    except urllib.error.HTTPError as exc:
        elapsed = time.perf_counter() - start
        try:
            detail = exc.read().decode("utf-8", errors="ignore")
        except Exception:
            detail = ""
        message = f"HTTP {exc.code}"
        if detail:
            message = f"{message}: {detail[:300]}"
        return None, message, elapsed
    except TimeoutError:
        elapsed = time.perf_counter() - start
        return None, f"timed out after {timeout:.1f}s", elapsed
    except Exception as exc:
        elapsed = time.perf_counter() - start
        return None, str(exc), elapsed


def post_json(url: str, payload: dict, timeout: float, retries: int) -> tuple[dict | None, str | None, float, int]:
    attempts = 0
    total_elapsed = 0.0
    last_result = None
    last_error = None
    for attempt in range(retries + 1):
        attempts += 1
        result, error, elapsed = post_json_once(url, payload, timeout)
        total_elapsed += elapsed
        last_result = result
        last_error = error
        if result is not None:
            return result, None, total_elapsed, attempts
        if not error or "timed out" not in error:
            return None, error, total_elapsed, attempts
    return last_result, last_error, total_elapsed, attempts


def check_required_fields(result: dict) -> bool:
    return all(field in result and result[field] not in (None, "") for field in REQUIRED_TOP_LEVEL_FIELDS)


def check_day_count(result: dict, expected_days: int) -> bool:
    return len(result.get("days", [])) == expected_days


def check_weather(result: dict, expected_days: int) -> bool:
    weather = result.get("weather_info", [])
    if len(weather) != expected_days:
        return False
    required = {"date", "day_weather", "night_weather", "day_temp", "night_temp"}
    return all(required.issubset(item.keys()) for item in weather if isinstance(item, dict))


def check_budget(result: dict) -> bool:
    budget = result.get("budget")
    if not isinstance(budget, dict):
        return False
    fields = {
        "total_attractions",
        "total_hotels",
        "total_meals",
        "total_transportation",
        "total",
    }
    return fields.issubset(budget.keys())


def check_hotel_presence(result: dict) -> bool:
    for day in result.get("days", []):
        if day.get("hotel"):
            return True
    return False


def check_meals(result: dict, minimum: int) -> bool:
    for day in result.get("days", []):
        if len(day.get("meals", [])) < minimum:
            return False
    return True


def check_attractions(result: dict, minimum: int) -> bool:
    for day in result.get("days", []):
        if len(day.get("attractions", [])) < minimum:
            return False
    return True


def check_fallback_expected(result: dict, auto_checks: dict) -> bool:
    if "expect_fallback" not in auto_checks:
        return True
    return bool(result.get("fallback")) == bool(auto_checks["expect_fallback"])


def run_auto_checks(case: dict, result: dict) -> dict:
    checks = case["auto_checks"]
    expected_days = checks["must_have_days"]
    return {
        "required_fields_present": check_required_fields(result),
        "day_count_match": check_day_count(result, expected_days),
        "weather_complete": (not checks.get("must_have_weather")) or check_weather(result, expected_days),
        "budget_complete": (not checks.get("must_have_budget")) or check_budget(result),
        "hotel_present": (not checks.get("must_have_hotel")) or check_hotel_presence(result),
        "meals_present": (not checks.get("must_have_meals")) or check_meals(result, checks.get("min_meals_per_day", 1)),
        "attractions_present": check_attractions(result, checks.get("min_attractions_per_day", 1)),
        "fallback_expected_match": check_fallback_expected(result, checks),
    }


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    values = sorted(values)
    k = (len(values) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return values[int(k)]
    d0 = values[f] * (c - k)
    d1 = values[c] * (k - f)
    return d0 + d1


def summarize(results: list[dict]) -> dict:
    latencies = [r["latency_seconds"] for r in results]
    auto_passes = [r["auto_pass"] for r in results]
    fallback_hits = [bool(r.get("fallback")) for r in results]
    errors = [r for r in results if r.get("error")]
    return {
        "total_cases": len(results),
        "passed_auto_checks": sum(1 for x in auto_passes if x),
        "auto_pass_rate": round(sum(1 for x in auto_passes if x) / len(results), 4) if results else 0.0,
        "average_latency_seconds": round(statistics.mean(latencies), 3) if latencies else 0.0,
        "p95_latency_seconds": round(percentile(latencies, 0.95), 3) if latencies else 0.0,
        "fallback_trigger_rate": round(sum(1 for x in fallback_hits if x) / len(results), 4) if results else 0.0,
        "error_rate": round(len(errors) / len(results), 4) if results else 0.0,
    }


def build_markdown_report(summary: dict, grouped: dict) -> str:
    lines = [
        "# Benchmark Report",
        "",
        "## Summary",
        f"- Total Cases: {summary['total_cases']}",
        f"- Passed Auto Checks: {summary['passed_auto_checks']}",
        f"- Auto Pass Rate: {summary['auto_pass_rate']:.2%}",
        f"- Average End-to-End Latency: {summary['average_latency_seconds']}s",
        f"- P95 Latency: {summary['p95_latency_seconds']}s",
        f"- Fallback Trigger Rate: {summary['fallback_trigger_rate']:.2%}",
        f"- Error Rate: {summary['error_rate']:.2%}",
        "",
        "## Dataset Results",
    ]
    for name, items in grouped.items():
        dataset_summary = summarize(items)
        lines.extend(
            [
                "",
                f"### {name}",
                f"- Case Count: {dataset_summary['total_cases']}",
                f"- Auto Pass Rate: {dataset_summary['auto_pass_rate']:.2%}",
                f"- Average Latency: {dataset_summary['average_latency_seconds']}s",
                f"- P95 Latency: {dataset_summary['p95_latency_seconds']}s",
                f"- Fallback Trigger Rate: {dataset_summary['fallback_trigger_rate']:.2%}",
            ]
        )
    lines.extend(["", "## Failed Cases", ""])
    failed = [item for items in grouped.values() for item in items if not item["auto_pass"] or item.get("error")]
    if not failed:
        lines.append("- None")
    else:
        for item in failed:
            lines.append(
                f"- `{item['case_id']}` ({item['dataset']}): auto_pass={item['auto_pass']}, "
                f"error={item.get('error') or 'none'}"
            )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run benchmark cases against the trip planner backend.")
    parser.add_argument(
        "--cases",
        default="benchmark_cases.json",
        help="Path to benchmark cases JSON.",
    )
    parser.add_argument(
        "--endpoint",
        default="http://localhost:8000/api/trip/plan",
        help="Backend endpoint for trip planning.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=45.0,
        help="Request timeout in seconds.",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=1,
        help="Retry count when a request times out.",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory to store benchmark outputs.",
    )
    args = parser.parse_args()

    cases_path = resolve_path(args.cases)
    output_dir = resolve_path(args.output_dir)
    cases_doc = load_cases(cases_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    total_cases = sum(len(dataset["cases"]) for dataset in cases_doc["datasets"])
    print(f"Loaded cases from: {cases_path}", flush=True)
    print(f"Target endpoint: {args.endpoint}", flush=True)
    print(f"Total cases: {total_cases}", flush=True)
    print(f"Per-request timeout: {args.timeout}s, retries: {args.retries}", flush=True)

    ready, detail = check_backend_ready(args.endpoint, args.timeout)
    if not ready:
        print(detail, flush=True)
        print("Please start the backend first, for example: http://localhost:8000/api/trip/health", flush=True)
        return
    print(f"Backend health check passed: {detail}", flush=True)

    run_results = []
    grouped = {}
    current_index = 0

    for dataset in cases_doc["datasets"]:
        dataset_name = dataset["name"]
        grouped[dataset_name] = []
        print(f"Running dataset: {dataset_name}", flush=True)
        for case in dataset["cases"]:
            current_index += 1
            print(f"[{current_index}/{total_cases}] {case['case_id']} - {case['name']}", flush=True)
            result, error, latency, attempts = post_json(args.endpoint, case["input"], args.timeout, args.retries)
            auto_check_results = run_auto_checks(case, result or {}) if result else {}
            auto_pass = bool(result) and all(auto_check_results.values())
            entry = {
                "dataset": dataset_name,
                "case_id": case["case_id"],
                "case_name": case["name"],
                "latency_seconds": round(latency, 3),
                "attempts": attempts,
                "error": error,
                "auto_checks": auto_check_results,
                "auto_pass": auto_pass,
                "fallback": bool((result or {}).get("fallback")),
                "result_preview": {
                    "city": (result or {}).get("city"),
                    "days": len((result or {}).get("days", [])),
                    "success": (result or {}).get("success"),
                },
            }
            run_results.append(entry)
            grouped[dataset_name].append(entry)
            status = "PASS" if auto_pass else "FAIL"
            print(f"  -> {status} ({entry['latency_seconds']}s, attempts={attempts})", flush=True)
            if error:
                print(f"     error: {error}", flush=True)

    summary = summarize(run_results)
    run_payload = {
        "benchmark_version": cases_doc.get("version"),
        "cases_path": str(cases_path),
        "endpoint": args.endpoint,
        "summary": summary,
        "results": run_results,
    }

    json_path = output_dir / "benchmark_run_results.json"
    json_path.write_text(json.dumps(run_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md_report = build_markdown_report(summary, grouped)
    md_path = output_dir / "benchmark_run_report.md"
    md_path.write_text(md_report, encoding="utf-8")

    print(f"Saved JSON results to: {json_path}", flush=True)
    print(f"Saved Markdown report to: {md_path}", flush=True)


if __name__ == "__main__":
    main()
