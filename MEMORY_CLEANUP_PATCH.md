## 🔧 Quick Patch for Existing main.py Files

هذا patch سريع لإضافة cleanup للملفات الموجودة بدون إعادة كتابة كاملة.

### الطريقة 1: Patch البسيط (5 دقائق)

أضف هذا الكود في نهاية ملف `main.py`:

```python
import gc

@app.on_event("shutdown")  # للنسخ القديمة من FastAPI
async def cleanup_on_shutdown():
    """Clean up resources on shutdown"""
    global crop_predictor, disease_detector, soil_analyzer, weather_forecaster

    # Clean up ML models
    for model in [crop_predictor, disease_detector, soil_analyzer, weather_forecaster]:
        if model is not None:
            # Delete model weights
            if hasattr(model, 'model'):
                del model.model

            # Clear caches
            if hasattr(model, '_cache'):
                model._cache.clear()

            # Delete model object
            del model

    # Force garbage collection
    gc.collect()

    logger.info("✅ Resources cleaned up")
```

### الطريقة 2: Patch باستخدام lifespan (موصى به)

إذا كنت تستخدم `lifespan` context manager، عدّل السطور 66-69:

```python
# قبل:
    yield

    # Shutdown
    logger.info("🛑 Shutting down ML Engine Service...")

# بعد:
    yield

    # Shutdown
    logger.info("🛑 Shutting down ML Engine Service...")

    # ✅ CLEANUP ADDED
    logger.info("🧹 Cleaning up resources...")

    # Clean models
    if crop_predictor:
        if hasattr(crop_predictor, 'model'):
            del crop_predictor.model
        del crop_predictor

    if disease_detector:
        if hasattr(disease_detector, 'model'):
            del disease_detector.model
        del disease_detector

    if soil_analyzer:
        if hasattr(soil_analyzer, 'model'):
            del soil_analyzer.model
        del soil_analyzer

    if weather_forecaster:
        if hasattr(weather_forecaster, 'model'):
            del weather_forecaster.model
        del weather_forecaster

    # Force GC
    import gc
    collected = gc.collect()
    logger.info(f"✅ Cleanup complete, GC collected {collected} objects")
```

### الطريقة 3: استخدام cleanup_helpers (الأسهل)

```python
# في أول الملف
from shared.cleanup_helpers import cleanup_ml_models_dict, force_garbage_collection, log_memory_usage

# في lifespan، بعد yield:
    yield

    # Shutdown
    logger.info("🛑 Shutting down...")

    # ✅ استخدام helper
    models = {
        "crop_predictor": crop_predictor,
        "disease_detector": disease_detector,
        "soil_analyzer": soil_analyzer,
        "weather_forecaster": weather_forecaster
    }

    cleanup_ml_models_dict(models)
    log_memory_usage("after cleanup")
```

### خدمات أخرى تحتاج cleanup:

#### Agent-AI (multi-repo/agent-ai/app/main.py):
```python
# بعد yield:
    # Cleanup LLM instances
    if agent_instance:
        del agent_instance.llm
        del agent_instance
    gc.collect()
```

#### IoT Gateway (iot-gateway/app/main.py):
```python
# بعد yield:
    # Cleanup connections
    if mqtt_client:
        mqtt_client.disconnect()
        del mqtt_client
    if redis_client:
        redis_client.close()
        del redis_client
    gc.collect()
```

#### Imagery Core (multi-repo/imagery-core/app/main.py):
```python
# بعد yield:
    # Cleanup image processing resources
    if image_processor:
        if hasattr(image_processor, '_cache'):
            image_processor._cache.clear()
        del image_processor
    gc.collect()
```

### ✅ كيف تختبر أن الpatch يعمل:

```python
# أضف هذا endpoint للاختبار:
@app.get("/memory/test")
async def test_memory():
    import gc
    import psutil
    import os

    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / 1024 / 1024

    # Force GC
    collected = gc.collect()

    mem_after = process.memory_info().rss / 1024 / 1024
    freed = mem_before - mem_after

    return {
        "memory_before_mb": mem_before,
        "memory_after_mb": mem_after,
        "freed_mb": freed,
        "objects_collected": collected
    }
```

### 🚨 علامات تدل على memory leak:

1. **Memory يزيد باستمرار:**
   ```bash
   # راقب الذاكرة كل 5 ثواني
   watch -n 5 'ps aux | grep python | grep main.py'
   ```

2. **استخدام htop:**
   ```bash
   htop -p $(pgrep -f "python.*main.py")
   ```

3. **استخدام memory_profiler:**
   ```bash
   pip install memory_profiler
   python -m memory_profiler main.py
   ```

### الأولويات:

| الخدمة | الأولوية | السبب |
|--------|---------|--------|
| **ML Engine** | 🔴 حرجة | يحمّل نماذج ML كبيرة (100-500MB) |
| **Agent-AI** | 🔴 حرجة | يحمّل LLM (GPT/Claude) |
| **Imagery Core** | 🟡 مهمة | معالجة صور (memory intensive) |
| **IoT Gateway** | 🟡 مهمة | اتصالات كثيرة (connections) |
| **Geo-Core** | 🟢 عادية | بيانات جغرافية (manageable) |
