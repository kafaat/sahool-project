interface AlertsListProps {
  alerts?: {
    high: number
    medium: number
    low: number
  }
}

export default function AlertsList({ alerts }: AlertsListProps) {
  const alertItems = [
    {
      level: 'high',
      count: alerts?.high || 5,
      label: 'عالية الأهمية',
      color: 'bg-red-100 text-red-700 border-red-200',
      icon: '🔴',
    },
    {
      level: 'medium',
      count: alerts?.medium || 12,
      label: 'متوسطة',
      color: 'bg-yellow-100 text-yellow-700 border-yellow-200',
      icon: '🟡',
    },
    {
      level: 'low',
      count: alerts?.low || 23,
      label: 'منخفضة',
      color: 'bg-green-100 text-green-700 border-green-200',
      icon: '🟢',
    },
  ]

  return (
    <div className="space-y-3">
      {alertItems.map((alert) => (
        <div
          key={alert.level}
          className={`flex items-center justify-between p-4 rounded-lg border ${alert.color}`}
        >
          <div className="flex items-center gap-3">
            <span className="text-xl">{alert.icon}</span>
            <span className="font-medium">{alert.label}</span>
          </div>
          <span className="text-2xl font-bold">{alert.count}</span>
        </div>
      ))}

      <button className="w-full mt-4 btn btn-secondary">
        عرض جميع التنبيهات ←
      </button>
    </div>
  )
}
