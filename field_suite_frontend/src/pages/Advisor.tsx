import { useState } from 'react'

const recommendations = [
  {
    id: 1,
    priority: 'high',
    title: 'تحذير: انخفاض مؤشر NDVI',
    description: 'الحقل رقم 15 في تعز يظهر انخفاضاً في مؤشر صحة النبات',
    actions: ['فحص التربة', 'زيادة الري', 'تفقد الآفات'],
  },
  {
    id: 2,
    priority: 'medium',
    title: 'موعد التسميد',
    description: 'حقول القمح في صنعاء تحتاج للتسميد هذا الأسبوع',
    actions: ['إضافة سماد NPK', 'مراقبة النمو'],
  },
  {
    id: 3,
    priority: 'low',
    title: 'موسم الحصاد قريب',
    description: 'محصول الشعير في ذمار جاهز للحصاد خلال أسبوعين',
    actions: ['تجهيز المعدات', 'ترتيب التخزين'],
  },
]

const chatHistory = [
  { role: 'user', message: 'ما هو أفضل وقت لري القمح؟' },
  { role: 'assistant', message: 'أفضل وقت لري القمح هو في الصباح الباكر (5-7 صباحاً) أو المساء (5-7 مساءً) لتقليل التبخر. يُنصح بالري كل 3-4 أيام في فصل الشتاء.' },
]

export default function Advisor() {
  const [message, setMessage] = useState('')
  const [chat, setChat] = useState(chatHistory)

  const handleSend = () => {
    if (!message.trim()) return

    setChat([...chat, { role: 'user', message }])

    // Simulate AI response
    setTimeout(() => {
      setChat(prev => [...prev, {
        role: 'assistant',
        message: 'شكراً لسؤالك. سأقوم بتحليل البيانات المتوفرة وتقديم التوصية المناسبة. يُرجى الانتظار...'
      }])
    }, 1000)

    setMessage('')
  }

  const getPriorityStyles = (priority: string) => {
    switch (priority) {
      case 'high':
        return { bg: 'bg-red-50', border: 'border-red-200', icon: '🔴', text: 'text-red-700' }
      case 'medium':
        return { bg: 'bg-yellow-50', border: 'border-yellow-200', icon: '🟡', text: 'text-yellow-700' }
      case 'low':
        return { bg: 'bg-green-50', border: 'border-green-200', icon: '🟢', text: 'text-green-700' }
      default:
        return { bg: 'bg-gray-50', border: 'border-gray-200', icon: '⚪', text: 'text-gray-700' }
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">المستشار الزراعي الذكي</h1>
          <p className="text-gray-500">توصيات ذكية مبنية على تحليل البيانات والذكاء الاصطناعي</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recommendations */}
        <div className="space-y-4">
          <h3 className="text-lg font-bold text-gray-800">التوصيات النشطة</h3>

          {recommendations.map((rec) => {
            const styles = getPriorityStyles(rec.priority)
            return (
              <div
                key={rec.id}
                className={`card ${styles.bg} border ${styles.border} card-hover`}
              >
                <div className="flex items-start gap-4">
                  <span className="text-2xl">{styles.icon}</span>
                  <div className="flex-1">
                    <h4 className={`font-bold ${styles.text}`}>{rec.title}</h4>
                    <p className="text-sm text-gray-600 mt-1">{rec.description}</p>
                    <div className="flex flex-wrap gap-2 mt-3">
                      {rec.actions.map((action, index) => (
                        <span
                          key={index}
                          className="px-3 py-1 bg-white rounded-full text-sm text-gray-600 border border-gray-200"
                        >
                          {action}
                        </span>
                      ))}
                    </div>
                  </div>
                  <button className="btn btn-secondary text-sm">
                    تنفيذ
                  </button>
                </div>
              </div>
            )
          })}
        </div>

        {/* Chat Interface */}
        <div className="card flex flex-col h-[600px]">
          <div className="flex items-center gap-3 pb-4 border-b border-gray-100">
            <span className="text-3xl">🤖</span>
            <div>
              <h3 className="font-bold text-gray-800">المستشار الذكي</h3>
              <p className="text-sm text-green-500">متصل الآن</p>
            </div>
          </div>

          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto py-4 space-y-4">
            {chat.map((msg, index) => (
              <div
                key={index}
                className={`flex ${msg.role === 'user' ? 'justify-start' : 'justify-end'}`}
              >
                <div
                  className={`max-w-[80%] p-4 rounded-2xl ${
                    msg.role === 'user'
                      ? 'bg-emerald-500 text-white rounded-br-none'
                      : 'bg-gray-100 text-gray-800 rounded-bl-none'
                  }`}
                >
                  {msg.message}
                </div>
              </div>
            ))}
          </div>

          {/* Chat Input */}
          <div className="pt-4 border-t border-gray-100">
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="اكتب سؤالك هنا..."
                className="flex-1 px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              />
              <button
                onClick={handleSend}
                className="btn btn-primary px-6"
              >
                إرسال 📤
              </button>
            </div>
            <div className="flex gap-2 mt-3">
              <button className="text-sm px-3 py-1 bg-gray-100 rounded-full hover:bg-gray-200">
                ما هو أفضل وقت للري؟
              </button>
              <button className="text-sm px-3 py-1 bg-gray-100 rounded-full hover:bg-gray-200">
                كيف أحسن التربة؟
              </button>
              <button className="text-sm px-3 py-1 bg-gray-100 rounded-full hover:bg-gray-200">
                متى أبدأ الحصاد؟
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
