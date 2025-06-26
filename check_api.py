import os
import yaml
import requests
import json
import time
from rich.console import Console
from rich.table import Table

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
OPENAPI_FILE = "openapi.yaml"

console = Console()

def wait_for_api(url, timeout=30):
    console.print(f"🕐 Очікуємо доступності API за {url}...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url)
            if r.status_code == 200:
                console.print("✅ API доступний")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    console.print("❌ Час очікування API вичерпано")
    return False

def load_openapi(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def is_protected(endpoint):
    return '401' in endpoint.get('responses', {}) or '403' in endpoint.get('responses', {})

def get_maturity_level(info: dict) -> int:
    if not info.get("auth_required"):
        return 0
    if info.get("auth_required") and not info.get("access_control"):
        return 1
    if info.get("access_control") and not info.get("iam"):
        return 2
    return 3

def get_behavior_weights(level: int) -> dict:
    matrix = {
        "0": { "auth": "В", "integrity": "С", "success": "С", "responsibility": "Н" },
        "1": { "auth": "В", "integrity": "С", "success": "С", "responsibility": "С" },
        "2": { "auth": "С", "integrity": "С", "success": "В", "responsibility": "С" },
        "3": { "auth": "Н", "integrity": "С", "success": "В", "responsibility": "В" }
    }
    row = matrix[str(level)]
    letter_to_value = {"В": 3, "С": 2, "Н": 1}
    raw = {k: letter_to_value.get(v, 1) for k, v in row.items()}
    total = sum(raw.values())
    return {k: round(v / total, 3) for k, v in raw.items()}

def calculate_behavior_api_qi(metrics: dict, weights: dict) -> float:
    return round(sum(metrics.get(k, 0) * weights.get(k, 0) for k in weights), 4)

def main():
    if not wait_for_api(f"{API_BASE_URL}/api/v1/books"):
        exit(1)

    data = load_openapi(OPENAPI_FILE)
    paths = data.get("paths", {})

    protected = protected_failed = auth_attempts = auth_success = 0
    integrity_checks = integrity_failed = 0

    table = Table(title="API Access Check (Anonymous)", show_lines=True)
    table.add_column("Method", style="cyan")
    table.add_column("Endpoint", style="magenta")
    table.add_column("Expected", style="yellow")
    table.add_column("Actual", style="green")
    table.add_column("Result", style="bold")

    for path, methods in paths.items():
        for method, details in methods.items():
            url = f"{API_BASE_URL}{path}"
            if "{book_id}" in url:
                url = url.replace("{book_id}", "1")

            expected = "401/403" if is_protected(details) else "200"
            if path == "/api/v1/books" and method.lower() == "post":
                expected = "401/403/201"

            try:
                r = requests.request(method.upper(), url)
                actual = str(r.status_code)

                if expected in ["401/403", "401/403/201"]:
                    protected += 1
                    auth_attempts += 1
                    if r.status_code in [401, 403]:
                        auth_success += 1
                        result = "✅"
                    elif expected == "401/403/201" and r.status_code == 201:
                        result = "❌"
                    else:
                        protected_failed += 1
                        result = "❌"
                else:
                    result = "✅" if r.status_code == 200 else "❌"

                if path in ["/api/v1/books", "/api/v1/books/{book_id}"] and method.lower() in ["post", "delete"]:
                    integrity_checks += 1
                    if r.status_code not in [401, 403]:
                        integrity_failed += 1

            except Exception as e:
                actual = "ERROR"
                result = f"💥 {e}"
            table.add_row(method.upper(), path, expected, actual, result)

    console.print(table)

    confidentiality = round((protected_failed / protected) * 100, 2) if protected else None
    authenticity = round((auth_success / auth_attempts) * 100, 2) if auth_attempts else None
    integrity = round((integrity_failed / integrity_checks) * 100, 2) if integrity_checks else None

    console.print(f"🔐 Confidentiality: {confidentiality}% leak")
    console.print(f"🧾 Authenticity: {authenticity}% successful auth")
    console.print(f"🛡️ Integrity: {100 - integrity if integrity is not None else 'N/A'}%")

    metrics_behavior = {
        "auth": authenticity / 100 if authenticity is not None else 0,
        "integrity": (100 - integrity) / 100 if integrity is not None else 0,
        "success": 0.85,
        "responsibility": 0.75,
        "auth_required": True,
        "access_control": False,
        "iam": False
    }

    level = get_maturity_level(metrics_behavior)
    weights_b = get_behavior_weights(level)
    api_qi_b = calculate_behavior_api_qi(metrics_behavior, weights_b)

    console.print("🧠 API-QI (behavior-based):")
    console.print(f"  Maturity level: {level}")
    console.print(f"  Weights: {weights_b}")
    console.print(f"  📊 API-QI = {api_qi_b:.4f}")

if __name__ == "__main__":
    main()
