import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { ClawLayerClient } from '../api/clawlayer-client';

@customElement('cl-config-editor')
export class ConfigEditor extends LitElement {
  static styles = css`
    :host { display: block; padding: 2rem; }
    h1 { margin: 0 0 2rem 0; color: #2c3e50; }
    .section { background: white; border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .section h2 { margin: 0 0 1rem 0; color: #34495e; font-size: 1.2rem; }
    .form-group { margin-bottom: 1rem; }
    .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
    label { display: block; margin-bottom: 0.25rem; font-weight: 500; color: #555; }
    input, select { width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
    input:focus, select:focus { outline: none; border-color: #3498db; }
    .provider-item { border: 1px solid #ecf0f1; border-radius: 4px; padding: 1rem; margin-bottom: 1rem; }
    .provider-header { display: flex; justify-content: between; align-items: center; margin-bottom: 1rem; }
    .provider-name { font-weight: 600; color: #2c3e50; }
    .remove-btn { background: #e74c3c; color: white; border: none; padding: 0.25rem 0.5rem; border-radius: 4px; cursor: pointer; font-size: 12px; }
    .add-btn { background: #27ae60; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; margin-top: 1rem; }
    .actions { margin-top: 2rem; display: flex; gap: 1rem; }
    button { padding: 0.75rem 1.5rem; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: 500; }
    .btn-primary { background: #3498db; color: white; }
    .btn-primary:hover { background: #2980b9; }
    .btn-secondary { background: #95a5a6; color: white; }
    .btn-secondary:hover { background: #7f8c8d; }
    .message { padding: 1rem; margin-top: 1rem; border-radius: 4px; }
    .message.success { background: #d4edda; color: #155724; }
    .message.error { background: #f8d7da; color: #721c24; }
    .checkbox { width: auto; margin-right: 0.5rem; }
  `;
  
  @state() config: any = {};
  @state() message = '';
  @state() messageType: 'success' | 'error' | '' = '';
  
  private client = new ClawLayerClient();
  
  async connectedCallback() {
    super.connectedCallback();
    await this.loadConfig();
  }
  
  async loadConfig() {
    try {
      this.config = await this.client.getConfig();
    } catch (e) {
      this.showMessage('Failed to load config', 'error');
    }
  }
  
