/**
 * ClawLayer API client
 */

const API_BASE = '/api';

export interface Stats {
  requests: number;
  router_hits: Record<string, number>;
  avg_latency: number;
  uptime: number;
}

export interface Router {
  name: string;
  type: string;
  enabled: boolean;
}

export interface Log {
  timestamp: number;
  message: string;
  router: string;
  latency_ms: number;
  content?: string;
}

export interface TestResult {
  router: string;
  content?: string;
  latency_ms: number;
  should_proxy: boolean;
}

export class ClawLayerClient {
  async getStats(): Promise<Stats> {
    const res = await fetch(`${API_BASE}/stats`);
    return res.json();
  }
  
  async getConfig(): Promise<any> {
    const res = await fetch(`${API_BASE}/config`);
    return res.json();
  }
  
  async saveConfig(config: any): Promise<{ status: string }> {
    const res = await fetch(`${API_BASE}/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    return res.json();
  }
  
  async reloadConfig(): Promise<{ status: string; message: string }> {
    const res = await fetch(`${API_BASE}/config/reload`, {
      method: 'POST'
    });
    return res.json();
  }
  
  async getRouters(): Promise<Router[]> {
    const res = await fetch(`${API_BASE}/routers`);
    return res.json();
  }
  
  async testRoute(message: string): Promise<TestResult> {
    const res = await fetch(`${API_BASE}/test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
    return res.json();
  }
  
  async getLogs(limit = 50): Promise<Log[]> {
    const res = await fetch(`${API_BASE}/logs?limit=${limit}`);
    return res.json();
  }
}
