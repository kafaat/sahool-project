"""
SQL Security Module - SQL Injection Prevention
Provides secure SQL query building and execution
"""

import logging
from typing import Any, Dict, List, Optional, Union, Tuple
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
import re

logger = logging.getLogger(__name__)


class SQLInjectionError(Exception):
    """Raised when potential SQL injection is detected"""
    pass


class SecureQueryBuilder:
    """
    Secure SQL query builder with automatic injection prevention

    ALWAYS use parameterized queries with :param syntax
    NEVER use string formatting or concatenation
    """

    def __init__(self):
        self.dangerous_patterns = [
            r"';",  # SQL statement terminator
            r"--",  # SQL comment
            r"/\*",  # SQL comment start
            r"\*/",  # SQL comment end
            r"union\s+select",  # Union-based injection
            r"drop\s+table",  # Drop table
            r"delete\s+from",  # Mass delete
            r"update\s+.*\s+set",  # Mass update (without WHERE in string)
            r"insert\s+into",  # Insert
            r"exec\s*\(",  # Execute
            r"execute\s*\(",  # Execute
            r"xp_",  # Extended stored procedures
            r"sp_",  # Stored procedures
        ]

        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.dangerous_patterns
        ]

    def validate_input(self, value: str, context: str = "input") -> None:
        """
        Validate input for SQL injection patterns

        Args:
            value: Input value to validate
            context: Context for error message

        Raises:
            SQLInjectionError: If dangerous pattern detected
        """
        if not isinstance(value, str):
            return  # Non-string values are safe in parameters

        value_lower = value.lower()

        for i, pattern in enumerate(self.compiled_patterns):
            if pattern.search(value_lower):
                logger.warning(
                    f"🚨 Potential SQL injection detected in {context}: "
                    f"Pattern '{self.dangerous_patterns[i]}' found"
                )
                raise SQLInjectionError(
                    f"Invalid {context}: contains potentially dangerous SQL pattern"
                )

    def build_select(
        self,
        table: str,
        columns: List[str] = None,
        where: Dict[str, Any] = None,
        order_by: str = None,
        limit: int = None,
        offset: int = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Build a safe SELECT query

        Args:
            table: Table name (will be validated)
            columns: List of column names (default: *)
            where: Dictionary of column: value for WHERE clause
            order_by: Column name for ORDER BY
            limit: LIMIT value
            offset: OFFSET value

        Returns:
            Tuple of (query_string, params_dict)

        Example:
            query, params = builder.build_select(
                table="sensors",
                columns=["id", "device_id", "value"],
                where={"device_id": "sensor_001", "active": True},
                order_by="timestamp DESC",
                limit=10
            )
        """
        # Validate table name (alphanumeric + underscore only)
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table):
            raise SQLInjectionError(f"Invalid table name: {table}")

        # Build SELECT clause
        if columns:
            # Validate column names
            for col in columns:
                if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col):
                    raise SQLInjectionError(f"Invalid column name: {col}")
            cols_str = ", ".join(columns)
        else:
            cols_str = "*"

        query = f"SELECT {cols_str} FROM {table}"
        params = {}

        # Build WHERE clause with parameters
        if where:
            where_parts = []
            for i, (col, val) in enumerate(where.items()):
                # Validate column name
                if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col):
                    raise SQLInjectionError(f"Invalid column name: {col}")

                param_name = f"{col}_{i}"
                where_parts.append(f"{col} = :{param_name}")
                params[param_name] = val

            query += " WHERE " + " AND ".join(where_parts)

        # ORDER BY (validate)
        if order_by:
            # Allow column name + optional ASC/DESC
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*(\s+(ASC|DESC))?$', order_by, re.IGNORECASE):
                raise SQLInjectionError(f"Invalid ORDER BY clause: {order_by}")
            query += f" ORDER BY {order_by}"

        # LIMIT and OFFSET (must be integers)
        if limit is not None:
            if not isinstance(limit, int) or limit < 0:
                raise SQLInjectionError("LIMIT must be a non-negative integer")
            query += f" LIMIT {limit}"

        if offset is not None:
            if not isinstance(offset, int) or offset < 0:
                raise SQLInjectionError("OFFSET must be a non-negative integer")
            query += f" OFFSET {offset}"

        return query, params

    def build_insert(
        self,
        table: str,
        data: Dict[str, Any],
        returning: List[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Build a safe INSERT query

        Args:
            table: Table name
            data: Dictionary of column: value
            returning: Optional list of columns to return

        Returns:
            Tuple of (query_string, params_dict)

        Example:
            query, params = builder.build_insert(
                table="sensors",
                data={"device_id": "sensor_001", "value": 25.3},
                returning=["id"]
            )
        """
        # Validate table name
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table):
            raise SQLInjectionError(f"Invalid table name: {table}")

        if not data:
            raise ValueError("INSERT data cannot be empty")

        # Validate column names and build query
        columns = []
        placeholders = []
        params = {}

        for col, val in data.items():
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col):
                raise SQLInjectionError(f"Invalid column name: {col}")

            columns.append(col)
            placeholders.append(f":{col}")
            params[col] = val

        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"

        # RETURNING clause
        if returning:
            for col in returning:
                if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col):
                    raise SQLInjectionError(f"Invalid column name: {col}")
            query += f" RETURNING {', '.join(returning)}"

        return query, params

    def build_update(
        self,
        table: str,
        data: Dict[str, Any],
        where: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Build a safe UPDATE query

        Args:
            table: Table name
            data: Dictionary of column: new_value
            where: Dictionary of column: value for WHERE clause

        Returns:
            Tuple of (query_string, params_dict)

        Example:
            query, params = builder.build_update(
                table="sensors",
                data={"active": False},
                where={"device_id": "sensor_001"}
            )
        """
        # Validate table name
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table):
            raise SQLInjectionError(f"Invalid table name: {table}")

        if not data:
            raise ValueError("UPDATE data cannot be empty")

        if not where:
            raise ValueError("UPDATE requires WHERE clause to prevent mass updates")

        params = {}

        # Build SET clause
        set_parts = []
        for col, val in data.items():
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col):
                raise SQLInjectionError(f"Invalid column name: {col}")

            param_name = f"set_{col}"
            set_parts.append(f"{col} = :{param_name}")
            params[param_name] = val

        query = f"UPDATE {table} SET {', '.join(set_parts)}"

        # Build WHERE clause
        where_parts = []
        for col, val in where.items():
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col):
                raise SQLInjectionError(f"Invalid column name: {col}")

            param_name = f"where_{col}"
            where_parts.append(f"{col} = :{param_name}")
            params[param_name] = val

        query += " WHERE " + " AND ".join(where_parts)

        return query, params

    def build_delete(
        self,
        table: str,
        where: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Build a safe DELETE query

        Args:
            table: Table name
            where: Dictionary of column: value for WHERE clause

        Returns:
            Tuple of (query_string, params_dict)

        Example:
            query, params = builder.build_delete(
                table="sensors",
                where={"device_id": "sensor_001"}
            )
        """
        # Validate table name
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table):
            raise SQLInjectionError(f"Invalid table name: {table}")

        if not where:
            raise ValueError("DELETE requires WHERE clause to prevent mass deletion")

        # Build WHERE clause
        where_parts = []
        params = {}

        for col, val in where.items():
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col):
                raise SQLInjectionError(f"Invalid column name: {col}")

            param_name = f"{col}"
            where_parts.append(f"{col} = :{param_name}")
            params[param_name] = val

        query = f"DELETE FROM {table} WHERE " + " AND ".join(where_parts)

        return query, params


