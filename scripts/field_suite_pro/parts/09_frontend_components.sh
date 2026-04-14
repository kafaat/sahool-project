#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# Part 9: Frontend Components
# ═══════════════════════════════════════════════════════════════════════════════

log_info "إنشاء مكونات الواجهة الأمامية..."

# ─────────────────────────────────────────────────────────────────────────────
# App Component
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/web/src/App.tsx" << 'EOF'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Suspense, lazy } from 'react';
import { useAuthStore } from '@/stores/authStore';
import Layout from '@/components/layout/Layout';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

// Lazy load pages
const Login = lazy(() => import('@/pages/Login'));
const Dashboard = lazy(() => import('@/pages/Dashboard'));
const Fields = lazy(() => import('@/pages/Fields'));
const FieldDetails = lazy(() => import('@/pages/FieldDetails'));
const Advisor = lazy(() => import('@/pages/Advisor'));
const Settings = lazy(() => import('@/pages/Settings'));

// Protected route wrapper
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingSpinner fullScreen />}>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="fields" element={<Fields />} />
            <Route path="fields/:id" element={<FieldDetails />} />
            <Route path="advisor" element={<Advisor />} />
            <Route path="settings" element={<Settings />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Layout Component
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/web/src/components/layout/Layout.tsx" << 'EOF'
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

export default function Layout() {
  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
EOF

cat > "$PROJECT_NAME/web/src/components/layout/Sidebar.tsx" << 'EOF'
import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  LayoutDashboard,
  Map,
  BarChart3,
  MessageSquare,
  Settings,
  Leaf
} from 'lucide-react';
import clsx from 'clsx';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'nav.dashboard' },
  { to: '/fields', icon: Map, label: 'nav.fields' },
  { to: '/advisor', icon: MessageSquare, label: 'nav.advisor' },
  { to: '/settings', icon: Settings, label: 'nav.settings' },
];

export default function Sidebar() {
  const { t } = useTranslation();

  return (
    <aside className="w-64 bg-white border-l border-gray-200 flex flex-col">
      {/* Logo */}
      <div className="h-16 flex items-center justify-center border-b border-gray-200">
        <Leaf className="w-8 h-8 text-primary-600" />
        <span className="mr-2 text-xl font-bold text-gray-900">Field Suite</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              clsx(
                'flex items-center px-4 py-3 rounded-lg transition-colors',
                isActive
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-gray-600 hover:bg-gray-100'
              )
            }
          >
            <item.icon className="w-5 h-5 ml-3" />
            {t(item.label)}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        <p className="text-xs text-gray-500 text-center">
          Field Suite Pro v2.0
        </p>
      </div>
    </aside>
  );
}
EOF

cat > "$PROJECT_NAME/web/src/components/layout/Header.tsx" << 'EOF'
import { useTranslation } from 'react-i18next';
import { Bell, User, LogOut, Globe } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';

export default function Header() {
  const { t, i18n } = useTranslation();
  const { user, logout } = useAuthStore();

  const toggleLanguage = () => {
    const newLang = i18n.language === 'ar' ? 'en' : 'ar';
    i18n.changeLanguage(newLang);
    document.documentElement.dir = newLang === 'ar' ? 'rtl' : 'ltr';
  };

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      {/* Search */}
      <div className="flex-1 max-w-md">
        <input
          type="text"
          placeholder={t('common.search')}
          className="input"
        />
      </div>

      {/* Actions */}
      <div className="flex items-center gap-4">
        {/* Language Toggle */}
        <button
          onClick={toggleLanguage}
          className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
          title={i18n.language === 'ar' ? 'English' : 'العربية'}
        >
          <Globe className="w-5 h-5" />
        </button>

        {/* Notifications */}
        <button className="relative p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
        </button>

        {/* User Menu */}
        <div className="flex items-center gap-3 pr-4 border-r border-gray-200">
          <div className="text-left">
            <p className="text-sm font-medium text-gray-900">{user?.fullName}</p>
            <p className="text-xs text-gray-500">{user?.email}</p>
          </div>
          <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
            <User className="w-5 h-5 text-primary-600" />
          </div>
        </div>

        {/* Logout */}
        <button
          onClick={logout}
          className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg"
          title={t('auth.logout')}
        >
          <LogOut className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
}
EOF

# ─────────────────────────────────────────────────────────────────────────────
# UI Components
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/web/src/components/ui/LoadingSpinner.tsx" << 'EOF'
import clsx from 'clsx';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  fullScreen?: boolean;
}

export default function LoadingSpinner({ size = 'md', fullScreen }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  const spinner = (
    <div className={clsx('spinner', sizeClasses[size])} />
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-white">
        {spinner}
      </div>
    );
  }

  return spinner;
}
EOF

cat > "$PROJECT_NAME/web/src/components/ui/Card.tsx" << 'EOF'
import clsx from 'clsx';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: boolean;
}

