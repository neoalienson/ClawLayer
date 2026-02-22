import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ClawLayerClient } from '../api/clawlayer-client';

describe('ClawLayerClient', () => {
  let client: ClawLayerClient;
  let mockFetch: any;

  beforeEach(() => {
    client = new ClawLayerClient();
    mockFetch = vi.mocked(fetch);
  });

  describe('getStats', () => {
    it('should fetch stats from API', async () => {
      const mockStats = { requests: 10, router_hits: {}, avg_latency: 100, uptime: 3600 };
      mockFetch.mockResolvedValueOnce({
        json: () => Promise.resolve(mockStats),
      } as Response);

      const result = await client.getStats();

      expect(mockFetch).toHaveBeenCalledWith('/api/stats');
      expect(result).toEqual(mockStats);
    });
  });

  describe('getConfig', () => {
    it('should fetch config from API', async () => {
      const mockConfig = { providers: {}, server: { port: 11435 } };
      mockFetch.mockResolvedValueOnce({
        json: () => Promise.resolve(mockConfig),
      } as Response);

      const result = await client.getConfig();

      expect(mockFetch).toHaveBeenCalledWith('/api/config');
      expect(result).toEqual(mockConfig);
    });
  });

  describe('saveConfig', () => {
    it('should save config via POST request', async () => {
      const config = { server: { port: 8080 } };
      const mockResponse = { status: 'saved' };
      mockFetch.mockResolvedValueOnce({
        json: () => Promise.resolve(mockResponse),
      } as Response);

      const result = await client.saveConfig(config);

      expect(mockFetch).toHaveBeenCalledWith('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe('testRoute', () => {
    it('should test route with message', async () => {
      const message = 'hello';
      const mockResult = { router: 'greeting', latency_ms: 50, should_proxy: false };
      mockFetch.mockResolvedValueOnce({
        json: () => Promise.resolve(mockResult),
      } as Response);

      const result = await client.testRoute(message);

      expect(mockFetch).toHaveBeenCalledWith('/api/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      });
      expect(result).toEqual(mockResult);
    });
  });
});