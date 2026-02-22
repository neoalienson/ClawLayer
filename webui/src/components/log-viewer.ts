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
    .message-content { white-space: pre-wrap; }
    .collapsible { cursor: pointer; user-select: none; }
    .collapsible:hover { background: #ecf0f1; }
    .collapsed .detail-content { display: none; }
    .expand-icon { display: inline-block; width: 16px; transition: transform 0.2s; }
    .collapsed .expand-icon { transform: rotate(-90deg); }
    .request-field { margin-bottom: 0.75rem; }
    .request-field:last-child { margin-bottom: 0; }
    .separator { border-top: 1px solid #ecf0f1; margin: 1rem 0; }
    .section-header { font-weight: 600; color: #34495e; margin-bottom: 0.5rem; cursor: pointer; user-select: none; }
    .section-header:hover { background: #f8f9fa; }
    .message-preview { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #7f8c8d; font-style: italic; }
  `;
  
  @state() logs: Log[] = [];
  @state() selectedLog: Log | null = null;
  @state() collapsedSections: Set<string> = new Set(['request-data', 'response-data']);
  
  private client = new ClawLayerClient();
  private eventSource?: EventSource;
  
  connectedCallback() {
    super.connectedCallback();
    this.loadLogs();
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
      this.logs = data.logs || this.logs;
    };
    this.eventSource.onerror = () => {
      console.log('SSE connection lost, retrying...');
    };
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
    // Collapse all individual messages by default
    const request = (log as any).request;
    if (request?.messages) {
      request.messages.forEach((_: any, i: number) => {
        this.collapsedSections.add(`msg-${i}`);
      });
    }
  }
  
  closeDetail() {
    this.selectedLog = null;
    this.collapsedSections = new Set(['request-data', 'response-data']);
  }
  
  estimateTokens(request: any): string {
    if (!request) return 'N/A';
    let tokens = 0;
    if (request.messages) {
      tokens += request.messages.reduce((sum: number, msg: any) => {
        const content = this.extractMessageContent(msg.content);
        return sum + Math.ceil(content.length / 4);
      }, 0);
    }
    if (request.tools) {
      tokens += request.tools.reduce((sum: number, tool: any) => {
        const desc = tool.function?.description || '';
        return sum + Math.ceil(desc.length / 4);
      }, 0);
    }
    return `~${tokens}`;
  }
  
  extractMessageContent(content: any): string {
    if (typeof content === 'string') return content;
    if (Array.isArray(content)) {
      return content.map(item => item.text || JSON.stringify(item)).join(' ');
    }
    if (content && typeof content === 'object' && content.text) {
      return content.text;
    }
    return JSON.stringify(content);
  }
  
  toggleSection(sectionId: string) {
    if (this.collapsedSections.has(sectionId)) {
      this.collapsedSections.delete(sectionId);
    } else {
      this.collapsedSections.add(sectionId);
    }
    this.requestUpdate();
  }
  
  renderRequestFields(request: any) {
    if (!request) return '';
    
    return html`
      <div class="request-field">
        <div class="detail-grid">
          <div class="detail-label">Model:</div>
          <div class="detail-value">${request.model || 'N/A'}</div>
        </div>
      </div>
      
      <div class="request-field">
        <div class="detail-grid">
          <div class="detail-label">Stream:</div>
          <div class="detail-value">${request.stream ? 'Yes' : 'No'}</div>
        </div>
      </div>
      
      ${request.temperature !== undefined ? html`
        <div class="request-field">
          <div class="detail-grid">
            <div class="detail-label">Temperature:</div>
            <div class="detail-value">${request.temperature}</div>
          </div>
        </div>
      ` : ''}
      
      ${request.max_tokens !== undefined ? html`
        <div class="request-field">
          <div class="detail-grid">
            <div class="detail-label">Max Tokens:</div>
            <div class="detail-value">${request.max_tokens}</div>
          </div>
        </div>
      ` : ''}
      
      ${request.max_completion_tokens !== undefined ? html`
        <div class="request-field">
          <div class="detail-grid">
            <div class="detail-label">Max Completion Tokens:</div>
            <div class="detail-value">${request.max_completion_tokens}</div>
          </div>
        </div>
      ` : ''}
      
      <div class="separator"></div>
      
      <div class="section-header">
        Messages
      </div>
      
      <div class="request-field">
        <div class="detail-grid">
          <div class="detail-label">Count:</div>
          <div class="detail-value">${request.messages?.length || 0} message(s)</div>
        </div>
      </div>
      
      ${request.messages?.map((msg: any, i: number) => html`
        <div class="request-field">
          <div class="detail-grid">
            <div class="detail-label">${i + 1}. ${msg.role}:</div>
            <div class="detail-value">
              <div class="section-header" @click=${() => this.toggleSection(`msg-${i}`)}>
                <span class="expand-icon">${this.collapsedSections.has(`msg-${i}`) ? '▶' : '▼'}</span> Click to ${this.collapsedSections.has(`msg-${i}`) ? 'expand' : 'collapse'}
              </div>
              ${this.collapsedSections.has(`msg-${i}`) ? html`
                <div class="message-preview">${this.extractMessageContent(msg.content)}</div>
              ` : html`
                <div class="message-content">${this.extractMessageContent(msg.content)}</div>
              `}
            </div>
          </div>
        </div>
      `)}
      
      ${request.tools ? html`
        <div class="separator"></div>
        
        <div class="section-header">
          Tools
        </div>
        
        <div class="request-field">
          <div class="detail-grid">
            <div class="detail-label">Count:</div>
            <div class="detail-value">${request.tools.length} tool(s)</div>
          </div>
        </div>
        
        ${request.tools.map((tool: any, i: number) => html`
          <div class="request-field">
            <div class="detail-grid">
              <div class="detail-label">${i + 1}. ${tool.function?.name || 'Unknown'}:</div>
              <div class="detail-value message-content">${tool.function?.description || 'No description'}</div>
            </div>
          </div>
        `)}
      ` : ''}
    `;
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
              
              <div class="detail-label">Est. Tokens:</div>
              <div class="detail-value">${this.estimateTokens((log as any).request)}</div>
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
              <h3>Request</h3>
              ${this.renderRequestFields((log as any).request)}
            </div>
            
            <div class="detail-section ${this.collapsedSections.has('request-data') ? 'collapsed' : ''}">
              <h3 class="collapsible" @click=${() => this.toggleSection('request-data')}>
                <span class="expand-icon">▼</span> Raw Request Data
              </h3>
              <div class="detail-content">${JSON.stringify((log as any).request, null, 2)}</div>
            </div>
          ` : ''}
          
          ${(log as any).response ? html`
            <div class="detail-section ${this.collapsedSections.has('response-data') ? 'collapsed' : ''}">
              <h3 class="collapsible" @click=${() => this.toggleSection('response-data')}>
                <span class="expand-icon">▼</span> Raw Response Data
              </h3>
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
