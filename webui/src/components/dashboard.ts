import { LitElement, html, css, unsafeCSS } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { ClawLayerClient, Stats, Router } from '../api/clawlayer-client';
import dashboardStyles from '../styles/dashboard.css?inline';

@customElement('cl-dashboard')
export class Dashboard extends LitElement {
  static styles = css`${unsafeCSS(dashboardStyles)}`;
  
  @state() stats: Stats = { 
    requests: 0, 
    router_hits: {}, 
    avg_latency: 0, 
    uptime: 0,
    cost_saved: 0,
    distribution: { handlers_pct: 0, semantic_pct: 0, llm_pct: 0 }
  };
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
    const costSaved = this.stats.cost_saved || 0;
    const dist = this.stats.distribution || { handlers_pct: 0, semantic_pct: 0, llm_pct: 0 };
    
    return html`
      <h1>ClawLayer Dashboard</h1>
      
      <div class="stats">
        <div class="stat-card">
          <div class="stat-label">Total Requests</div>
          <div class="stat-value">${this.stats.requests}</div>
        </div>
        
        <div class="stat-card">
          <div class="stat-label">Cost Saved</div>
          <div class="stat-value">$${costSaved.toFixed(4)}</div>
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
        <h2>Request Distribution</h2>
        <div class="router-list">
          <div class="router-item">
            <span class="router-name">Fast Routers (zero cost)</span>
            <span class="router-hits">${dist.handlers_pct}%</span>
          </div>
          <div class="router-item">
            <span class="router-name">Semantic Routers (cheap)</span>
            <span class="router-hits">${dist.semantic_pct}%</span>
          </div>
          <div class="router-item">
            <span class="router-name">LLM Fallback (expensive)</span>
            <span class="router-hits">${dist.llm_pct}%</span>
          </div>
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