  async save() {
    try {
      await this.client.saveConfig(this.config);
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
  
  updateProvider(name: string, field: string, value: any) {
    if (!this.config.providers) this.config.providers = {};
    if (!this.config.providers[name]) this.config.providers[name] = {};
    this.config.providers[name][field] = value;
    this.requestUpdate();
  }
  
  updateProviderModel(providerName: string, modelType: string, value: string) {
    if (!this.config.providers[providerName].models) {
      this.config.providers[providerName].models = {};
    }
    this.config.providers[providerName].models[modelType] = value;
    this.requestUpdate();
  }
  
  addProvider() {
    const name = prompt('Provider name:');
    if (name && !this.config.providers[name]) {
      this.config.providers[name] = {
        url: '',
        type: 'ollama',
        models: {}
      };
      this.requestUpdate();
    }
  }
  
  removeProvider(name: string) {
    if (confirm(`Remove provider "${name}"?`)) {
      delete this.config.providers[name];
      this.requestUpdate();
    }
  }
  
  updateDefault(field: string, value: string) {
    if (!this.config.defaults) this.config.defaults = {};
    this.config.defaults[field] = value;
    this.requestUpdate();
  }
  
  updateServer(field: string, value: any) {
    if (!this.config.server) this.config.server = {};
    this.config.server[field] = value;
    this.requestUpdate();
  }
  
  updateRouter(type: string, name: string, field: string, value: any) {
    if (!this.config.routers) this.config.routers = {};
    if (!this.config.routers[type]) this.config.routers[type] = {};
    if (!this.config.routers[type][name]) this.config.routers[type][name] = {};
    this.config.routers[type][name][field] = value;
    this.requestUpdate();
  }
  
  render() {
    const providers = this.config.providers || {};
    const defaults = this.config.defaults || {};
    const server = this.config.server || {};
    const routers = this.config.routers || {};
    
    return html`
      <h1>Configuration Editor</h1>
      
      <!-- Server Configuration -->
      <div class="section">
        <h2>Server</h2>
        <div class="form-group">
          <label>Port</label>
          <input type="number" .value=${server.port || 11435} 
                 @input=${(e: any) => this.updateServer('port', parseInt(e.target.value))}>
        </div>
      </div>
      
      <!-- Providers Configuration -->
      <div class="section">
        <h2>Providers</h2>
        ${Object.entries(providers).map(([name, provider]: [string, any]) => html`
          <div class="provider-item">
            <div class="provider-header">
              <span class="provider-name">${name}</span>
              <button class="remove-btn" @click=${() => this.removeProvider(name)}>Remove</button>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label>URL</label>
                <input .value=${provider.url || ''} 
                       @input=${(e: any) => this.updateProvider(name, 'url', e.target.value)}>
              </div>
              <div class="form-group">
                <label>Type</label>
                <select .value=${provider.type || 'ollama'} 
                        @change=${(e: any) => this.updateProvider(name, 'type', e.target.value)}>
                  <option value="ollama">Ollama</option>
                  <option value="openai">OpenAI</option>
                </select>
              </div>
            </div>
            
            <div class="form-group">
              <label>Models</label>
              <div class="form-row">
                <div>
                  <label>Text Model</label>
                  <input .value=${provider.models?.text || ''} 
                         @input=${(e: any) => this.updateProviderModel(name, 'text', e.target.value)}>
                </div>
                <div>
                  <label>Embed Model</label>
                  <input .value=${provider.models?.embed || ''} 
                         @input=${(e: any) => this.updateProviderModel(name, 'embed', e.target.value)}>
                </div>
              </div>
              <div class="form-row">
                <div>
                  <label>Vision Model</label>
                  <input .value=${provider.models?.vision || ''} 
                         @input=${(e: any) => this.updateProviderModel(name, 'vision', e.target.value)}>
                </div>
              </div>
            </div>
          </div>
        `)}
        <button class="add-btn" @click=${this.addProvider}>Add Provider</button>
      </div>
      
      <!-- Default Assignments -->
      <div class="section">
        <h2>Default Provider Assignments</h2>
        <div class="form-row">
          <div class="form-group">
            <label>Embedding Provider</label>
            <select .value=${defaults.embedding_provider || ''} 
                    @change=${(e: any) => this.updateDefault('embedding_provider', e.target.value)}>
              <option value="">Select...</option>
              ${Object.keys(providers).map(name => html`<option value="${name}">${name}</option>`)}
            </select>
          </div>
          <div class="form-group">
            <label>Text Provider</label>
            <select .value=${defaults.text_provider || ''} 
                    @change=${(e: any) => this.updateDefault('text_provider', e.target.value)}>
              <option value="">Select...</option>
              ${Object.keys(providers).map(name => html`<option value="${name}">${name}</option>`)}
            </select>
          </div>
        </div>
        <div class="form-group">
          <label>Vision Provider</label>
          <select .value=${defaults.vision_provider || ''} 
                  @change=${(e: any) => this.updateDefault('vision_provider', e.target.value)}>
            <option value="">Select...</option>
            ${Object.keys(providers).map(name => html`<option value="${name}">${name}</option>`)}
          </select>
        </div>
      </div>
      
      <!-- Router Configuration -->
      <div class="section">
        <h2>Routers</h2>
        
        <h3>Fast Routers</h3>
        ${['echo', 'command'].map(name => html`
          <div class="form-group">
            <label>
              <input type="checkbox" class="checkbox" 
                     .checked=${routers.fast?.[name]?.enabled !== false}
                     @change=${(e: any) => this.updateRouter('fast', name, 'enabled', e.target.checked)}>
              ${name} Router
            </label>
            ${name === 'command' ? html`
              <input placeholder="Command prefix (e.g., run:)" 
                     .value=${routers.fast?.command?.prefix || 'run:'}
                     @input=${(e: any) => this.updateRouter('fast', 'command', 'prefix', e.target.value)}>
            ` : ''}
          </div>
        `)}
        
        <h3>Semantic Routers</h3>
        ${['greeting', 'summarize'].map(name => html`
          <div class="form-group">
            <label>
              <input type="checkbox" class="checkbox" 
                     .checked=${routers.semantic?.[name]?.enabled !== false}
                     @change=${(e: any) => this.updateRouter('semantic', name, 'enabled', e.target.checked)}>
              ${name} Router
            </label>
            <select .value=${routers.semantic?.[name]?.provider || ''}
                    @change=${(e: any) => this.updateRouter('semantic', name, 'provider', e.target.value)}>
              <option value="">Select provider...</option>
              ${Object.keys(providers).map(pname => html`<option value="${pname}">${pname}</option>`)}
            </select>
          </div>
        `)}
      </div>
      
      <div class="actions">
        <button class="btn-primary" @click=${this.save}>Save Configuration</button>
        <button class="btn-secondary" @click=${this.loadConfig}>Reload</button>
      </div>
      
      ${this.message ? html`
        <div class="message ${this.messageType}">${this.message}</div>
      ` : ''}
    `;
  }
}
