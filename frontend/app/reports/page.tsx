'use client';

import { useState } from 'react';
import Link from 'next/link';
import FileUpload from '@/components/FileUpload';
import { api } from '@/lib/api';

export default function ReportsPage() {
  const [file, setFile] = useState<File | null>(null);
  const [templateType, setTemplateType] = useState('revenue_health');
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateReport = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);

    try {
      const result = await api.generateReport(file, templateType);
      setReport(result);
    } catch (err: any) {
      setError(err.message || 'Failed to generate report');
      console.error(err);
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
              <Link href="/" className="text-gray-600 hover:text-gray-900">Home</Link>
              <Link href="/chat" className="text-gray-600 hover:text-gray-900">Chat</Link>
              <Link href="/reports" className="text-gray-900 font-medium">Reports</Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900">Generate Report</h2>
          <p className="mt-2 text-gray-600">
            Create structured business reports with AI-generated insights
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1 space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Report Type
              </label>
              <select
                value={templateType}
                onChange={(e) => setTemplateType(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="revenue_health">Revenue Health</option>
                <option value="marketing_funnel">Marketing Funnel</option>
                <option value="financial_overview">Financial Overview</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Upload Data
              </label>
              <FileUpload onFileSelect={setFile} />
            </div>

            <button
              onClick={handleGenerateReport}
              disabled={!file || loading}
              className="w-full bg-blue-600 text-white rounded-lg px-6 py-3 font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Generating...' : 'Generate Report'}
            </button>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}
          </div>

          <div className="lg:col-span-2">
            {loading && (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                <p className="mt-4 text-gray-600">Generating your report...</p>
              </div>
            )}

            {report && !loading && (
              <div className="bg-white rounded-lg shadow border border-gray-200 p-8">
                <div className="mb-6">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">
                    {report.report_type?.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
                  </h3>
                  <p className="text-sm text-gray-500">
                    Generated {new Date(report.generated_at).toLocaleString()}
                  </p>
                </div>

                {report.narratives?.executive_summary && (
                  <div className="mb-6">
                    <h4 className="text-lg font-semibold text-gray-900 mb-2">Executive Summary</h4>
                    <p className="text-gray-700">{report.narratives.executive_summary}</p>
                  </div>
                )}

                {report.narratives?.key_findings && (
                  <div className="mb-6">
                    <h4 className="text-lg font-semibold text-gray-900 mb-2">Key Findings</h4>
                    <ul className="list-disc list-inside space-y-1 text-gray-700">
                      {report.narratives.key_findings.map((finding: string, idx: number) => (
                        <li key={idx}>{finding}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {report.narratives?.detailed_analysis && (
                  <div className="mb-6">
                    <h4 className="text-lg font-semibold text-gray-900 mb-2">Detailed Analysis</h4>
                    <p className="text-gray-700 whitespace-pre-wrap">{report.narratives.detailed_analysis}</p>
                  </div>
                )}

                {report.narratives?.recommendations && (
                  <div className="mb-6">
                    <h4 className="text-lg font-semibold text-gray-900 mb-2">Recommendations</h4>
                    <ul className="list-disc list-inside space-y-1 text-gray-700">
                      {report.narratives.recommendations.map((rec: string, idx: number) => (
                        <li key={idx}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {report.metrics && (
                  <div>
                    <h4 className="text-lg font-semibold text-gray-900 mb-2">Metrics</h4>
                    <div className="grid grid-cols-2 gap-4">
                      {Object.entries(report.metrics).map(([key, value]: [string, any]) => (
                        <div key={key} className="bg-gray-50 rounded p-3">
                          <p className="text-xs text-gray-600">{key.replace(/([A-Z])/g, ' $1').trim()}</p>
                          <p className="text-lg font-semibold text-gray-900">
                            {typeof value.value === 'number' ? value.value.toLocaleString() : value.value}
                            {value.unit && <span className="text-sm text-gray-600 ml-1">{value.unit}</span>}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {!report && !loading && (
              <div className="text-center py-12 text-gray-500">
                <p>Select a report type and upload data to generate a report</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
