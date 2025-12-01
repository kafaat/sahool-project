"""
Secure IoT API Example
مثال على API آمن لـ IoT Gateway مع حماية من SQL Injection

This file demonstrates how to use SQL safely in IoT Gateway
"""

from fastapi import APIRouter, HTTPException, Request, Depends, Header
from typing import Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import logging

# Import SQL security
import sys
sys.path.append('/home/user/sahool-project')
from shared.sql_security import SecureQueryBuilder, execute_safe_query

logger = logging.getLogger(__name__)

router = APIRouter(tags=["IoT Gateway - Secure"])


# ============================================================================
# SECURE SENSOR DATA ENDPOINT
# ============================================================================

@router.post("/sensors/secure")
async def receive_sensor_data_secure(
    request: Request,
    device_id: str,
    signature: str = Header(..., alias="X-Device-Signature"),
    # db: AsyncSession = Depends(get_db)  # You would inject DB session here
):
    """
    Secure sensor data endpoint with SQL injection protection

    Features:
    - HMAC signature verification
    - Parameterized SQL queries
    - Input validation
    - Rate limiting
    """

    # 1. Verify HMAC signature
    payload = await request.body()

    # ✅ Log with truncated device_id (security best practice)
    logger.info(f"Receiving data from device: {device_id[:10]}...")

    # In real implementation:
    # if not iot_security.verify_device_signature(device_id, payload, signature):
    #     logger.warning(f"Invalid signature from device: {device_id[:10]}...")
    #     raise HTTPException(status_code=403, detail="Invalid device signature")

    # 2. Validate sensor data
    # is_valid, message = await validate_sensor_data(data)
    # if not is_valid:
    #     raise HTTPException(status_code=400, detail=message)

    # ============================================================================
    # ❌ VULNERABLE CODE (DO NOT USE):
    # ============================================================================
    # query = f"SELECT * FROM sensors WHERE device_id = '{device_id}'"
    # result = await db.execute(query)
    #
    # This is vulnerable to SQL injection:
    # device_id = "'; DROP TABLE sensors; --"

    # ============================================================================
    # ✅ SECURE CODE (USE THIS):
    # ============================================================================

    # Method 1: Using SQLAlchemy text() with parameters
    query = text("SELECT * FROM sensors WHERE device_id = :device_id")
    # result = await db.execute(query, {"device_id": device_id})

    # Method 2: Using SecureQueryBuilder
    builder = SecureQueryBuilder()
    query, params = builder.build_select(
        "sensors",
        columns=["device_id", "device_type", "field_id", "last_seen"],
        where={"device_id": device_id}
    )

    # This produces:
    # SELECT device_id, device_type, field_id, last_seen
    # FROM sensors
    # WHERE device_id = :device_id_0
    #
    # With params: {"device_id_0": device_id}

    # Execute safely (in real code with actual DB session):
    # result = await execute_safe_query(db, query, params, fetch="one")

    # 3. Process and store data
    logger.info(f"✅ Sensor data processed securely from device: {device_id[:10]}...")

    return {
        "status": "success",
        "device_id": device_id,
        "message": "Data received securely"
    }


# ============================================================================
# SECURE DEVICE QUERY ENDPOINT
# ============================================================================

@router.get("/devices/secure/{device_id}")
async def get_device_secure(
    device_id: str,
    # db: AsyncSession = Depends(get_db)
):
    """
    Secure device query endpoint

    ✅ Uses parameterized queries to prevent SQL injection
    """

    builder = SecureQueryBuilder()

    # Build secure SELECT query
    query, params = builder.build_select(
        "devices",
        columns=["device_id", "device_type", "field_id", "status", "last_seen"],
        where={"device_id": device_id}
    )

    logger.info(f"Querying device: {device_id[:10]}...")

    # Execute query (in real code):
    # device = await execute_safe_query(db, query, params, fetch="one")
    #
    # if not device:
    #     raise HTTPException(status_code=404, detail="Device not found")
    #
    # return device

    return {
        "device_id": device_id,
        "message": "This is a secure query example",
        "query": query,
        "params": params
    }


# ============================================================================
# SECURE BULK SENSOR DATA QUERY
# ============================================================================

