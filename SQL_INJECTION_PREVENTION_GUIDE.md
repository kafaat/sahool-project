# 🔒 دليل منع SQL Injection - SQL Injection Prevention Guide

## ⚠️ خطورة SQL Injection

**SQL Injection** هي من أخطر الثغرات الأمنية (OWASP Top 10 #1)!

### التأثير المحتمل:
- 💥 **سرقة البيانات** - كل قاعدة البيانات!
- 💥 **حذف البيانات** - DELETE FROM users
- 💥 **تعديل البيانات** - UPDATE passwords
- 💥 **التحكم الكامل** - Execute commands
- 💥 **التصعيد** - Access to OS

### مثال حقيقي:

```python
# ❌ VULNERABLE CODE - خطر جداً!
device_id = request.query_params.get("device_id")
query = f"SELECT * FROM sensors WHERE device_id = '{device_id}'"
result = await db.execute(query)
```

**ماذا لو أرسل المهاجم:**
```
device_id = "sensor_001' OR '1'='1"
```

**Query النهائي:**
```sql
SELECT * FROM sensors WHERE device_id = 'sensor_001' OR '1'='1'
```
**النتيجة:** ✅ Returns ALL sensors! (Bypassed authentication!)

**أسوأ:**
```
device_id = "sensor_001'; DROP TABLE sensors; --"
```

**Query النهائي:**
```sql
SELECT * FROM sensors WHERE device_id = 'sensor_001';
DROP TABLE sensors;
--'
```
**النتيجة:** 💥 جدول الsensors محذوف بالكامل!

---

## ✅ الحل الصحيح: Parameterized Queries

### قبل (غير آمن):

```python
# ❌ خطر! String formatting
device_id = "sensor_001"
query = f"SELECT * FROM sensors WHERE device_id = '{device_id}'"
result = await db.execute(query)

# ❌ خطر! String concatenation
query = "SELECT * FROM sensors WHERE device_id = '" + device_id + "'"
result = await db.execute(query)

# ❌ خطر! % formatting
query = "SELECT * FROM sensors WHERE device_id = '%s'" % device_id
result = await db.execute(query)
```

### بعد (آمن):

```python
# ✅ آمن! Parameterized query
from sqlalchemy import text

device_id = "sensor_001"
query = text("SELECT * FROM sensors WHERE device_id = :device_id")
result = await db.execute(query, {"device_id": device_id})
```

**لماذا هذا آمن؟**
- القيم تُعامل كـ **data** وليس **code**
- لا يمكن تنفيذ SQL commands في القيمة
- SQLAlchemy يقوم بـ escape تلقائياً

---

## 🛡️ أمثلة شاملة

### 1. SELECT Query

```python
# ❌ خطر
def get_sensors_unsafe(device_type: str):
    query = f"SELECT * FROM sensors WHERE type = '{device_type}'"
    return db.execute(query)

# ✅ آمن - الطريقة 1: text() مع parameters
def get_sensors_safe_v1(device_type: str):
    from sqlalchemy import text

    query = text("SELECT * FROM sensors WHERE type = :type")
    return db.execute(query, {"type": device_type})

# ✅ آمن - الطريقة 2: استخدام secure_query builder
def get_sensors_safe_v2(device_type: str):
    from shared.sql_security import secure_query, execute_safe_query

    query, params = secure_query.build_select(
        table="sensors",
        where={"type": device_type}
    )
    return execute_safe_query(db, query, params)
```

### 2. INSERT Query

```python
# ❌ خطر
def add_sensor_unsafe(device_id: str, value: float):
    query = f"INSERT INTO sensors (device_id, value) VALUES ('{device_id}', {value})"
    db.execute(query)

# ✅ آمن
def add_sensor_safe(device_id: str, value: float):
    from sqlalchemy import text

    query = text("""
        INSERT INTO sensors (device_id, value, created_at)
        VALUES (:device_id, :value, NOW())
    """)
    db.execute(query, {
        "device_id": device_id,
        "value": value
    })

# ✅ آمن - باستخدام builder
def add_sensor_safe_builder(device_id: str, value: float):
    from shared.sql_security import secure_query

    query, params = secure_query.build_insert(
        table="sensors",
        data={"device_id": device_id, "value": value},
        returning=["id"]
    )
    return db.execute(query, params)
```

### 3. UPDATE Query

```python
# ❌ خطر جداً! (يمكن تحديث كل الصفوف)
def update_sensor_unsafe(device_id: str, active: bool):
    query = f"UPDATE sensors SET active = {active} WHERE device_id = '{device_id}'"
    db.execute(query)

# ✅ آمن
def update_sensor_safe(device_id: str, active: bool):
    from sqlalchemy import text

    query = text("""
        UPDATE sensors
        SET active = :active, updated_at = NOW()
        WHERE device_id = :device_id
    """)
    db.execute(query, {
        "device_id": device_id,
        "active": active
    })

# ✅ آمن - باستخدام builder (يجبر على WHERE clause)
def update_sensor_safe_builder(device_id: str, active: bool):
    from shared.sql_security import secure_query

    query, params = secure_query.build_update(
        table="sensors",
        data={"active": active},
        where={"device_id": device_id}  # مطلوب!
    )
    return db.execute(query, params)
```

### 4. DELETE Query

```python
# ❌ خطر جداً! (يمكن حذف كل شيء)
def delete_sensor_unsafe(device_id: str):
    query = f"DELETE FROM sensors WHERE device_id = '{device_id}'"
    db.execute(query)

# ✅ آمن
def delete_sensor_safe(device_id: str):
    from sqlalchemy import text

    query = text("DELETE FROM sensors WHERE device_id = :device_id")
    db.execute(query, {"device_id": device_id})

# ✅ آمن - باستخدام builder (يجبر على WHERE clause)
def delete_sensor_safe_builder(device_id: str):
    from shared.sql_security import secure_query

    query, params = secure_query.build_delete(
        table="sensors",
        where={"device_id": device_id}  # مطلوب!
    )
    return db.execute(query, params)
```

### 5. Complex WHERE Conditions

```python
# ❌ خطر
def get_sensors_complex_unsafe(type: str, min_value: float, max_value: float):
    query = f"""
        SELECT * FROM sensors
        WHERE type = '{type}'
        AND value >= {min_value}
        AND value <= {max_value}
    """
    return db.execute(query)

# ✅ آمن
def get_sensors_complex_safe(type: str, min_value: float, max_value: float):
    from sqlalchemy import text

    query = text("""
        SELECT * FROM sensors
        WHERE type = :type
        AND value >= :min_value
        AND value <= :max_value
    """)
    return db.execute(query, {
        "type": type,
        "min_value": min_value,
        "max_value": max_value
    })
```

### 6. Dynamic Column Names (حذر!)

```python
# ❌ خطر - dynamic columns من user input
def get_by_column_unsafe(column: str, value: str):
    # المهاجم يمكنه إرسال: column = "id; DROP TABLE sensors; --"
    query = f"SELECT * FROM sensors WHERE {column} = '{value}'"
    return db.execute(query)

# ✅ آمن - whitelist approach
def get_by_column_safe(column: str, value: str):
    # Only allow specific columns
    ALLOWED_COLUMNS = ["device_id", "type", "status"]

    if column not in ALLOWED_COLUMNS:
        raise ValueError(f"Invalid column: {column}")

    from sqlalchemy import text

    # Column name is validated, value is parameterized
    query = text(f"SELECT * FROM sensors WHERE {column} = :value")
    return db.execute(query, {"value": value})
```

---

## 🚀 استخدام shared/sql_security.py

### تثبيت:

```python
from shared.sql_security import (
    secure_query,
    execute_safe_query,
    SQLInjectionError
)
```

### أمثلة الاستخدام:

#### SELECT:

```python
# بناء query آمن
query, params = secure_query.build_select(
    table="sensors",
    columns=["id", "device_id", "value", "timestamp"],
    where={
        "device_id": "sensor_001",
        "active": True
    },
    order_by="timestamp DESC",
    limit=10
)

# تنفيذ
result = await execute_safe_query(db_session, query, params, fetch="all")
```

#### INSERT:

```python
query, params = secure_query.build_insert(
    table="sensors",
    data={
        "device_id": "sensor_002",
        "value": 25.3,
        "unit": "celsius"
    },
    returning=["id", "created_at"]
)

result = await execute_safe_query(db_session, query, params, fetch="one")
```

#### UPDATE:

```python
query, params = secure_query.build_update(
    table="sensors",
    data={"active": False, "status": "offline"},
    where={"device_id": "sensor_001"}
)

await execute_safe_query(db_session, query, params, fetch="none")
```

#### DELETE:

```python
query, params = secure_query.build_delete(
    table="sensors",
    where={"device_id": "sensor_001", "active": False}
)

await execute_safe_query(db_session, query, params, fetch="none")
```

---

## 🧪 كيف تختبر للثغرات؟

### 1. Manual Testing

```python
# جرب هذه القيم كـ input:
test_payloads = [
    "' OR '1'='1",                    # Always true
    "'; DROP TABLE sensors; --",     # Drop table
    "' UNION SELECT * FROM users--", # Union injection
    "admin'--",                       # Comment out password check
    "' OR 1=1--",                     # Bypass
]

for payload in test_payloads:
    try:
        result = get_sensor(payload)  # Your function
        print(f"⚠️ VULNERABLE to: {payload}")
    except Exception as e:
        print(f"✅ Protected against: {payload}")
```

### 2. Automated Scanner

```bash
# استخدام sqlmap (أداة شهيرة)
sqlmap -u "http://localhost:8000/api/sensors?device_id=test" --batch
```

### 3. Unit Tests

```python
import pytest
from shared.sql_security import SQLInjectionError, secure_query

def test_sql_injection_prevention():
    """Test that SQL injection is prevented"""

    # Test dangerous patterns
    with pytest.raises(SQLInjectionError):
        secure_query.validate_input("'; DROP TABLE sensors; --")

    with pytest.raises(SQLInjectionError):
        secure_query.validate_input("' OR '1'='1")

    # Test safe input
    secure_query.validate_input("sensor_001")  # Should not raise

def test_table_name_validation():
    """Test that invalid table names are rejected"""

    with pytest.raises(SQLInjectionError):
        secure_query.build_select(table="sensors; DROP TABLE users;")

    with pytest.raises(SQLInjectionError):
        secure_query.build_select(table="sensors--")

def test_column_name_validation():
    """Test that invalid column names are rejected"""

    with pytest.raises(SQLInjectionError):
        secure_query.build_select(
            table="sensors",
            columns=["id; DROP TABLE sensors"]
        )
```

---

## 🔍 كيف تفحص الكود الموجود؟

### Automated Scanner Script:

```python
# tools/scan_sql_injection.py
import re
import os

def scan_file(filepath):
    """Scan file for potential SQL injection vulnerabilities"""
    vulnerabilities = []

    with open(filepath, 'r') as f:
        content = f.read()
        lines = content.split('\n')

    # Patterns that indicate SQL injection risk
    dangerous_patterns = [
        (r'f"SELECT.*{', 'f-string in SQL query'),
        (r"f'SELECT.*{", 'f-string in SQL query'),
        (r'%\s*"SELECT', '% formatting in SQL query'),
        (r'\+\s*"SELECT', 'String concatenation in SQL query'),
        (r'\.format\(.*SELECT', '.format() in SQL query'),
    ]

    for i, line in enumerate(lines, 1):
        for pattern, description in dangerous_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                vulnerabilities.append({
                    'file': filepath,
                    'line': i,
                    'code': line.strip(),
                    'issue': description
                })

    return vulnerabilities

# Scan all Python files
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            vulns = scan_file(filepath)

            if vulns:
                print(f"🚨 Found issues in {filepath}:")
                for v in vulns:
                    print(f"  Line {v['line']}: {v['issue']}")
                    print(f"    Code: {v['code']}")
```

---

## 📋 Checklist للمطورين

عند كتابة أي SQL query:

- [ ] ✅ استخدمت `text()` مع `:parameter` syntax؟
- [ ] ✅ لا يوجد f-strings في SQL queries؟
- [ ] ✅ لا يوجد string concatenation (+) في SQL؟
- [ ] ✅ لا يوجد % formatting في SQL؟
- [ ] ✅ الcolumn names من whitelist وليس user input؟
- [ ] ✅ UPDATE/DELETE لديها WHERE clause؟
- [ ] ✅ اختبرت ضد SQL injection payloads؟

---

## 🚨 هجمات SQL Injection الشائعة

### 1. Authentication Bypass

```sql
-- Login form
SELECT * FROM users WHERE username = 'admin' AND password = 'xxx'

-- Attacker input:
-- username = "admin'--"
-- password = "anything"

-- Final query:
SELECT * FROM users WHERE username = 'admin'--' AND password = 'xxx'
-- Result: Logged in without password!
```

### 2. Data Extraction (Union-based)

```sql
-- Original query
SELECT name, price FROM products WHERE id = 1

-- Attacker input: id = "1 UNION SELECT username, password FROM users--"

-- Final query:
SELECT name, price FROM products WHERE id = 1
UNION SELECT username, password FROM users--
-- Result: Extracted all usernames and passwords!
```

### 3. Blind SQL Injection

```sql
-- Boolean-based
SELECT * FROM products WHERE id = 1 AND (SELECT COUNT(*) FROM users) > 0

-- Time-based
SELECT * FROM products WHERE id = 1 AND IF(1=1, SLEEP(5), 0)
-- If query takes 5 seconds, injection successful!
```

### 4. Second-Order SQL Injection

```sql
-- Step 1: Insert malicious data
INSERT INTO users (username) VALUES ("admin'--")

-- Step 2: Data is used in another query (later)
SELECT * FROM logs WHERE username = 'admin'--'
-- Injection triggers here!
```

---

## ✅ أفضل الممارسات (Best Practices)

### 1. دائماً استخدم Parameterized Queries

```python
# ✅ جيد
query = text("SELECT * FROM sensors WHERE id = :id")
db.execute(query, {"id": sensor_id})
```

### 2. استخدم ORM عندما ممكن

```python
# ✅ SQLAlchemy ORM (آمن تلقائياً)
from sqlalchemy.orm import Session
from models import Sensor

def get_sensor(db: Session, sensor_id: int):
    return db.query(Sensor).filter(Sensor.id == sensor_id).first()
```

### 3. Whitelist للColumn/Table Names

```python
ALLOWED_TABLES = ["sensors", "devices", "fields"]
ALLOWED_COLUMNS = ["id", "device_id", "value", "timestamp"]

if table not in ALLOWED_TABLES:
    raise ValueError("Invalid table")
```

### 4. Input Validation

```python
from pydantic import BaseModel, Field, validator

class SensorQuery(BaseModel):
    device_id: str = Field(..., min_length=3, max_length=50)

    @validator('device_id')
    def validate_device_id(cls, v):
        # Only allow alphanumeric and underscore
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError("Invalid device_id format")
        return v
```

### 5. Least Privilege

```sql
-- Database user should have minimal permissions
-- Don't use 'root' or 'admin' user in application
CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'password';
GRANT SELECT, INSERT, UPDATE ON app_db.* TO 'app_user'@'localhost';
-- No DELETE, DROP, ALTER permissions!
```

### 6. Logging و Monitoring

```python
import logging

logger.info(f"Executing query with params: {params}")

# Monitor for suspicious patterns
if re.search(r"(DROP|DELETE|UNION)", user_input, re.IGNORECASE):
    logger.warning(f"Suspicious input detected: {user_input}")
    # Alert security team
```

---

## 📊 ملخص

| الطريقة | آمنة؟ | مثال |
|---------|-------|------|
| f-string | ❌ خطر | `f"SELECT * FROM t WHERE id = {id}"` |
| + concatenation | ❌ خطر | `"SELECT * FROM t WHERE id = " + id` |
| % formatting | ❌ خطر | `"SELECT * FROM t WHERE id = %s" % id` |
| .format() | ❌ خطر | `"SELECT * FROM t WHERE id = {}".format(id)` |
| **text() + params** | ✅ آمن | `text("SELECT * FROM t WHERE id = :id")` |
| **ORM** | ✅ آمن | `db.query(T).filter(T.id == id)` |
| **secure_query** | ✅ آمن | `secure_query.build_select(...)` |

---

## 🔗 موارد إضافية

- **OWASP SQL Injection:** https://owasp.org/www-community/attacks/SQL_Injection
- **SQLAlchemy Docs:** https://docs.sqlalchemy.org/
- **Python DB-API:** https://peps.python.org/pep-0249/
- **sqlmap Tool:** https://sqlmap.org/

---

**تذكر:** SQL Injection من أخطر الثغرات!
**الحل:** Parameterized Queries دائماً ✅

---

**تاريخ الإنشاء:** 2025-12-01
**الإصدار:** v3.2.6
**الحالة:** Production Ready - Security Critical ✅
