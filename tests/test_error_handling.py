"""
Tests for Error Handling System
اختبارات شاملة لنظام معالجة الأخطاء
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

import sys
sys.path.append('/home/user/sahool-project')

from shared.error_handling import (
    SahoolException,
    ValidationException,
    NotFoundException,
    DatabaseException,
    ErrorCode,
    ErrorSeverity
)

from shared.validation import (
    GeometryValidator,
    FieldValidators,
    NumericValidators,
    PaginationValidator
)

from shared.resilience import (
    retry_async,
    RetryConfig,
    RetryStrategy,
    CircuitBreaker,
    CircuitState
)

# ===================================================================
# ERROR HANDLING TESTS
# ===================================================================

class TestErrorHandling:
    """Test error handling framework"""

    def test_validation_exception(self):
        """Test ValidationException"""

        exc = ValidationException(
            message_ar="خطأ في التحقق",
            message_en="Validation error"
        )

        assert exc.error_code == ErrorCode.VALIDATION_ERROR
        assert exc.severity == ErrorSeverity.LOW
        assert exc.status_code == 400

    def test_not_found_exception(self):
        """Test NotFoundException"""

        exc = NotFoundException("Field", "field-123")

        assert exc.error_code == ErrorCode.NOT_FOUND
        assert "field-123" in exc.message_ar
        assert exc.status_code == 404
        assert exc.context["resource_id"] == "field-123"

    def test_database_exception(self):
        """Test DatabaseException"""

        original_error = ValueError("Connection failed")
        exc = DatabaseException("create_field", original_error)

        assert exc.error_code == ErrorCode.DATABASE_ERROR
        assert exc.severity == ErrorSeverity.CRITICAL
        assert exc.status_code == 500
        assert "create_field" in exc.context["operation"]


# ===================================================================
# VALIDATION TESTS
# ===================================================================

class TestValidation:
    """Test input validation"""

    def test_valid_geometry(self):
        """Test valid geometry passes"""

        valid_geojson = {
            "type": "Polygon",
            "coordinates": [
                [[30.0, 31.0], [30.1, 31.0], [30.1, 31.1], [30.0, 31.1], [30.0, 31.0]]
            ]
        }

        result = GeometryValidator.validate_geojson(valid_geojson)
        assert result == valid_geojson

    def test_invalid_geometry_type(self):
        """Test invalid geometry type fails"""

        invalid_geojson = {
            "type": "InvalidType",
            "coordinates": [[30.0, 31.0]]
        }

        with pytest.raises(Exception) as exc_info:
            GeometryValidator.validate_geojson(invalid_geojson)

        assert "غير مدعوم" in str(exc_info.value.message_ar)

    def test_geometry_too_complex(self):
        """Test geometry with too many vertices fails"""

        # Create polygon with 1001 vertices
        coords = [[float(i), float(i)] for i in range(1001)]
        coords.append(coords[0])  # Close the polygon

        complex_geojson = {
            "type": "Polygon",
            "coordinates": [coords]
        }

        with pytest.raises(Exception) as exc_info:
            GeometryValidator.validate_geojson(complex_geojson)

        assert "معقد جداً" in str(exc_info.value.message_ar)

    def test_valid_crop_type(self):
        """Test valid crop type"""

        result = FieldValidators.validate_crop_type("tomato")
        assert result == "tomato"

    def test_invalid_crop_type(self):
        """Test invalid crop type fails"""

        with pytest.raises(ValidationException) as exc_info:
            FieldValidators.validate_crop_type("invalid_crop")

        assert exc_info.value.error_code == ErrorCode.VALIDATION_ERROR

    def test_valid_field_name(self):
        """Test valid field name"""

        result = FieldValidators.validate_field_name("  Test Field  ")
        assert result == "Test Field"

    def test_empty_field_name(self):
        """Test empty field name fails"""

        with pytest.raises(ValidationException):
            FieldValidators.validate_field_name("")

    def test_field_name_too_long(self):
        """Test field name too long fails"""

        long_name = "a" * 256

        with pytest.raises(ValidationException):
            FieldValidators.validate_field_name(long_name)

    def test_positive_validation(self):
        """Test positive number validation"""

        result = NumericValidators.validate_positive(5.0, "area")
        assert result == 5.0

        with pytest.raises(ValidationException):
            NumericValidators.validate_positive(-1.0, "area")

    def test_percentage_validation(self):
        """Test percentage validation"""

        assert NumericValidators.validate_percentage(50.0, "humidity") == 50.0

        with pytest.raises(ValidationException):
            NumericValidators.validate_percentage(150.0, "humidity")

    def test_pagination_validation(self):
        """Test pagination validation"""

        page, page_size = PaginationValidator.validate(1, 50)
        assert page == 1
        assert page_size == 50

        # Test invalid page
        with pytest.raises(ValidationException):
            PaginationValidator.validate(0, 50)

        # Test page size too large
        with pytest.raises(ValidationException):
            PaginationValidator.validate(1, 2000)


# ===================================================================
# RETRY TESTS
# ===================================================================

class TestRetry:
    """Test retry mechanism"""

    @pytest.mark.asyncio
    async def test_retry_success_first_attempt(self):
        """Test function succeeds on first attempt"""

        call_count = 0

        @retry_async(RetryConfig(max_attempts=3))
        async def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_function()

        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self):
        """Test function succeeds after retries"""

        call_count = 0

        @retry_async(RetryConfig(max_attempts=3, initial_delay=0.1))
        async def flaky_function():
            nonlocal call_count
            call_count += 1

            if call_count < 3:
                raise ConnectionError("Temporary failure")

            return "success"

        result = await flaky_function()

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_all_attempts_fail(self):
        """Test all retry attempts fail"""

        call_count = 0

        @retry_async(RetryConfig(max_attempts=3, initial_delay=0.1))
        async def failing_function():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Permanent failure")

        with pytest.raises(ConnectionError):
            await failing_function()

        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exponential_backoff(self):
        """Test exponential backoff timing"""

        config = RetryConfig(
            max_attempts=4,
            initial_delay=1.0,
            strategy=RetryStrategy.EXPONENTIAL,
            backoff_multiplier=2.0
        )

        assert config.calculate_delay(1) == 1.0
        assert config.calculate_delay(2) == 2.0
        assert config.calculate_delay(3) == 4.0
        assert config.calculate_delay(4) == 8.0


# ===================================================================
# CIRCUIT BREAKER TESTS
# ===================================================================

class TestCircuitBreaker:
    """Test circuit breaker pattern"""

    def test_circuit_breaker_closed_initially(self):
        """Test circuit breaker starts in CLOSED state"""

        breaker = CircuitBreaker(name="test", failure_threshold=3)

        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures"""

        breaker = CircuitBreaker(name="test", failure_threshold=3)

        async def failing_function():
            raise ConnectionError("Service down")

        # First 3 failures should open the circuit
        for i in range(3):
            with pytest.raises(ConnectionError):
                await breaker.call_async(failing_function)

        # Circuit should be open now
        assert breaker.state == CircuitState.OPEN

        # Next call should be rejected immediately
        with pytest.raises(Exception) as exc_info:
            await breaker.call_async(failing_function)

        assert "Circuit breaker" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_after_timeout(self):
        """Test circuit breaker transitions to HALF_OPEN after timeout"""

        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            timeout=0.1  # 100ms
        )

        async def failing_function():
            raise ConnectionError("Service down")

        # Open the circuit
        for i in range(2):
            with pytest.raises(ConnectionError):
                await breaker.call_async(failing_function)

        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        await asyncio.sleep(0.15)

        # Should transition to HALF_OPEN
        assert breaker.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_circuit_breaker_closes_after_successes(self):
        """Test circuit breaker closes after successful calls"""

        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            success_threshold=2,
            timeout=0.1
        )

        call_count = 0

        async def recovering_function():
            nonlocal call_count
            call_count += 1

            # Fail first 2 times, then succeed
            if call_count <= 2:
                raise ConnectionError("Service down")

            return "success"

        # Open the circuit
        for i in range(2):
            with pytest.raises(ConnectionError):
                await breaker.call_async(recovering_function)

        assert breaker.state == CircuitState.OPEN

        # Wait for timeout -> HALF_OPEN
        await asyncio.sleep(0.15)

        # Two successful calls should close the circuit
        result1 = await breaker.call_async(recovering_function)
        result2 = await breaker.call_async(recovering_function)

        assert result1 == "success"
        assert result2 == "success"
        assert breaker.state == CircuitState.CLOSED

    def test_circuit_breaker_metrics(self):
        """Test circuit breaker metrics"""

        breaker = CircuitBreaker(name="test", failure_threshold=3)

        metrics = breaker.get_metrics()

        assert metrics["name"] == "test"
        assert metrics["state"] == CircuitState.CLOSED
        assert metrics["failure_count"] == 0


# ===================================================================
# INTEGRATION TEST
# ===================================================================

@pytest.mark.asyncio
async def test_end_to_end_error_handling():
    """Test complete error handling flow"""

    from multi-repo.geo_core.app.main_enhanced import app

    client = TestClient(app)

    # Test successful request
    response = client.get("/")
    assert response.status_code == 200
    assert "Sahool Geo-Core" in response.json()["service"]

    # Test validation error
    response = client.post("/api/v2/fields", json={
        "name": "",  # Empty name should fail
        "geometry": {"type": "Point", "coordinates": [0, 0]}
    })
    assert response.status_code == 400
    assert "error_code" in response.json()

    # Test not found
    response = client.get("/api/v2/fields/not-found")
    assert response.status_code == 404
    assert response.json()["error_code"] == "NOT_FOUND"

    # Test health check
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()


# ===================================================================
# RUN TESTS
# ===================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
