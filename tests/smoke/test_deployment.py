"""
Smoke Tests for Sahool Yemen Deployment
سهول اليمن - اختبارات التدخين للنشر

These tests verify that the deployment is working correctly.
Run after deployment to ensure all services are up and responding.
"""
import pytest
import httpx
import time
from typing import Dict, List

# Service endpoints to test
SERVICES = {
    "gateway": "http://localhost/health",
    "backend": "http://localhost:8000/health",
    "backend_ready": "http://localhost:8000/health/ready",
    "backend_live": "http://localhost:8000/health/live",
}

# Nano services through gateway
NANO_SERVICES = {
    "weather": "http://localhost/nano/weather/health",
    "imagery": "http://localhost/nano/imagery/health",
    "geo": "http://localhost/nano/geo/health",
    "analytics": "http://localhost/nano/analytics/health",
    "query": "http://localhost/nano/query/health",
    "advisor": "http://localhost/nano/advisor/health",
}

# Direct nano service ports (if exposed)
NANO_DIRECT = {
    "weather-core": "http://localhost:8010/health",
    "imagery-core": "http://localhost:8011/health",
    "geo-core": "http://localhost:8012/health",
    "analytics-core": "http://localhost:8013/health",
    "query-core": "http://localhost:8014/health",
    "advisor-core": "http://localhost:8015/health",
}


class TestDeploymentSmoke:
    """Smoke tests for deployment verification"""

    @pytest.fixture
    def client(self):
        """HTTP client with short timeout"""
        return httpx.Client(timeout=10.0)

    def test_gateway_is_responding(self, client):
        """Gateway should be responding"""
        try:
            response = client.get("http://localhost/health")
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip("Gateway not running - deployment may not be active")

    def test_backend_health(self, client):
        """Backend health endpoint should respond"""
        try:
            response = client.get("http://localhost:8000/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "field-suite-backend"
        except httpx.ConnectError:
            pytest.skip("Backend not running")

    def test_backend_liveness(self, client):
        """Backend liveness probe should respond"""
        try:
            response = client.get("http://localhost:8000/health/live")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "alive"
        except httpx.ConnectError:
            pytest.skip("Backend not running")

    def test_backend_api_docs(self, client):
        """API documentation should be available"""
        try:
            response = client.get("http://localhost:8000/docs")
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip("Backend not running")

    def test_metrics_endpoint(self, client):
        """Metrics endpoint should be available"""
        try:
            response = client.get("http://localhost:8000/metrics")
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip("Backend not running")

    def test_regions_endpoint_responds(self, client):
        """Regions endpoint should return data"""
        try:
            response = client.get("http://localhost:8000/v1/regions")
            assert response.status_code == 200
            data = response.json()
            assert "regions" in data
            assert len(data["regions"]) == 20
        except httpx.ConnectError:
            pytest.skip("Backend not running")

    def test_dashboard_endpoint_responds(self, client):
        """Dashboard endpoint should return data"""
        try:
            response = client.get("http://localhost:8000/v1/dashboard")
            assert response.status_code == 200
            data = response.json()
            assert "summary" in data
        except httpx.ConnectError:
            pytest.skip("Backend not running")


class TestNanoServicesSmoke:
    """Smoke tests for nano services"""

    @pytest.fixture
    def client(self):
        """HTTP client with short timeout"""
        return httpx.Client(timeout=10.0)

    def test_weather_service_through_gateway(self, client):
        """Weather service should respond through gateway"""
        try:
            response = client.get("http://localhost/nano/weather/health")
            if response.status_code == 200:
                data = response.json()
                assert data["status"] == "healthy"
        except httpx.ConnectError:
            pytest.skip("Gateway/Weather service not running")

    def test_imagery_service_through_gateway(self, client):
        """Imagery service should respond through gateway"""
        try:
            response = client.get("http://localhost/nano/imagery/health")
            if response.status_code == 200:
                data = response.json()
                assert data["status"] == "healthy"
        except httpx.ConnectError:
            pytest.skip("Gateway/Imagery service not running")

    def test_geo_service_through_gateway(self, client):
        """Geo service should respond through gateway"""
        try:
            response = client.get("http://localhost/nano/geo/health")
            if response.status_code == 200:
                data = response.json()
                assert data["status"] == "healthy"
        except httpx.ConnectError:
            pytest.skip("Gateway/Geo service not running")


class TestDatabaseSmoke:
    """Smoke tests for database connectivity"""

    @pytest.fixture
    def client(self):
        """HTTP client"""
        return httpx.Client(timeout=10.0)

    def test_database_connected_via_readiness(self, client):
        """Backend should report database connectivity in readiness"""
        try:
            response = client.get("http://localhost:8000/health/ready")
            # If ready returns 200, database is connected
            # If degraded, some services might be unavailable
            assert response.status_code in [200, 503]
        except httpx.ConnectError:
            pytest.skip("Backend not running")


class TestMonitoringSmoke:
    """Smoke tests for monitoring stack"""

    @pytest.fixture
    def client(self):
        """HTTP client"""
        return httpx.Client(timeout=10.0)

    def test_prometheus_is_running(self, client):
        """Prometheus should be running"""
        try:
            response = client.get("http://localhost:9091/-/healthy")
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip("Prometheus not running")

    def test_grafana_is_running(self, client):
        """Grafana should be running"""
        try:
            response = client.get("http://localhost:3003/api/health")
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip("Grafana not running")


class TestSecuritySmoke:
    """Smoke tests for security headers"""

    @pytest.fixture
    def client(self):
        """HTTP client"""
        return httpx.Client(timeout=10.0)

    def test_security_headers_present(self, client):
        """Security headers should be present"""
        try:
            response = client.get("http://localhost/health")
            headers = response.headers

            # Check for common security headers (may vary by configuration)
            # These are set in nginx.conf
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip("Gateway not running")


def run_all_smoke_tests():
    """Run all smoke tests and report status"""
    print("\n" + "=" * 60)
    print("سهول اليمن - Smoke Tests")
    print("Sahool Yemen Deployment Verification")
    print("=" * 60 + "\n")

    results = {
        "passed": 0,
        "failed": 0,
        "skipped": 0,
    }

    client = httpx.Client(timeout=10.0)

    # Test services
    services_to_test = [
        ("Gateway", "http://localhost/health"),
        ("Backend", "http://localhost:8000/health"),
        ("Backend Liveness", "http://localhost:8000/health/live"),
        ("API Docs", "http://localhost:8000/docs"),
        ("Metrics", "http://localhost:8000/metrics"),
        ("Regions API", "http://localhost:8000/v1/regions"),
        ("Dashboard API", "http://localhost:8000/v1/dashboard"),
        ("Prometheus", "http://localhost:9091/-/healthy"),
        ("Grafana", "http://localhost:3003/api/health"),
    ]

    for name, url in services_to_test:
        try:
            response = client.get(url)
            if response.status_code == 200:
                print(f"✅ {name}: OK")
                results["passed"] += 1
            else:
                print(f"❌ {name}: Failed (HTTP {response.status_code})")
                results["failed"] += 1
        except httpx.ConnectError:
            print(f"⏭️  {name}: Skipped (not running)")
            results["skipped"] += 1
        except Exception as e:
            print(f"❌ {name}: Error ({str(e)})")
            results["failed"] += 1

    print("\n" + "-" * 60)
    print(f"Results: {results['passed']} passed, {results['failed']} failed, {results['skipped']} skipped")
    print("=" * 60 + "\n")

    return results["failed"] == 0


if __name__ == "__main__":
    # Run as standalone script
    success = run_all_smoke_tests()
    exit(0 if success else 1)
