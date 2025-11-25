export interface MetricResult {
  value: number | string;
  unit?: string;
  period?: string;
  metadata?: Record<string, any>;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface Report {
  id: string;
  report_type: string;
  generated_at: string;
  metrics: Record<string, MetricResult>;
  narratives: {
    executive_summary?: string;
    key_findings?: string[];
    detailed_analysis?: string;
    recommendations?: string[];
  };
}

export interface AnalyticsStats {
  total_sessions: number;
  total_time_saved_hours: number;
  avg_satisfaction_rating: number;
  accuracy_rate: number;
}
