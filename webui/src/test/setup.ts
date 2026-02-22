import { beforeEach, vi } from 'vitest';

// Mock fetch globally
global.fetch = vi.fn();

// Mock EventSource
global.EventSource = vi.fn(() => ({
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  close: vi.fn(),
  onmessage: null,
  onerror: null,
}));

beforeEach(() => {
  vi.clearAllMocks();
});