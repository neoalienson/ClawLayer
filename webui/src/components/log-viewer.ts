import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { ClawLayerClient, Log } from '../api/clawlayer-client';

@customElement('cl-log-viewer')
export class LogViewer extends LitElement {
  static styles = css`
    :host { display: block; padding: 2rem; }
    h1 { margin: 0 0 1rem 0; color: #2c3e50; }
    .logs { background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); max-height: 600px; overflow-y: auto; }
    .log-entry { display: grid; grid-template-columns: 100px 1fr 150px 80px; gap: 1rem; padding: 0.75rem 1rem; border-bottom: 1px solid #ecf0f1; font-size: 14px; }
    .log-entry:hover { background: #f8f9fa; }
    .log-time { color: #7f8c8d; }
    .log-message { font-family: monospace; }
    .log-router { font-weight: 500; color: #3498db; }
    .log-latency { text-align: right; color: #7f8c8d; }
    .empty { padding: 2rem; text-align: center; color: #7f8c8d; }
  `;
  
  @state() logs: Log[] = [];
  
  private client = new ClawLayerClient();
  private interval?: number;
  
  connectedCallback() {
    super.connectedCallback();
    this.loadLogs();
    this.interval = window.setInterval(() => this.loadLogs(), 2000);
  }
  
  disconnectedCallback() {
    super.disconnectedCallback();
    if (this.interval) clearInterval(this.interval);
  }
  
  async loadLogs() {
    try {
      this.logs = await this.client.getLogs(100);
    } catch (e) {
      console.error('Failed to load logs:', e);
    }
  }
  
  formatTime(timestamp: number) {
    return new Date(timestamp * 1000).toLocaleTimeString();
  }
  
  render() {
    return html`
      <h1>Request Logs</h1>
      <div class="logs">
        ${this.logs.length === 0 ? html`
          <div class="empty">No requests yet</div>
        ` : this.logs.slice().reverse().map(log => html`
          <div class="log-entry">
            <div class="log-time">${this.formatTime(log.timestamp)}</div>
            <div class="log-message">${log.message}</div>
            <div class="log-router">${log.router}</div>
            <div class="log-latency">${log.latency_ms.toFixed(1)}ms</div>
          </div>
        `)}
      </div>
    `;
  }
}
