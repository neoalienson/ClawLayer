import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { ClawLayerClient, Stats, Router } from '../api/clawlayer-client';

@customElement('cl-dashboard')
export class Dashboard extends LitElement {
  static styles = css`
    :host { display: block; padding: 2rem; }
    h1 { margin: 0 0 2rem 0; color: #2c3e50; }
    .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
    .stat-card { background: #ecf0f1; padding: 1.5rem; border-radius: 8px; }
    .stat-label { font-size: 0.875rem; color: #7f8c8d; margin-bottom: 0.5rem; }
    .stat-value { font-size: 2rem; font-weight: bold; color: #2c3e50; }
    .router-chain { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .router-chain h2 { margin: 0 0 1rem 0; color: #2c3e50; }
    .router-list { display: flex; flex-direction: column; gap: 0.5rem; }
    .router-item { display: flex; justify-content: space-between; padding: 0.75rem; background: #f8f9fa; border-radius: 4px; }
    .router-name { font-weight: 500; }
    .router-hits { color: #7f8c8d; }
  `;
  
  @state() stats: Stats = { requests: 0, router_hits: {}, avg_latency: 0, uptime: 0 };
  @state() routers: Router[] = [];
  
  private client = new ClawLayerClient();
  private eventSource?: EventSource;
  
  connectedCallback() {
    super.connectedCallback();
    this.startEventStream();
  }
  
  disconnectedCallback() {
    super.disconnectedCallback();
    if (this.eventSource) {
      this.eventSource.close();
    }
  }
  
  startEventStream() {
    this.eventSource = new EventSource('/api/events');
    this.eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.stats = data.stats;
      this.routers = data.routers || this.routers;
    };
    this.eventSource.onerror = () => {
      console.log('SSE connection lost, retrying...');
    };
  }
  
  async loadData() {
    try {
      this.stats = await this.client.getStats();
      this.routers = await this.client.getRouters();
    } catch (e) {
      console.error('Failed to load data:', e);
    }
  }
  
  render() {
    const totalHits = Object.values(this.stats.router_hits).reduce((a, b) => a + b, 0);
    const hitRate = this.stats.requests > 0 ? (totalHits / this.stats.requests * 100).toFixed(1) : '0';
    
    return html`
      <h1>ClawLayer Dashboard</h1>
      
      <div class="stats">
        <div class="stat-card">
          <div class="stat-label">Total Requests</div>
          <div class="stat-value">${this.stats.requests}</div>
        </div>
        
        <div class="stat-card">
          <div class="stat-label">Router Hit Rate</div>
          <div class="stat-value">${hitRate}%</div>
        </div>
        
        <div class="stat-card">
          <div class="stat-label">Avg Latency</div>
          <div class="stat-value">${this.stats.avg_latency.toFixed(0)}ms</div>
        </div>
        
        <div class="stat-card">
          <div class="stat-label">Uptime</div>
          <div class="stat-value">${Math.floor(this.stats.uptime / 60)}m</div>
        </div>
      </div>
      
      <div class="router-chain">
        <h2>Router Performance</h2>
        <div class="router-list">
          ${Object.entries(this.stats.router_hits).map(([name, count]) => html`
            <div class="router-item">
              <span class="router-name">${name}</span>
              <span class="router-hits">${count} hits</span>
            </div>
          `)}
        </div>
      </div>
    `;
  }
}
