"""
Comprehensive Tests for SQL Injection Prevention System
Tests SecureQueryBuilder, input validation, and attack prevention
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from shared.sql_security import (
    SecureQueryBuilder,
    SQLInjectionError,
    execute_safe_query,
    execute_safe_query_sync,
    get_db_session
)


class TestSecureQueryBuilder:
    """Test SecureQueryBuilder core functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.builder = SecureQueryBuilder()

    # ==================== Input Validation Tests ====================

    def test_validate_input_clean(self):
        """Test that clean input passes validation"""
        # Should not raise
        self.builder.validate_input("normal_input", "test")
        self.builder.validate_input("user@example.com", "email")
        self.builder.validate_input("123456", "id")

    def test_validate_input_sql_comment(self):
        """Test detection of SQL comment injection"""
        with pytest.raises(SQLInjectionError, match="dangerous pattern"):
            self.builder.validate_input("' OR '1'='1' --", "input")

    def test_validate_input_union_select(self):
        """Test detection of UNION SELECT attack"""
        with pytest.raises(SQLInjectionError, match="dangerous pattern"):
            self.builder.validate_input("1' UNION SELECT password FROM users --", "input")

    def test_validate_input_drop_table(self):
        """Test detection of DROP TABLE attack"""
        with pytest.raises(SQLInjectionError, match="dangerous pattern"):
            self.builder.validate_input("'; DROP TABLE users; --", "input")

    def test_validate_input_multi_line_comment(self):
        """Test detection of multi-line comment attack"""
        with pytest.raises(SQLInjectionError, match="dangerous pattern"):
            self.builder.validate_input("/* malicious */ SELECT * FROM users", "input")

    def test_validate_input_stacked_queries(self):
        """Test detection of stacked queries"""
        with pytest.raises(SQLInjectionError, match="dangerous pattern"):
            self.builder.validate_input("1; DELETE FROM users WHERE 1=1", "input")

    def test_validate_input_hex_encoding(self):
        """Test detection of hex-encoded attacks"""
        with pytest.raises(SQLInjectionError, match="dangerous pattern"):
            self.builder.validate_input("0x53454c454354", "input")

    def test_validate_input_xp_cmdshell(self):
        """Test detection of xp_cmdshell attack"""
        with pytest.raises(SQLInjectionError, match="dangerous pattern"):
            self.builder.validate_input("'; EXEC xp_cmdshell('dir'); --", "input")

    # ==================== Table Name Validation Tests ====================

    def test_validate_table_name_valid(self):
        """Test that valid table names pass"""
        assert self.builder.validate_table_name("users") == True
        assert self.builder.validate_table_name("sensor_data") == True
        assert self.builder.validate_table_name("field_measurements") == True

    def test_validate_table_name_invalid_characters(self):
        """Test rejection of invalid table names"""
        with pytest.raises(SQLInjectionError, match="Invalid table name"):
            self.builder.validate_table_name("users; DROP TABLE")

        with pytest.raises(SQLInjectionError, match="Invalid table name"):
            self.builder.validate_table_name("users--")

        with pytest.raises(SQLInjectionError, match="Invalid table name"):
            self.builder.validate_table_name("users/*comment*/")

    def test_validate_table_name_sql_injection(self):
        """Test rejection of SQL injection in table names"""
        with pytest.raises(SQLInjectionError, match="Invalid table name"):
            self.builder.validate_table_name("users' OR '1'='1")

    # ==================== Column Name Validation Tests ====================

    def test_validate_column_name_valid(self):
        """Test that valid column names pass"""
        assert self.builder.validate_column_name("id") == True
        assert self.builder.validate_column_name("user_name") == True
        assert self.builder.validate_column_name("created_at") == True

    def test_validate_column_name_invalid(self):
        """Test rejection of invalid column names"""
        with pytest.raises(SQLInjectionError, match="Invalid column name"):
            self.builder.validate_column_name("id; DROP TABLE")

        with pytest.raises(SQLInjectionError, match="Invalid column name"):
            self.builder.validate_column_name("id--")

    # ==================== SELECT Query Builder Tests ====================

    def test_build_select_simple(self):
        """Test simple SELECT query"""
        query, params = self.builder.build_select("users")

        assert query == "SELECT * FROM users"
        assert params == {}

    def test_build_select_with_columns(self):
        """Test SELECT with specific columns"""
        query, params = self.builder.build_select(
            "users",
            columns=["id", "name", "email"]
        )

        assert query == "SELECT id, name, email FROM users"
        assert params == {}

    def test_build_select_with_where(self):
        """Test SELECT with WHERE clause"""
        query, params = self.builder.build_select(
            "users",
            where={"id": 123, "status": "active"}
        )

        assert "SELECT * FROM users WHERE" in query
        assert "id = :id_0" in query
        assert "status = :status_1" in query
        assert params == {"id_0": 123, "status_1": "active"}

    def test_build_select_with_order_by(self):
        """Test SELECT with ORDER BY"""
        query, params = self.builder.build_select(
            "users",
            order_by=[("created_at", "DESC"), ("name", "ASC")]
        )

        assert query == "SELECT * FROM users ORDER BY created_at DESC, name ASC"
        assert params == {}

    def test_build_select_with_limit(self):
        """Test SELECT with LIMIT"""
        query, params = self.builder.build_select(
            "users",
            limit=10
        )

        assert query == "SELECT * FROM users LIMIT 10"
        assert params == {}

    def test_build_select_complex(self):
        """Test complex SELECT with all options"""
        query, params = self.builder.build_select(
            "sensor_data",
            columns=["device_id", "temperature", "humidity"],
            where={"device_id": "sensor_001", "status": "active"},
            order_by=[("timestamp", "DESC")],
            limit=100
        )

        assert "SELECT device_id, temperature, humidity FROM sensor_data" in query
        assert "WHERE" in query
        assert "device_id = :device_id_0" in query
        assert "status = :status_1" in query
        assert "ORDER BY timestamp DESC" in query
        assert "LIMIT 100" in query
        assert params == {"device_id_0": "sensor_001", "status_1": "active"}

    def test_build_select_invalid_table(self):
        """Test SELECT with invalid table name"""
        with pytest.raises(SQLInjectionError, match="Invalid table name"):
            self.builder.build_select("users; DROP TABLE users")

    def test_build_select_invalid_column(self):
        """Test SELECT with invalid column name"""
        with pytest.raises(SQLInjectionError, match="Invalid column name"):
            self.builder.build_select(
                "users",
                columns=["id", "name; DROP TABLE users"]
            )

    # ==================== INSERT Query Builder Tests ====================

    def test_build_insert_simple(self):
        """Test simple INSERT query"""
        query, params = self.builder.build_insert(
            "users",
            {"name": "John Doe", "email": "john@example.com"}
        )

        assert "INSERT INTO users" in query
        assert "name, email" in query
        assert ":name, :email" in query
        assert params == {"name": "John Doe", "email": "john@example.com"}

    def test_build_insert_with_returning(self):
        """Test INSERT with RETURNING clause"""
        query, params = self.builder.build_insert(
            "users",
            {"name": "Jane Doe"},
            returning=["id", "created_at"]
        )

        assert "INSERT INTO users" in query
        assert "RETURNING id, created_at" in query

    def test_build_insert_invalid_table(self):
        """Test INSERT with invalid table name"""
        with pytest.raises(SQLInjectionError, match="Invalid table name"):
            self.builder.build_insert(
                "users; DROP TABLE",
                {"name": "test"}
            )

    def test_build_insert_invalid_column(self):
        """Test INSERT with invalid column name"""
        with pytest.raises(SQLInjectionError, match="Invalid column name"):
            self.builder.build_insert(
                "users",
                {"name; DROP TABLE": "test"}
            )

    # ==================== UPDATE Query Builder Tests ====================

    def test_build_update_simple(self):
        """Test simple UPDATE query"""
        query, params = self.builder.build_update(
            "users",
            values={"name": "John Updated", "status": "inactive"},
            where={"id": 123}
        )

        assert "UPDATE users SET" in query
        assert "name = :name" in query
        assert "status = :status" in query
        assert "WHERE id = :id_where" in query
        assert params["name"] == "John Updated"
        assert params["status"] == "inactive"
        assert params["id_where"] == 123

    def test_build_update_with_returning(self):
        """Test UPDATE with RETURNING clause"""
        query, params = self.builder.build_update(
            "users",
            values={"status": "active"},
            where={"id": 123},
            returning=["id", "status", "updated_at"]
        )

        assert "UPDATE users SET" in query
        assert "WHERE id = :id_where" in query
        assert "RETURNING id, status, updated_at" in query

    def test_build_update_without_where(self):
        """Test UPDATE without WHERE clause (should raise error)"""
        with pytest.raises(SQLInjectionError, match="UPDATE without WHERE"):
            self.builder.build_update(
                "users",
                values={"status": "active"}
            )

    def test_build_update_invalid_table(self):
        """Test UPDATE with invalid table name"""
        with pytest.raises(SQLInjectionError, match="Invalid table name"):
            self.builder.build_update(
                "users; DROP TABLE",
                values={"name": "test"},
                where={"id": 1}
            )

    # ==================== DELETE Query Builder Tests ====================

    def test_build_delete_simple(self):
        """Test simple DELETE query"""
        query, params = self.builder.build_delete(
            "users",
            where={"id": 123}
        )

        assert query == "DELETE FROM users WHERE id = :id_0"
        assert params == {"id_0": 123}

    def test_build_delete_with_returning(self):
        """Test DELETE with RETURNING clause"""
        query, params = self.builder.build_delete(
            "users",
            where={"id": 123},
            returning=["id", "name"]
        )

        assert "DELETE FROM users WHERE" in query
        assert "RETURNING id, name" in query

    def test_build_delete_without_where(self):
        """Test DELETE without WHERE clause (should raise error)"""
        with pytest.raises(SQLInjectionError, match="DELETE without WHERE"):
            self.builder.build_delete("users")

    def test_build_delete_invalid_table(self):
        """Test DELETE with invalid table name"""
        with pytest.raises(SQLInjectionError, match="Invalid table name"):
            self.builder.build_delete(
                "users; DROP TABLE",
                where={"id": 1}
            )

    # ==================== Dangerous Pattern Detection Tests ====================

    def test_dangerous_patterns_comprehensive(self):
        """Test comprehensive list of dangerous patterns"""
        dangerous_inputs = [
            "' OR '1'='1",
            "admin'--",
            "'; DROP TABLE users; --",
            "1' UNION SELECT NULL, username, password FROM users--",
            "admin' OR 1=1/*",
            "1; DELETE FROM users WHERE 1=1",
            "'; EXEC xp_cmdshell('dir'); --",
            "' AND 1=0 UNION ALL SELECT 'admin', 'password'",
            "1' AND '1'='1",
            "0x53454c454354",  # hex encoded SELECT
            "char(0x53,0x45,0x4c,0x45,0x43,0x54)",  # char encoding
        ]

        for dangerous_input in dangerous_inputs:
            with pytest.raises(SQLInjectionError, match="dangerous pattern"):
                self.builder.validate_input(dangerous_input, "test")

    # ==================== Edge Cases Tests ====================

    def test_empty_table_name(self):
        """Test empty table name"""
        with pytest.raises(SQLInjectionError, match="Invalid table name"):
            self.builder.build_select("")

    def test_none_table_name(self):
        """Test None table name"""
        with pytest.raises((SQLInjectionError, AttributeError)):
            self.builder.build_select(None)

    def test_special_characters_in_values(self):
        """Test that special characters in VALUES are OK (will be parameterized)"""
        # These should NOT raise errors because they're in values, not identifiers
        query, params = self.builder.build_insert(
            "users",
            {"comment": "User said: 'hello' and 1=1"}
        )

        assert params["comment"] == "User said: 'hello' and 1=1"

    def test_unicode_in_values(self):
        """Test Unicode characters in values"""
        query, params = self.builder.build_insert(
            "users",
            {"name": "مستخدم", "comment": "This is Arabic: مرحبا"}
        )

        assert params["name"] == "مستخدم"
        assert params["comment"] == "This is Arabic: مرحبا"