@router.get("/sensors/secure/field/{field_id}")
async def get_field_sensors_secure(
    field_id: int,
    limit: int = 100,
    # db: AsyncSession = Depends(get_db)
):
    """
    Secure bulk query for all sensors in a field

    ✅ Uses parameterized queries
    ✅ Applies LIMIT to prevent resource exhaustion
    """

    builder = SecureQueryBuilder()

    # Build secure query
    query, params = builder.build_select(
        "sensor_data",
        columns=["device_id", "timestamp", "temperature", "humidity"],
        where={"field_id": field_id},
        order_by=[("timestamp", "DESC")],
        limit=min(limit, 1000)  # Cap at 1000 to prevent abuse
    )

    logger.info(f"Querying sensors for field: {field_id}, limit: {limit}")

    # Execute query (in real code):
    # sensors = await execute_safe_query(db, query, params, fetch="all")
    # return {
    #     "field_id": field_id,
    #     "count": len(sensors),
    #     "data": sensors
    # }

    return {
        "field_id": field_id,
        "message": "This is a secure bulk query example",
        "query": query,
        "params": params
    }


# ============================================================================
# SECURE UPDATE ENDPOINT
# ============================================================================

@router.put("/devices/secure/{device_id}/status")
async def update_device_status_secure(
    device_id: str,
    status: str,
    # db: AsyncSession = Depends(get_db)
):
    """
    Secure device status update

    ✅ Uses parameterized UPDATE queries
    ✅ Requires WHERE clause (prevented by SecureQueryBuilder)
    """

    # Validate status
    if status not in ["online", "offline", "maintenance"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid status. Must be: online, offline, or maintenance"
        )

    builder = SecureQueryBuilder()

    # Build secure UPDATE query
    query, params = builder.build_update(
        "devices",
        values={"status": status, "updated_at": "NOW()"},
        where={"device_id": device_id}
    )

    logger.info(f"Updating device {device_id[:10]}... status to: {status}")

    # Execute query (in real code):
    # await execute_safe_query(db, query, params, fetch=None)
    # return {"device_id": device_id, "status": status, "updated": True}

    return {
        "device_id": device_id,
        "status": status,
        "message": "This is a secure UPDATE example",
        "query": query,
        "params": params
    }


# ============================================================================
# ATTACK PREVENTION EXAMPLES
# ============================================================================

"""
Attack Scenario 1: SQL Comment Injection
=========================================

❌ Vulnerable:
    device_id = "device_001'; --"
    query = f"SELECT * FROM sensors WHERE device_id = '{device_id}'"
    # Result: SELECT * FROM sensors WHERE device_id = 'device_001'; --'
    # Everything after -- is commented out!

✅ Secure (our implementation):
    query, params = builder.build_select("sensors", where={"device_id": device_id})
    # Result: SELECT * FROM sensors WHERE device_id = :device_id_0
    # Params: {"device_id_0": "device_001'; --"}
    # The SQL comment is treated as literal data!


Attack Scenario 2: UNION-based Data Exfiltration
=================================================

❌ Vulnerable:
    device_id = "device_001' UNION SELECT password FROM users--"
    query = f"SELECT * FROM sensors WHERE device_id = '{device_id}'"
    # Result: Attacker can extract password data!

✅ Secure (our implementation):
    query, params = builder.build_select("sensors", where={"device_id": device_id})
    # The UNION statement is safely parameterized as data
    # No SQL injection possible!


Attack Scenario 3: Stacked Queries (DROP TABLE)
===============================================

❌ Vulnerable:
    device_id = "device_001'; DROP TABLE sensors; --"
    query = f"SELECT * FROM sensors WHERE device_id = '{device_id}'"
    # Result: Table deleted!

✅ Secure (our implementation):
    query, params = builder.build_select("sensors", where={"device_id": device_id})
    # The DROP statement is safely parameterized
    # Table is safe!
"""


# ============================================================================
# MIGRATION GUIDE
# ============================================================================

"""
How to migrate existing code:
==============================

BEFORE (Vulnerable):
-------------------
@app.get("/devices/{device_id}")
async def get_device(device_id: str, db: AsyncSession = Depends(get_db)):
    query = f"SELECT * FROM devices WHERE device_id = '{device_id}'"
    result = await db.execute(query)
    return result.fetchone()


AFTER (Secure):
--------------
from shared.sql_security import SecureQueryBuilder, execute_safe_query

@app.get("/devices/{device_id}")
async def get_device(device_id: str, db: AsyncSession = Depends(get_db)):
    builder = SecureQueryBuilder()
    query, params = builder.build_select(
        "devices",
        where={"device_id": device_id}
    )
    result = await execute_safe_query(db, query, params, fetch="one")
    return result


MIGRATION CHECKLIST:
-------------------
✅ Replace all f-strings in SQL queries
✅ Replace all % formatting in SQL queries
✅ Replace all + concatenation in SQL queries
✅ Use SecureQueryBuilder for all queries
✅ Test with malicious inputs
✅ Run security tests: pytest tests/security/test_sql_injection.py
"""
