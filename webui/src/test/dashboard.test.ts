import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Dashboard } from '../components/dashboard';
import { ClawLayerClient } from '../api/clawlayer-client';

// Mock the ClawLayerClient
vi.mock('../api/clawlayer-client');

describe('Dashboard', () => {
  let dashboard: Dashboard;
  let mockClient: any;
  let mockEventSource: any;

  beforeEach(() => {
    mockClient = {
      getStats: vi.fn(),
      getRouters: vi.fn(),
    };
    vi.mocked(ClawLayerClient).mockImplementation(() => mockClient);
    
    mockEventSource = {
      onmessage: null,
      onerror: null,
      close: vi.fn(),
    };
    vi.mocked(EventSource).mockImplementation(() => mockEventSource);
    
    dashboard = new Dashboard();
    document.body.appendChild(dashboard);
  });

  afterEach(() => {
    document.body.removeChild(dashboard);
  });

  describe('loadData', () => {
    it('should load stats and routers from API', async () => {
      const mockStats = { requests: 10, router_hits: { greeting: 5 }, avg_latency: 100, uptime: 3600 };
      const mockRouters = [{ name: 'GreetingRouter', type: 'semantic', enabled: true }];
      
      mockClient.getStats.mockResolvedValue(mockStats);
      mockClient.getRouters.mockResolvedValue(mockRouters);

      await dashboard.loadData();

      expect(mockClient.getStats).toHaveBeenCalled();
      expect(mockClient.getRouters).toHaveBeenCalled();
      expect(dashboard.stats).toEqual(mockStats);
      expect(dashboard.routers).toEqual(mockRouters);
    });

    it('should handle API errors gracefully', async () => {
      mockClient.getStats.mockRejectedValue(new Error('Network error'));
      mockClient.getRouters.mockRejectedValue(new Error('Network error'));
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      await dashboard.loadData();

      expect(consoleSpy).toHaveBeenCalledWith('Failed to load data:', expect.any(Error));
    });
  });

  describe('startEventStream', () => {
    it('should create EventSource and handle messages', () => {
      dashboard.startEventStream();

      expect(EventSource).toHaveBeenCalledWith('/api/events');
      
      // Simulate SSE message
      const mockData = {
        stats: { requests: 15, router_hits: { greeting: 8 }, avg_latency: 90, uptime: 3700 },
        routers: [{ name: 'GreetingRouter', type: 'semantic', enabled: true }],
      };
      
      mockEventSource.onmessage({ data: JSON.stringify(mockData) });

      expect(dashboard.stats).toEqual(mockData.stats);
      expect(dashboard.routers).toEqual(mockData.routers);
    });

    it('should handle SSE errors', () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      
      dashboard.startEventStream();
      mockEventSource.onerror();

      expect(consoleSpy).toHaveBeenCalledWith('SSE connection lost, retrying...');
    });
  });

  describe('disconnectedCallback', () => {
    it('should close EventSource on disconnect', () => {
      dashboard.startEventStream();
      
      dashboard.disconnectedCallback();

      expect(mockEventSource.close).toHaveBeenCalled();
    });
  });

  describe('render calculations', () => {
    it('should calculate hit rate correctly', () => {
      dashboard.stats = {
        requests: 100,
        router_hits: { greeting: 30, command: 20 },
        avg_latency: 150,
        uptime: 7200,
      };

      // Trigger render to test calculations
      const rendered = dashboard.render();
      const htmlString = rendered.strings.join('');
      
      // Hit rate should be (30 + 20) / 100 * 100 = 50%
      expect(htmlString).toContain('50.0%');
    });

    it('should handle zero requests', () => {
      dashboard.stats = {
        requests: 0,
        router_hits: {},
        avg_latency: 0,
        uptime: 0,
      };

      const rendered = dashboard.render();
      const htmlString = rendered.strings.join('');
      
      expect(htmlString).toContain('0%');
    });

    it('should format uptime in minutes', () => {
      dashboard.stats = {
        requests: 10,
        router_hits: {},
        avg_latency: 100,
        uptime: 3660, // 61 minutes
      };

      const rendered = dashboard.render();
      const htmlString = rendered.strings.join('');
      
      expect(htmlString).toContain('61m');
    });
  });
});