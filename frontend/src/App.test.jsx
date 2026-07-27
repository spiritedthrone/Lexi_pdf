import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';
import * as api from './services/api';

vi.mock('./services/api', () => ({
  checkHealth: vi.fn().mockResolvedValue({ status: 'healthy' }),
  uploadPdf: vi.fn().mockResolvedValue({ id: 'test-123', page_count: 1 }),
  simplifyPdf: vi.fn().mockResolvedValue({
    total_chunks: 1,
    total_words: 100,
    total_paragraphs: 2,
  }),
  downloadPdf: vi.fn().mockResolvedValue(),
}));

describe('PDF Summarizer App Frontend Tests', () => {
  it('renders application header and title correctly', async () => {
    render(<App />);
    expect(screen.getByText(/PDF Summarizer & Simplifier/i)).toBeInTheDocument();
  });

  it('renders PDF uploader dropzone', () => {
    render(<App />);
    expect(screen.getByText(/Drag & drop your PDF here/i)).toBeInTheDocument();
  });
});