export default function Card({ children, className, padding = true }: CardProps) {
  return (
    <div className={clsx('card', padding && 'p-6', className)}>
      {children}
    </div>
  );
}

export function CardHeader({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={clsx('border-b border-gray-100 pb-4 mb-4', className)}>
      {children}
    </div>
  );
}

export function CardTitle({ children }: { children: React.ReactNode }) {
  return <h3 className="text-lg font-semibold text-gray-900">{children}</h3>;
}
EOF

cat > "$PROJECT_NAME/web/src/components/ui/Button.tsx" << 'EOF'
import clsx from 'clsx';
import LoadingSpinner from './LoadingSpinner';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
}

export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  loading,
  icon,
  className,
  disabled,
  ...props
}: ButtonProps) {
  const variants = {
    primary: 'btn-primary',
    secondary: 'btn-secondary',
    danger: 'btn-danger',
    ghost: 'text-gray-600 hover:bg-gray-100',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2',
    lg: 'px-6 py-3 text-lg',
  };

  return (
    <button
      className={clsx(
        'btn',
        variants[variant],
        sizes[size],
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <LoadingSpinner size="sm" />
      ) : (
        <>
          {icon && <span className="ml-2">{icon}</span>}
          {children}
        </>
      )}
    </button>
  );
}
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Advisor Components
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/web/src/components/advisor/AdvisorPanel.tsx" << 'EOF'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { AlertTriangle, CheckCircle, Info, RefreshCw, Clock } from 'lucide-react';
import clsx from 'clsx';
import apiClient from '@/api/client';
import Card, { CardHeader, CardTitle } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

interface AdvisorPanelProps {
  fieldId: number;
}

interface Recommendation {
  id: number;
  uuid: string;
  rule_name: string;
  category: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  status: string;
  title_ar: string;
  title_en: string;
  description_ar: string;
  description_en: string;
  actions: Array<{
    action_ar: string;
    action_en: string;
    urgency: string;
  }>;
  confidence_score: number;
  created_at: string;
}

interface AdvisorSession {
  id: number;
  health_score: number;
  risk_score: number;
  recommendations: Recommendation[];
  alerts: any[];
}

