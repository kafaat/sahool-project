"""
Security Tests: SQL Injection Prevention
اختبارات أمان شاملة لمنع حقن SQL
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from shared.sql_security import (
    SecureQueryBuilder,
    SQLInjectionError
)


class TestSQLInjectionPrevention:
    """Test SQL injection prevention"""

    def setup_method(self):
        """Setup test fixtures"""
        self.builder = SecureQueryBuilder()

    # ==================== Attack Prevention Tests ====================

    def test_prevent_comment_injection(self):
        """Test prevention of SQL comment injection"""
        attacks = [
            "admin'--",
            "user'; --",
            "test'-- ",
        ]

        for attack in attacks:
            with pytest.raises(SQLInjectionError, match="dangerous pattern"):
                self.builder.validate_input(attack, "username")

    def test_prevent_union_injection(self):
        """Test prevention of UNION SELECT attacks"""
        attacks = [
            "1' UNION SELECT password FROM users--",
            "test' UNION ALL SELECT NULL, username, password FROM users--",
            "' UNION SELECT 1,2,3--",
        ]

        for attack in attacks:
            with pytest.raises(SQLInjectionError, match="dangerous pattern"):
                self.builder.validate_input(attack, "id")

    def test_prevent_drop_table(self):
        """Test prevention of DROP TABLE attacks"""
        attacks = [
            "'; DROP TABLE users; --",
            "test'; DROP TABLE sensors CASCADE; --",
            "1; DROP DATABASE sahool; --",
        ]

        for attack in attacks:
            with pytest.raises(SQLInjectionError, match="dangerous pattern"):
                self.builder.validate_input(attack, "input")

    def test_prevent_stacked_queries(self):
        """Test prevention of stacked query attacks"""
        attacks = [
            "1; DELETE FROM users WHERE 1=1",
            "test; UPDATE users SET password='hacked'",
            "admin; INSERT INTO admins VALUES ('hacker', 'pass')",
        ]

        for attack in attacks:
            with pytest.raises(SQLInjectionError, match="dangerous pattern"):
                self.builder.validate_input(attack, "input")

    def test_prevent_blind_sql_injection(self):
        """Test prevention of blind SQL injection"""
        attacks = [
            "1' AND SLEEP(5)--",
            "admin' AND 1=1--",
            "test' AND SUBSTRING(password,1,1)='a'--",
        ]

        for attack in attacks:
            with pytest.raises(SQLInjectionError, match="dangerous pattern"):
                self.builder.validate_input(attack, "input")

    # ==================== Safe Input Tests ====================

    def test_safe_normal_input(self):
        """Test that normal input passes validation"""
        safe_inputs = [
            "john_doe",
            "user@example.com",
            "sensor_001",
            "Test Field Name",
            "123456",
        ]

        for safe_input in safe_inputs:
            # Should not raise
            self.builder.validate_input(safe_input, "test")

    def test_safe_special_characters_in_values(self):
        """Test that special characters in values are safe (parameterized)"""
        # These should be OK because they're in values, not identifiers
        query, params = self.builder.build_insert(
            "users",
            {
                "comment": "User said: 'hello' and goodbye",
                "email": "user+tag@example.com"
            }
        )

        assert params["comment"] == "User said: 'hello' and goodbye"
        assert params["email"] == "user+tag@example.com"

    # ==================== Query Builder Security ====================

    def test_parameterized_where_clause(self):
        """Test that WHERE clauses are properly parameterized"""
        query, params = self.builder.build_select(
            "users",
            where={"username": "admin'--", "password": "test"}
        )

        # Query should use parameters, not inline values
        assert "admin'--" not in query
        assert ":username_0" in query
        assert ":password_1" in query
        assert params["username_0"] == "admin'--"

    def test_prevent_sql_in_table_name(self):
        """Test that SQL injection in table names is blocked"""
        malicious_tables = [
            "users; DROP TABLE users",
            "users--",
            "users/*comment*/",
        ]

        for table in malicious_tables:
            with pytest.raises(SQLInjectionError, match="Invalid table name"):
                self.builder.build_select(table)

    def test_prevent_sql_in_column_name(self):
        """Test that SQL injection in column names is blocked"""
        with pytest.raises(SQLInjectionError, match="Invalid column name"):
            self.builder.build_select(
                "users",
                columns=["id", "name; DROP TABLE users"]
            )

    # ==================== Real-World Attack Scenarios ====================

    def test_authentication_bypass_prevention(self):
        """Test prevention of authentication bypass"""
        # Attacker tries: username = admin'-- password = anything
        username = "admin'--"
        password = "anything"

        query, params = self.builder.build_select(
            "users",
            where={"username": username, "password": password}
        )

        # The attack should be neutralized through parameterization
        assert "admin'--" not in query
        assert params["username_0"] == "admin'--"
        assert params["password_1"] == "anything"

    def test_data_exfiltration_prevention(self):
        """Test prevention of data exfiltration"""
        # Attacker tries: id = 1' UNION SELECT username, password FROM users--
        malicious_id = "1' UNION SELECT username, password FROM users--"

        query, params = self.builder.build_select(
            "sensors",
            where={"device_id": malicious_id}
        )

        # The UNION attack should be safely parameterized
        assert "UNION" not in query.upper() or ":device_id_0" in query
        assert params["device_id_0"] == malicious_id


class TestSecurityBestPractices:
    """Test that security best practices are enforced"""

    def setup_method(self):
        self.builder = SecureQueryBuilder()

    def test_update_requires_where_clause(self):
        """Test that UPDATE requires WHERE clause (prevent accidental mass updates)"""
        with pytest.raises(SQLInjectionError, match="UPDATE without WHERE"):
            self.builder.build_update(
                "users",
                values={"status": "inactive"}
                # Missing WHERE clause!
            )

    def test_delete_requires_where_clause(self):
        """Test that DELETE requires WHERE clause (prevent accidental mass deletes)"""
        with pytest.raises(SQLInjectionError, match="DELETE without WHERE"):
            self.builder.build_delete("users")

    def test_table_name_alphanumeric_only(self):
        """Test that table names must be alphanumeric + underscore"""
        valid_tables = ["users", "sensor_data", "field_measurements"]
        for table in valid_tables:
            assert self.builder.validate_table_name(table) == True

        invalid_tables = ["users!", "table.name", "table-name"]
        for table in invalid_tables:
            with pytest.raises(SQLInjectionError):
                self.builder.validate_table_name(table)


# ==================== Integration Tests ====================

class TestSecurityIntegration:
    """Integration tests for complete security workflows"""

    def setup_method(self):
        self.builder = SecureQueryBuilder()

    def test_complete_crud_security(self):
        """Test that complete CRUD operations are secure"""

        # CREATE - with potentially malicious input
        malicious_name = "Test'; DROP TABLE fields; --"
        malicious_email = "user' OR '1'='1"

        insert_query, insert_params = self.builder.build_insert(
            "users",
            {
                "name": malicious_name,
                "email": malicious_email
            }
        )

        # Malicious content should be in params, not query
        assert "DROP TABLE" not in insert_query
        assert insert_params["name"] == malicious_name
        assert insert_params["email"] == malicious_email

        # READ - with malicious search
        malicious_search = "admin'--"

        select_query, select_params = self.builder.build_select(
            "users",
            where={"name": malicious_search}
        )

        assert "--" not in select_query or ":name_0" in select_query
        assert select_params["name_0"] == malicious_search

        # UPDATE - with malicious data
        update_query, update_params = self.builder.build_update(
            "users",
            values={"status": "'; DROP TABLE users; --"},
            where={"id": "1' OR '1'='1"}
        )

        assert "DROP TABLE" not in update_query
        assert update_params["status"] == "'; DROP TABLE users; --"

        # DELETE - with malicious condition
        delete_query, delete_params = self.builder.build_delete(
            "users",
            where={"id": "1' OR '1'='1"}
        )

        assert delete_params["id_0"] == "1' OR '1'='1"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
