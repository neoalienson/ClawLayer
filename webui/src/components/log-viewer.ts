import { LitElement, html, css, unsafeCSS } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { ClawLayerClient, Log } from '../api/clawlayer-client';
import logViewerStyles from '../styles/log-viewer.css?inline';

@customElement('cl-log-viewer')
export class LogViewer extends LitElement {
  static styles = css`${unsafeCSS(logViewerStyles)}`;
  
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
    // Collapse tried routers and all router stages by default
    this.collapsedSections.add('tried-routers');
    if ((log as any).tried_routers) {
      (log as any).tried_routers.forEach((_: any, i: number) => {
        this.collapsedSections.add(`router-${i}-stages`);
        this.collapsedSections.add(`router-${i}-data`);
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
  
  getRouterStageData(log: any, routerIndex: number): any[] {
    console.log('Getting stage data for router', routerIndex, 'log.stage_data:', log.stage_data);
    // Extract stage data from the successful router's result
    if (log.stage_data && Array.isArray(log.stage_data)) {
      return log.stage_data;
    }
    return [];
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
              
              ${(log as any).tried_routers ? html`
                <div class="detail-label">Tried Routers:</div>
                <div class="detail-value">
                  <div class="section-header" @click=${() => this.toggleSection('tried-routers')}>
                    <span class="expand-icon">${this.collapsedSections.has('tried-routers') ? '▶' : '▼'}</span> 
                    ${(log as any).tried_routers.length} router(s) tried
                  </div>
                  ${this.collapsedSections.has('tried-routers') ? html`
                    <div class="message-preview">
                      ${(log as any).tried_routers.map((r: any) => typeof r === 'string' ? r : r.name).join(' → ')}
                    </div>
                  ` : html`
                    <div class="router-details">
                      ${(log as any).tried_routers.map((router: any, i: number) => {
                        const routerName = typeof router === 'string' ? router : (router.name || router.router_name || 'unknown');
                        const routerData = typeof router === 'object' ? router : null;
                        const stageData = routerData?.stage_data || [];
                        return html`
                        <div class="router-step">
                          <strong>${i + 1}. ${routerName.split('[')[0].trim()}</strong>
                          ${stageData.length > 0 ? html`
                            <div class="stage-info">
                              <div class="section-header" @click=${() => this.toggleSection(`router-${i}-stages`)}>
                                <span class="expand-icon">${this.collapsedSections.has(`router-${i}-stages`) ? '▶' : '▼'}</span>
                                ${stageData.length} stage(s)
                              </div>
                              ${!this.collapsedSections.has(`router-${i}-stages`) ? html`
                                <div class="stage-requests">
                                  ${stageData.map((stage: any) => html`
                                    <div class="stage-request">
                                      <div class="stage-header">
                                        <strong>Stage ${stage.stage} (${stage.type})</strong>
                                        ${stage.latency_ms ? html`<span class="stage-timing">${stage.latency_ms}ms</span>` : ''}
                                        ${stage.model ? html`<span class="stage-model">${stage.model}</span>` : ''}
                                      </div>
                                      ${stage.confidence !== undefined ? html`
                                        <div style="font-size: 11px; color: #7f8c8d; margin-top: 0.25rem;">
                                          Confidence: ${stage.confidence.toFixed(3)} / Threshold: ${stage.threshold} → ${stage.result}
                                        </div>
                                      ` : stage.result ? html`
                                        <div style="font-size: 11px; color: #7f8c8d; margin-top: 0.25rem;">
                                          ${stage.result}
                                        </div>
                                      ` : ''}
                                      
                                      ${stage.type === 'LLM' && stage.request ? html`
                                        <div class="request-section">
                                          <strong>LLM Classification Request:</strong>
                                          <pre class="request-json">${JSON.stringify(stage.request, null, 2)}</pre>
                                        </div>
                                      ` : ''}
                                      
                                      ${stage.type === 'LLM' && stage.response ? html`
                                        <div class="response-section">
                                          <strong>LLM Classification Response:</strong>
                                          <pre class="request-json">${JSON.stringify(stage.response, null, 2)}</pre>
                                        </div>
                                      ` : ''}
                                      
                                      ${stage.error ? html`
                                        <div class="error-section">
                                          <strong>Error:</strong>
                                          <pre class="error-text">${stage.error}</pre>
                                        </div>
                                      ` : ''}
                                    </div>
                                  `)}
                                </div>
                              ` : ''}
                            </div>
                          ` : ''}
                          ${routerData && (routerName.includes('llm_fallback') || routerData.name === 'llm_fallback') ? html`
                            <div class="stage-info">
                              <div class="section-header" @click=${() => this.toggleSection(`router-${i}-data`)}>
                                <span class="expand-icon">${this.collapsedSections.has(`router-${i}-data`) ? '▶' : '▼'}</span>
                                Request/Response
                              </div>
                              ${!this.collapsedSections.has(`router-${i}-data`) ? html`
                                <div class="stage-requests">
                                  ${routerData.request ? html`
                                    <div class="request-section">
                                      <strong>Request:</strong>
                                      <pre class="request-json">${JSON.stringify(routerData.request, null, 2)}</pre>
                                    </div>
                                  ` : ''}
                                  ${routerData.response ? html`
                                    <div class="response-section">
                                      <strong>Response:</strong>
                                      ${routerData.response.combined_content ? html`
                                        <div class="detail-content" style="background: #f8f9fa; padding: 0.5rem; margin-top: 0.5rem;">
                                          ${routerData.response.combined_content}
                                        </div>
                                        ${routerData.response.chunks ? html`
                                          <details style="margin-top: 0.5rem;">
                                            <summary style="cursor: pointer; color: #7f8c8d; font-size: 11px;">Show raw chunks (${routerData.response.chunks.length})</summary>
                                            <pre class="request-json">${JSON.stringify(routerData.response.chunks, null, 2)}</pre>
                                          </details>
                                        ` : ''}
                                      ` : html`
                                        <pre class="request-json">${JSON.stringify(routerData.response, null, 2)}</pre>
                                      `}
                                    </div>
                                  ` : ''}
                                </div>
                              ` : ''}
                            </div>
                          ` : ''}
                        </div>
                      `})}
                    </div>
                  `}
                </div>
              ` : ''}
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
  
  async deleteLog(logId: number, event: Event) {
    event.stopPropagation();
    try {
      const response = await fetch(`/api/logs/${logId}`, { method: 'DELETE' });
      if (response.ok) {
        this.logs = this.logs.filter(log => (log as any).id !== logId);
      }
    } catch (e) {
      console.error('Failed to delete log:', e);
    }
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
            <button class="delete-btn" @click=${(e: Event) => this.deleteLog((log as any).id, e)}>×</button>
          </div>
        `)}}
      </div>
      ${this.renderModal()}
    `;
  }
}