export default function AdvisorPanel({ fieldId }: AdvisorPanelProps) {
  const { t, i18n } = useTranslation();
  const queryClient = useQueryClient();
  const isArabic = i18n.language === 'ar';

  const { data: session, isLoading, refetch } = useQuery({
    queryKey: ['advisor', fieldId],
    queryFn: async () => {
      const { data } = await apiClient.post<AdvisorSession>('/advisor/analyze', {
        field_id: fieldId,
      });
      return data;
    },
  });

  const actionMutation = useMutation({
    mutationFn: async ({ recId, action }: { recId: number; action: string }) => {
      await apiClient.post(`/advisor/recommendations/${recId}/action`, { action });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['advisor', fieldId] });
    },
  });

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'critical':
        return <AlertTriangle className="w-5 h-5 text-red-500" />;
      case 'high':
        return <AlertTriangle className="w-5 h-5 text-orange-500" />;
      case 'medium':
        return <Info className="w-5 h-5 text-yellow-500" />;
      default:
        return <CheckCircle className="w-5 h-5 text-green-500" />;
    }
  };

  const getPriorityClass = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'border-red-500 bg-red-50';
      case 'high':
        return 'border-orange-500 bg-orange-50';
      case 'medium':
        return 'border-yellow-500 bg-yellow-50';
      default:
        return 'border-green-500 bg-green-50';
    }
  };

  const getUrgencyText = (urgency: string) => {
    return t(`advisor.urgency.${urgency}`);
  };

  if (isLoading) {
    return (
      <Card className="flex items-center justify-center h-64">
        <LoadingSpinner />
        <span className="mr-3">{t('common.loading')}</span>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex items-center justify-between">
        <CardTitle>{t('advisor.title')}</CardTitle>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => refetch()}
          icon={<RefreshCw className="w-4 h-4" />}
        >
          {t('common.refresh')}
        </Button>
      </CardHeader>

      {/* Health Score */}
      {session && (
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-3xl font-bold text-green-600">
              {session.health_score?.toFixed(0) || 0}%
            </div>
            <div className="text-sm text-gray-600">صحة الحقل</div>
          </div>
          <div className="text-center p-4 bg-red-50 rounded-lg">
            <div className="text-3xl font-bold text-red-600">
              {session.risk_score?.toFixed(0) || 0}%
            </div>
            <div className="text-sm text-gray-600">مستوى المخاطر</div>
          </div>
        </div>
      )}

      {/* Recommendations */}
      <div className="space-y-4">
        {session?.recommendations?.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <CheckCircle className="w-12 h-12 mx-auto mb-3 text-green-500" />
            <p>لا توجد توصيات حالياً - الحقل في حالة جيدة</p>
          </div>
        ) : (
          session?.recommendations?.map((rec) => (
            <div
              key={rec.id}
              className={clsx(
                'p-4 rounded-lg border-r-4',
                getPriorityClass(rec.priority)
              )}
            >
              <div className="flex items-start gap-3">
                {getPriorityIcon(rec.priority)}
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-gray-900">
                      {isArabic ? rec.title_ar : rec.title_en}
                    </h4>
                    <span className={clsx(
                      'px-2 py-1 text-xs rounded-full',
                      rec.priority === 'critical' ? 'bg-red-100 text-red-700' :
                      rec.priority === 'high' ? 'bg-orange-100 text-orange-700' :
                      'bg-yellow-100 text-yellow-700'
                    )}>
                      {t(`advisor.priority.${rec.priority}`)}
                    </span>
                  </div>

                  <p className="text-sm text-gray-600 mb-3">
                    {isArabic ? rec.description_ar : rec.description_en}
                  </p>

                  {rec.actions?.length > 0 && (
                    <div className="space-y-2 mb-3">
                      <p className="text-xs font-medium text-gray-500">الإجراءات:</p>
                      {rec.actions.map((action, idx) => (
                        <div key={idx} className="flex items-center gap-2 text-sm">
                          <Clock className="w-4 h-4 text-gray-400" />
                          <span>{isArabic ? action.action_ar : action.action_en}</span>
                          <span className={clsx(
                            'px-1.5 py-0.5 text-xs rounded',
                            action.urgency === 'immediate' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'
                          )}>
                            {getUrgencyText(action.urgency)}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}

                  {rec.status === 'pending' && (
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        onClick={() => actionMutation.mutate({ recId: rec.id, action: 'accept' })}
                      >
                        قبول
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => actionMutation.mutate({ recId: rec.id, action: 'reject' })}
                      >
                        رفض
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </Card>
  );
}
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Pages
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/web/src/pages/Login.tsx" << 'EOF'
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Leaf, Mail, Lock, AlertCircle } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import apiClient from '@/api/client';
import Button from '@/components/ui/Button';

export default function Login() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { setUser, setTokens } = useAuthStore();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const { data } = await apiClient.post('/auth/login', { email, password });
      setTokens(data.access_token, data.refresh_token);

      const { data: user } = await apiClient.get('/auth/me');
      setUser(user);

      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.error?.message || t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-4">
              <Leaf className="w-8 h-8 text-primary-600" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Field Suite Pro</h1>
            <p className="text-gray-500 mt-1">نظام إدارة الحقول الزراعية</p>
          </div>

          {/* Error */}
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3 text-red-700">
              <AlertCircle className="w-5 h-5" />
              {error}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">{t('auth.email')}</label>
              <div className="relative">
                <Mail className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input pr-10"
                  placeholder="example@email.com"
                  required
                />
              </div>
            </div>

            <div>
              <label className="label">{t('auth.password')}</label>
              <div className="relative">
                <Lock className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input pr-10"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            <Button type="submit" className="w-full" loading={loading}>
              {t('auth.login')}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
EOF

cat > "$PROJECT_NAME/web/src/pages/Dashboard.tsx" << 'EOF'
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Map, BarChart3, AlertTriangle, TrendingUp } from 'lucide-react';
import apiClient from '@/api/client';
import Card, { CardHeader, CardTitle } from '@/components/ui/Card';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

export default function Dashboard() {
  const { t } = useTranslation();

  const { data: fields, isLoading } = useQuery({
    queryKey: ['fields'],
    queryFn: async () => {
      const { data } = await apiClient.get('/fields');
      return data;
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  const stats = [
    { label: 'إجمالي الحقول', value: fields?.total || 0, icon: Map, color: 'text-blue-600 bg-blue-100' },
    { label: 'متوسط NDVI', value: '0.65', icon: BarChart3, color: 'text-green-600 bg-green-100' },
    { label: 'تنبيهات نشطة', value: '3', icon: AlertTriangle, color: 'text-orange-600 bg-orange-100' },
    { label: 'نمو هذا الشهر', value: '+12%', icon: TrendingUp, color: 'text-purple-600 bg-purple-100' },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">{t('nav.dashboard')}</h1>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => (
          <Card key={index} className="flex items-center gap-4">
            <div className={`p-3 rounded-lg ${stat.color}`}>
              <stat.icon className="w-6 h-6" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              <p className="text-sm text-gray-500">{stat.label}</p>
            </div>
          </Card>
        ))}
      </div>

      {/* Recent Fields */}
      <Card>
        <CardHeader>
          <CardTitle>الحقول الأخيرة</CardTitle>
        </CardHeader>
        <div className="space-y-3">
          {fields?.items?.slice(0, 5).map((field: any) => (
            <div key={field.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900">{field.name}</p>
                <p className="text-sm text-gray-500">{field.crop_type}</p>
              </div>
              <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
                {field.status}
              </span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
EOF

cat > "$PROJECT_NAME/web/src/pages/Fields.tsx" << 'EOF'
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { Plus, MapPin } from 'lucide-react';
import apiClient from '@/api/client';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

export default function Fields() {
  const { t } = useTranslation();

  const { data, isLoading } = useQuery({
    queryKey: ['fields'],
    queryFn: async () => {
      const { data } = await apiClient.get('/fields');
      return data;
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">{t('fields.title')}</h1>
        <Button icon={<Plus className="w-4 h-4" />}>
          {t('fields.addField')}
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data?.items?.map((field: any) => (
          <Link key={field.id} to={`/fields/${field.id}`}>
            <Card className="hover:shadow-md transition-shadow cursor-pointer">
              <div className="flex items-start justify-between mb-4">
                <div className="p-2 bg-primary-100 rounded-lg">
                  <MapPin className="w-5 h-5 text-primary-600" />
                </div>
                <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">
                  {field.status}
                </span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-1">{field.name}</h3>
              <p className="text-sm text-gray-500 mb-3">{field.crop_type || 'غير محدد'}</p>
              {field.area_ha && (
                <p className="text-sm text-gray-600">
                  المساحة: {field.area_ha.toFixed(2)} هكتار
                </p>
              )}
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
EOF

cat > "$PROJECT_NAME/web/src/pages/FieldDetails.tsx" << 'EOF'
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import apiClient from '@/api/client';
import Card, { CardHeader, CardTitle } from '@/components/ui/Card';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import AdvisorPanel from '@/components/advisor/AdvisorPanel';

export default function FieldDetails() {
  const { id } = useParams<{ id: string }>();
  const { t } = useTranslation();
  const fieldId = parseInt(id || '0');

  const { data: field, isLoading } = useQuery({
    queryKey: ['field', fieldId],
    queryFn: async () => {
      const { data } = await apiClient.get(`/fields/${fieldId}`);
      return data;
    },
    enabled: !!fieldId,
  });

  const { data: ndvi } = useQuery({
    queryKey: ['ndvi', fieldId],
    queryFn: async () => {
      const { data } = await apiClient.get(`/ndvi/${fieldId}`);
      return data;
    },
    enabled: !!fieldId,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">{field?.name}</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Field Info */}
        <Card>
          <CardHeader>
            <CardTitle>معلومات الحقل</CardTitle>
          </CardHeader>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-500">المحصول:</span>
              <span className="font-medium">{field?.crop_type || 'غير محدد'}</span>
            </div>
            {field?.area_ha && (
              <div className="flex justify-between">
                <span className="text-gray-500">المساحة:</span>
                <span className="font-medium">{field.area_ha.toFixed(2)} هكتار</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-gray-500">الحالة:</span>
              <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-sm">
                {field?.status}
              </span>
            </div>
          </div>
        </Card>

        {/* NDVI Data */}
        <Card>
          <CardHeader>
            <CardTitle>{t('ndvi.title')}</CardTitle>
          </CardHeader>
          {ndvi ? (
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {ndvi.mean_ndvi?.toFixed(3)}
                </div>
                <div className="text-sm text-gray-500">{t('ndvi.mean')}</div>
              </div>
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {ndvi.max_ndvi?.toFixed(3)}
                </div>
                <div className="text-sm text-gray-500">{t('ndvi.max')}</div>
              </div>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">لا توجد بيانات NDVI</p>
          )}
        </Card>

        {/* Advisor Panel */}
        <div className="lg:col-span-2">
          <AdvisorPanel fieldId={fieldId} />
        </div>
      </div>
    </div>
  );
}
EOF

cat > "$PROJECT_NAME/web/src/pages/Advisor.tsx" << 'EOF'
import { useTranslation } from 'react-i18next';
import Card from '@/components/ui/Card';

export default function Advisor() {
  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">{t('advisor.title')}</h1>
      <Card>
        <p className="text-gray-500">اختر حقلاً من صفحة الحقول لعرض التوصيات</p>
      </Card>
    </div>
  );
}
EOF

cat > "$PROJECT_NAME/web/src/pages/Settings.tsx" << 'EOF'
import { useTranslation } from 'react-i18next';
import Card, { CardHeader, CardTitle } from '@/components/ui/Card';

export default function Settings() {
  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">{t('nav.settings')}</h1>
      <Card>
        <CardHeader>
          <CardTitle>الإعدادات العامة</CardTitle>
        </CardHeader>
        <p className="text-gray-500">قريباً...</p>
      </Card>
    </div>
  );
}
EOF

log_success "تم إنشاء مكونات الواجهة الأمامية"
