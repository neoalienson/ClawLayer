import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { ClawLayerClient } from '../api/clawlayer-client';

@customElement('cl-config-editor')
export class ConfigEditor extends LitElement {
  static styles = css`
    :host { display: block; padding: 2rem; }
    h1 { margin: 0 0 1rem 0; color: #2c3e50; }
    textarea { width: 100%; height: 500px; font-family: 'Courier New', monospace; font-size: 14px; padding: 1rem; border: 1px solid #ddd; border-radius: 4px; }
    .actions { margin-top: 1rem; display: flex; gap: 1rem; }
    button { padding: 0.75rem 1.5rem; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: 500; }
    .btn-primary { background: #3498db; color: white; }
    .btn-primary:hover { background: #2980b9; }
    .btn-secondary { background: #95a5a6; color: white; }
    .btn-secondary:hover { background: #7f8c8d; }
    .message { padding: 1rem; margin-top: 1rem; border-radius: 4px; }
    .message.success { background: #d4edda; color: #155724; }
    .message.error { background: #f8d7da; color: #721c24; }
  `;
  
  @state() config = '';
  @state() message = '';
  @state() messageType: 'success' | 'error' | '' = '';
  
  private client = new ClawLayerClient();
  
  async connectedCallback() {
    super.connectedCallback();
    await this.loadConfig();
  }
  
  async loadConfig() {
    try {
      const cfg = await this.client.getConfig();
      this.config = JSON.stringify(cfg, null, 2);
    } catch (e) {
      this.showMessage('Failed to load config', 'error');
    }
  }
  
  async save() {
    try {
      const cfg = JSON.parse(this.config);
      await this.client.saveConfig(cfg);
      this.showMessage('Config saved! Restart ClawLayer to apply changes.', 'success');
    } catch (e: any) {
      this.showMessage(`Error: ${e.message}`, 'error');
    }
  }
  
  showMessage(msg: string, type: 'success' | 'error') {
    this.message = msg;
    this.messageType = type;
    setTimeout(() => {
      this.message = '';
      this.messageType = '';
    }, 5000);
  }
  
  render() {
    return html`
      <h1>Configuration Editor</h1>
      <textarea .value=${this.config} @input=${(e: any) => this.config = e.target.value}></textarea>
      <div class="actions">
        <button class="btn-primary" @click=${this.save}>Save Config</button>
        <button class="btn-secondary" @click=${this.loadConfig}>Reload</button>
      </div>
      ${this.message ? html`
        <div class="message ${this.messageType}">${this.message}</div>
      ` : ''}
    `;
  }
}
