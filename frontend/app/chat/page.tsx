'use client';

import { useState } from 'react';
import Link from 'next/link';
import ChatInterface from '@/components/ChatInterface';
import FileUpload from '@/components/FileUpload';
import { ChatMessage } from '@/types';
import { api } from '@/lib/api';

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [isLoading, setIsLoading] = useState(false);
  const [hasData, setHasData] = useState(false);

  const handleFileSelect = async (file: File) => {
    setIsLoading(true);
    try {
      const result = await api.chatWithData('Analyze this data and give me a summary.', file);
      setSessionId(result.session_id);
      setMessages([
        { role: 'assistant', content: result.message, timestamp: new Date() }
      ]);
      setHasData(true);
    } catch (error) {
      console.error('Failed to load data:', error);
      setMessages([
        { role: 'assistant', content: 'Failed to load data. Please try again.', timestamp: new Date() }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async (message: string) => {
    const userMessage: ChatMessage = {
      role: 'user',
      content: message,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const result = await api.chat(message, sessionId);
      setSessionId(result.session_id);
      
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: result.message,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
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
              <Link href="/chat" className="text-gray-900 font-medium">Chat</Link>
              <Link href="/reports" className="text-gray-600 hover:text-gray-900">Reports</Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900">Chat with Echo</h2>
          <p className="mt-2 text-gray-600">
            Upload data and ask questions in natural language
          </p>
        </div>

        {!hasData && (
          <div className="mb-8">
            <p className="text-sm text-gray-600 mb-4">First, upload your data:</p>
            <FileUpload onFileSelect={handleFileSelect} />
          </div>
        )}

        <ChatInterface
          onSendMessage={handleSendMessage}
          messages={messages}
          isLoading={isLoading}
        />
      </main>
    </div>
  );
}
