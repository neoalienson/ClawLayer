import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { ClawLayerClient, Log } from '../api/clawlayer-client';

@customElement('cl-log-viewer')
export class LogViewer extends LitElement {
  static styles = css`
    :host { display: block; padding: 2rem; }
    h1 { margin: 0 0 1rem 0; color: #2c3e50; }
    .logs { background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); max-height: 600px; overflow-y: auto; }
    .log-entry { display: grid; grid-template-columns: 100px 1fr 150px 80px; gap: 1rem; padding: 0.75rem 1rem; border-bottom: 1px solid #ecf0f1; font-size: 14px; cursor: pointer; }
    .log-entry:hover { background: #f8f9fa; }
    .log-time { color: #7f8c8d; }
    .log-message { font-family: monospace; }
    .log-router { font-weight: 500; color: #3498db; }
    .log-latency { text-align: right; color: #7f8c8d; }
    .empty { padding: 2rem; text-align: center; color: #7f8c8d; }
    
    .modal { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
    .modal-content { background: white; border-radius: 8px; max-width: 800px; max-height: 80vh; overflow-y: auto; padding: 2rem; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
    .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
    .modal-header h2 { margin: 0; color: #2c3e50; }
    .close-btn { background: none; border: none; font-size: 24px; cursor: pointer; color: #7f8c8d; padding: 0; width: 32px; height: 32px; }
    .close-btn:hover { color: #2c3e50; }
    .detail-section { margin-bottom: 1.5rem; }
    .detail-section h3 { margin: 0 0 0.5rem 0; color: #34495e; font-size: 14px; text-transform: uppercase; }
    .detail-content { background: #f8f9fa; padding: 1rem; border-radius: 4px; font-family: monospace; font-size: 13px; white-space: pre-wrap; word-break: break-all; }
    .detail-grid { display: grid; grid-template-columns: 120px 1fr; gap: 0.5rem; }
    .detail-label { font-weight: 600; color: #7f8c8d; }
    .detail-value { color: #2c3e50; }
  `;
  
  @state() logs: Log[] = [];
  @state() selectedLog: Log | null = null;
  
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
  
  formatFullTime(timestamp: number) {
    return new Date(timestamp * 1000).toLocaleString();
  }
  
  openDetail(log: Log) {
    this.selectedLog = log;
  }
  
  closeDetail() {
    this.selectedLog = null;
  }
  
  renderModal() {
    if (!this.selectedLog) return null;
    
    const log = this.selectedLog;
    
    return html`
      <div class="modal" @click=${this.closeDetail}>
        <div class="modal-content" @click=${(e: Event) => e.stopPropagation()}>
          <div class="modal-header">
            <h2>Request Details</h2>
            <button class="close-btn" @click=${this.closeDetail}>&times;</button>
          </div>
          
          <div class="detail-section">
            <div class="detail-grid">
              <div class="detail-label">Timestamp:</div>
              <div class="detail-value">${this.formatFullTime(log.timestamp)}</div>
              
              <div class="detail-label">Router:</div>
              <div class="detail-value">${log.router}</div>
              
              <div class="detail-label">Latency:</div>
              <div class="detail-value">${log.latency_ms.toFixed(2)}ms</div>
            </div>
          </div>
          
          <div class="detail-section">
            <h3>Message</h3>
            <div class="detail-content">${(log as any).full_message || log.message}</div>
          </div>
          
          ${(log as any).full_content ? html`
            <div class="detail-section">
              <h3>Response Content</h3>
              <div class="detail-content">${(log as any).full_content}</div>
            </div>
          ` : ''}
          
          ${(log as any).request ? html`
            <div class="detail-section">
              <h3>Request Data</h3>
              <div class="detail-content">${JSON.stringify((log as any).request, null, 2)}</div>
            </div>
          ` : ''}
          
          ${(log as any).response ? html`
            <div class="detail-section">
              <h3>Response Data</h3>
              <div class="detail-content">${JSON.stringify((log as any).response, null, 2)}</div>
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }
  
  render() {
    return html`
      <h1>Request Logs</h1>
      <div class="logs">
        ${this.logs.length === 0 ? html`
          <div class="empty">No requests yet</div>
        ` : this.logs.slice().reverse().map(log => html`
          <div class="log-entry" @click=${() => this.openDetail(log)}>
            <div class="log-time">${this.formatTime(log.timestamp)}</div>
            <div class="log-message">${log.message}</div>
            <div class="log-router">${log.router}</div>
            <div class="log-latency">${log.latency_ms.toFixed(1)}ms</div>
          </div>
        `)}
      </div>
      ${this.renderModal()}
    `;
  }
}
