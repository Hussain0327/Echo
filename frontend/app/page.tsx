'use client';

import { useState } from 'react';
import Link from 'next/link';
import FileUpload from '@/components/FileUpload';
import MetricsCard from '@/components/MetricsCard';
import { api, ApiError } from '@/lib/api';

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = async (selectedFile: File) => {
    setFile(selectedFile);
    setError(null);
    setLoading(true);

    try {
      const result = await api.uploadAndCalculateMetrics(selectedFile, [
        'TotalRevenue',
        'AverageOrderValue',
        'ConversionRate',
      ]);
      setMetrics(result);
    } catch (err) {
      console.error('Full error:', err);
      if (err instanceof ApiError) {
        setError(`API Error (${err.status}): ${err.message}`);
      } else if (err instanceof TypeError) {
        setError(`Network Error: ${err.message}. Make sure backend is running on http://localhost:8000`);
      } else {
        setError(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">Echo</h1>
              <span className="ml-2 text-sm text-gray-500">AI Data Scientist</span>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/" className="text-gray-900 font-medium">Home</Link>
              <Link href="/chat" className="text-gray-600 hover:text-gray-900">Chat</Link>
              <Link href="/reports" className="text-gray-600 hover:text-gray-900">Reports</Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900">Analyze Your Business Data</h2>
          <p className="mt-2 text-gray-600">
            Upload your CSV or Excel file to get instant metrics and insights
          </p>
        </div>

        <div className="mb-8">
          <FileUpload onFileSelect={handleFileSelect} />
        </div>

        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Calculating metrics...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
            <p className="text-red-800">{error}</p>
            <p className="text-sm text-red-600 mt-1">
              Make sure your backend is running: <code className="bg-red-100 px-1 rounded">docker-compose up -d</code>
            </p>
          </div>
        )}

        {metrics && !loading && (
          <div>
            <h3 className="text-xl font-bold text-gray-900 mb-4">Your Metrics</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {metrics.results && metrics.results.map((metric: any) => (
                <MetricsCard
                  key={metric.metric_name}
                  title={metric.metric_name.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
                  value={typeof metric.value === 'number' ? metric.value.toLocaleString() : metric.value}
                  unit={metric.unit}
                  description={metric.metadata?.transaction_count ? `${metric.metadata.transaction_count} transactions` : undefined}
                />
              ))}
            </div>

            <div className="mt-8 bg-white rounded-lg shadow p-6 border border-gray-200">
              <h4 className="font-semibold text-gray-900 mb-2">Next Steps</h4>
              <div className="space-y-2 text-sm text-gray-600">
                <p>• <Link href="/chat" className="text-blue-600 hover:underline">Chat with Echo</Link> to ask questions about your data</p>
                <p>• <Link href="/reports" className="text-blue-600 hover:underline">Generate a report</Link> for detailed analysis</p>
              </div>
            </div>
          </div>
        )}

        {!file && !loading && !error && (
          <div className="text-center py-12">
            <p className="text-gray-500">Upload a file to get started</p>
            <div className="mt-4 space-y-2 text-sm text-gray-400">
              <p>Sample data available in: <code className="bg-gray-100 px-2 py-1 rounded">data/samples/</code></p>
              <p>• revenue_sample.csv</p>
              <p>• marketing_sample.csv</p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
