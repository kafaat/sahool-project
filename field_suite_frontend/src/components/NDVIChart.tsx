import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'

interface NDVIChartProps {
  data?: {
    excellent: number
    good: number
    moderate: number
    poor: number
  }
}

const COLORS = ['#10b981', '#34d399', '#fbbf24', '#ef4444']

export default function NDVIChart({ data }: NDVIChartProps) {
  const chartData = [
    { name: 'ممتاز', value: data?.excellent || 35, color: COLORS[0] },
    { name: 'جيد', value: data?.good || 35, color: COLORS[1] },
    { name: 'متوسط', value: data?.moderate || 20, color: COLORS[2] },
    { name: 'يحتاج متابعة', value: data?.poor || 10, color: COLORS[3] },
  ]

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={90}
            paddingAngle={2}
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number) => [`${value}%`, '']}
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              direction: 'rtl',
            }}
          />
          <Legend
            layout="vertical"
            align="left"
            verticalAlign="middle"
            formatter={(value) => <span className="text-gray-600 text-sm">{value}</span>}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