class TestExecuteSafeQuery:
    """Test safe query execution functions"""

    @pytest.mark.asyncio
    async def test_execute_safe_query_async_fetch_all(self):
        """Test async query execution with fetch all"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = Mock()
        mock_row1 = Mock()
        mock_row1._mapping = {"id": 1, "name": "John"}
        mock_row2 = Mock()
        mock_row2._mapping = {"id": 2, "name": "Jane"}
        mock_result.fetchall.return_value = [mock_row1, mock_row2]
        mock_session.execute.return_value = mock_result

        query = "SELECT * FROM users WHERE id = :id"
        params = {"id": 1}

        result = await execute_safe_query(mock_session, query, params, fetch="all")

        assert len(result) == 2
        assert result[0] == {"id": 1, "name": "John"}
        assert result[1] == {"id": 2, "name": "Jane"}
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_safe_query_async_fetch_one(self):
        """Test async query execution with fetch one"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = Mock()
        mock_row = Mock()
        mock_row._mapping = {"id": 1, "name": "John"}
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        query = "SELECT * FROM users WHERE id = :id"
        params = {"id": 1}

        result = await execute_safe_query(mock_session, query, params, fetch="one")

        assert result == {"id": 1, "name": "John"}

    @pytest.mark.asyncio
    async def test_execute_safe_query_async_no_fetch(self):
        """Test async query execution without fetching (INSERT/UPDATE/DELETE)"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = Mock()
        mock_session.execute.return_value = mock_result

        query = "INSERT INTO users (name) VALUES (:name)"
        params = {"name": "John"}

        result = await execute_safe_query(mock_session, query, params, fetch=None)

        assert result is None
        mock_session.commit.assert_called_once()

    def test_execute_safe_query_sync_fetch_all(self):
        """Test sync query execution with fetch all"""
        mock_session = Mock()
        mock_result = Mock()
        mock_row1 = Mock()
        mock_row1._mapping = {"id": 1, "name": "John"}
        mock_row2 = Mock()
        mock_row2._mapping = {"id": 2, "name": "Jane"}
        mock_result.fetchall.return_value = [mock_row1, mock_row2]
        mock_session.execute.return_value = mock_result

        query = "SELECT * FROM users WHERE id = :id"
        params = {"id": 1}

        result = execute_safe_query_sync(mock_session, query, params, fetch="all")

        assert len(result) == 2
        assert result[0] == {"id": 1, "name": "John"}

    def test_execute_safe_query_sync_no_fetch(self):
        """Test sync query execution without fetching"""
        mock_session = Mock()
        mock_result = Mock()
        mock_session.execute.return_value = mock_result

        query = "DELETE FROM users WHERE id = :id"
        params = {"id": 1}

        result = execute_safe_query_sync(mock_session, query, params, fetch=None)

        assert result is None
        mock_session.commit.assert_called_once()


class TestSecurityScenarios:
    """Test real-world security scenarios"""

    def setup_method(self):
        self.builder = SecureQueryBuilder()

    def test_authentication_bypass_attempt(self):
        """Test prevention of authentication bypass"""
        # Attacker tries: username = admin'-- password = anything
        malicious_username = "admin'--"

        with pytest.raises(SQLInjectionError):
            self.builder.validate_input(malicious_username, "username")

    def test_data_extraction_attempt(self):
        """Test prevention of data extraction via UNION"""
        # Attacker tries: id = 1' UNION SELECT username,password FROM users--
        malicious_id = "1' UNION SELECT username, password FROM users--"

        with pytest.raises(SQLInjectionError):
            self.builder.validate_input(malicious_id, "id")

    def test_blind_sql_injection_attempt(self):
        """Test prevention of blind SQL injection"""
        # Attacker tries: id = 1' AND SUBSTRING(password,1,1)='a
        malicious_id = "1' AND SUBSTRING(password,1,1)='a"

        with pytest.raises(SQLInjectionError):
            self.builder.validate_input(malicious_id, "id")

    def test_time_based_sql_injection_attempt(self):
        """Test prevention of time-based SQL injection"""
        # Attacker tries: id = 1' AND SLEEP(5)--
        malicious_id = "1' AND SLEEP(5)--"

        with pytest.raises(SQLInjectionError):
            self.builder.validate_input(malicious_id, "id")

    def test_safe_user_input(self):
        """Test that normal user input works correctly"""
        # Normal query with user input
        query, params = self.builder.build_select(
            "sensors",
            where={"device_id": "sensor_001", "status": "active"}
        )

        # Verify parameterized query
        assert ":device_id_0" in query
        assert ":status_1" in query
        assert params["device_id_0"] == "sensor_001"
        assert params["status_1"] == "active"

    def test_email_with_special_chars(self):
        """Test email addresses with special characters"""
        # Email addresses should work in VALUES
        query, params = self.builder.build_insert(
            "users",
            {"email": "user+tag@example.com"}
        )

        assert params["email"] == "user+tag@example.com"

    def test_json_data_storage(self):
        """Test storing JSON data (common in modern apps)"""
        json_data = '{"key": "value", "nested": {"data": "test"}}'

        query, params = self.builder.build_insert(
            "logs",
            {"data": json_data}
        )

        assert params["data"] == json_data


class TestPerformance:
    """Test performance characteristics"""

    def setup_method(self):
        self.builder = SecureQueryBuilder()

    def test_pattern_compilation_performance(self):
        """Test that patterns are compiled once"""
        import time

        # First validation (compiles patterns)
        start = time.time()
        try:
            self.builder.validate_input("test", "test")
        except:
            pass
        first_time = time.time() - start

        # Second validation (uses compiled patterns)
        start = time.time()
        for _ in range(100):
            try:
                self.builder.validate_input("test", "test")
            except:
                pass
        second_time = time.time() - start

        # Compiled patterns should be much faster
        assert second_time < first_time * 10

    def test_large_where_clause_performance(self):
        """Test performance with large WHERE clauses"""
        # Build query with 50 WHERE conditions
        where_dict = {f"field_{i}": f"value_{i}" for i in range(50)}

        query, params = self.builder.build_select(
            "large_table",
            where=where_dict
        )

        # Verify all parameters are included
        assert len(params) == 50
        assert all(f"field_{i}_" in query for i in range(50))


# ==================== Integration Tests ====================

class TestIntegration:
    """Integration tests with mock database"""

    def setup_method(self):
        self.builder = SecureQueryBuilder()

    @pytest.mark.asyncio
    async def test_full_crud_cycle_async(self):
        """Test complete CRUD cycle with async execution"""
        mock_session = AsyncMock(spec=AsyncSession)

        # CREATE
        insert_query, insert_params = self.builder.build_insert(
            "users",
            {"name": "Test User", "email": "test@example.com"},
            returning=["id"]
        )

        mock_result = Mock()
        mock_row = Mock()
        mock_row._mapping = {"id": 1}
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        result = await execute_safe_query(mock_session, insert_query, insert_params, fetch="one")
        assert result["id"] == 1

        # READ
        select_query, select_params = self.builder.build_select(
            "users",
            where={"id": 1}
        )

        mock_row._mapping = {"id": 1, "name": "Test User", "email": "test@example.com"}
        mock_result.fetchone.return_value = mock_row

        result = await execute_safe_query(mock_session, select_query, select_params, fetch="one")
        assert result["name"] == "Test User"

        # UPDATE
        update_query, update_params = self.builder.build_update(
            "users",
            values={"name": "Updated User"},
            where={"id": 1}
        )

        await execute_safe_query(mock_session, update_query, update_params, fetch=None)

        # DELETE
        delete_query, delete_params = self.builder.build_delete(
            "users",
            where={"id": 1}
        )

        await execute_safe_query(mock_session, delete_query, delete_params, fetch=None)

    def test_full_crud_cycle_sync(self):
        """Test complete CRUD cycle with sync execution"""
        mock_session = Mock()

        # CREATE
        insert_query, insert_params = self.builder.build_insert(
            "users",
            {"name": "Test User"},
            returning=["id"]
        )

        mock_result = Mock()
        mock_row = Mock()
        mock_row._mapping = {"id": 1}
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        result = execute_safe_query_sync(mock_session, insert_query, insert_params, fetch="one")
        assert result["id"] == 1


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
