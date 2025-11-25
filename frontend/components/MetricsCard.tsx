'use client';

interface MetricsCardProps {
  title: string;
  value: string | number;
  unit?: string;
  description?: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
}

export default function MetricsCard({ title, value, unit, description, trend, trendValue }: MetricsCardProps) {
  const trendColors = {
    up: 'text-green-600',
    down: 'text-red-600',
    neutral: 'text-gray-600',
  };

  const trendIcons = {
    up: '↑',
    down: '↓',
    neutral: '→',
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 border border-gray-200 hover:shadow-md transition-shadow">
      <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">{title}</h3>
      <div className="mt-2 flex items-baseline">
        <p className="text-3xl font-semibold text-gray-900">
          {value}
          {unit && <span className="text-xl text-gray-600 ml-1">{unit}</span>}
        </p>
        {trend && trendValue && (
          <p className={`ml-2 flex items-baseline text-sm font-semibold ${trendColors[trend]}`}>
            <span className="mr-1">{trendIcons[trend]}</span>
            {trendValue}
          </p>
        )}
      </div>
      {description && <p className="mt-1 text-sm text-gray-600">{description}</p>}
    </div>
  );
}
