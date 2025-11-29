# Monitoring & Alerting & Dashboards - Sahool v280

## Prometheus / ServiceMonitor

- تم إنشاء ServiceMonitor في `templates/servicemonitor.yaml` (من v4).
- يتم تفعيله عبر:

```yaml
monitoring:
  enabled: true
  prometheus:
    serviceMonitor:
      enabled: true
      namespace: "monitoring"
```

## Alerts (PrometheusRule)

- تم إضافة `templates/prometheusrule.yaml`:
  - تنبيهات:
    - SahoolGatewayDown
    - SahoolImageryDown
    - SahoolWeatherDown
    - SahoolHighCPU (استهلاك عالي على gateway)

> تأكد أن Prometheus Operator يلتقط هذا الـ PrometheusRule في نفس الـ namespace.

## Grafana Dashboards

- تم إضافة `templates/grafana-dashboard-overview.yaml`:
  - ينشئ ConfigMap باسم `sahool-grafana-dashboard-overview`
  - يحتوي لوحة `Sahool Platform - Overview`.

يفعّل عبر:

```yaml
grafana:
  dashboards:
    enabled: true
    namespace: "monitoring"
    label: "grafana_dashboard"
```

وتحتاج أن يكون لديك Grafana sidecar يلتقط ConfigMaps بهذه الـ label.

بهذه الإضافات، المنصة أصبحت ليست فقط جاهزة للتشغيل، بل أيضًا للمراقبة والتنبيه والعرض على Grafana.