async def execute_safe_query(
    session: AsyncSession,
    query: str,
    params: Dict[str, Any],
    fetch: str = "all"
) -> Union[List[Dict], Dict, None]:
    """
    Execute a safe parameterized query

    Args:
        session: SQLAlchemy async session
        query: SQL query with :param placeholders
        params: Dictionary of parameter values
        fetch: "all", "one", or "none"

    Returns:
        Query results

    Example:
        result = await execute_safe_query(
            session,
            "SELECT * FROM sensors WHERE device_id = :device_id",
            {"device_id": "sensor_001"},
            fetch="all"
        )
    """
    try:
        stmt = text(query)
        result = await session.execute(stmt, params)

        if fetch == "all":
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]
        elif fetch == "one":
            row = result.fetchone()
            return dict(row._mapping) if row else None
        else:  # "none" for INSERT/UPDATE/DELETE
            await session.commit()
            return None

    except Exception as e:
        logger.error(f"Error executing query: {e}", exc_info=True)
        await session.rollback()
        raise


def execute_safe_query_sync(
    session: Session,
    query: str,
    params: Dict[str, Any],
    fetch: str = "all"
) -> Union[List[Dict], Dict, None]:
    """
    Execute a safe parameterized query (synchronous version)

    Args:
        session: SQLAlchemy session
        query: SQL query with :param placeholders
        params: Dictionary of parameter values
        fetch: "all", "one", or "none"

    Returns:
        Query results
    """
    try:
        stmt = text(query)
        result = session.execute(stmt, params)

        if fetch == "all":
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]
        elif fetch == "one":
            row = result.fetchone()
            return dict(row._mapping) if row else None
        else:  # "none"
            session.commit()
            return None

    except Exception as e:
        logger.error(f"Error executing query: {e}", exc_info=True)
        session.rollback()
        raise


# Convenience instance
secure_query = SecureQueryBuilder()
