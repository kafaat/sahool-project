interface StatsCardProps {
  title: string
  value: string
  icon: string
  trend?: string
  trendUp?: boolean | null
}

export default function StatsCard({ title, value, icon, trend, trendUp }: StatsCardProps) {
  return (
    <div className="card card-hover">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-gray-500 text-sm mb-1">{title}</p>
          <p className="text-2xl font-bold text-gray-800">{value}</p>
          {trend && (
            <p className={`text-sm mt-2 flex items-center gap-1 ${
              trendUp === true ? 'text-green-500' :
              trendUp === false ? 'text-red-500' :
              'text-gray-500'
            }`}>
              {trendUp === true && '↑'}
              {trendUp === false && '↓'}
              {trend}
            </p>
          )}
        </div>
        <span className="text-3xl opacity-80">{icon}</span>
      </div>
    </div>
  )
}
