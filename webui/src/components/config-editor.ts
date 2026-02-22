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
    input, select, textarea { width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; box-sizing: border-box; }
    input:focus, select:focus { outline: none; border-color: #3498db; }
    .provider-item { border: 1px solid #ecf0f1; border-radius: 4px; padding: 1rem; margin-bottom: 1rem; }
    .provider-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
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
    .draggable { cursor: grab; padding: 0.5rem; margin: 0.25rem 0; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; }
    .draggable:hover { background: #e9ecef; }
    .draggable.dragging { opacity: 0.5; }
    .drop-zone { min-height: 2rem; border: 2px dashed #dee2e6; border-radius: 4px; margin: 0.5rem 0; }
    .drop-zone.drag-over { border-color: #007bff; background: #f8f9fa; }
    .router-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
    .stage-card { background: #fff; border: 1px solid #e9ecef; border-radius: 4px; padding: 0.75rem; margin: 0.5rem 0; }
    .stage-row { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.5rem; align-items: end; }
    .provider-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }
    .provider-models { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.5rem; }
    @media (max-width: 768px) { 
      .stage-row { grid-template-columns: 1fr; }
      .provider-row { grid-template-columns: 1fr; }
      .provider-models { grid-template-columns: 1fr; }
    }
    .router-controls { display: flex; gap: 0.5rem; align-items: center; }
    .checkbox { width: auto; margin-right: 0.5rem; }
    .view-toggle { display: flex; gap: 0.5rem; margin-bottom: 2rem; }
    .toggle-btn { padding: 0.5rem 1rem; border: 1px solid #ddd; background: white; cursor: pointer; border-radius: 4px; }
    .toggle-btn.active { background: #3498db; color: white; border-color: #3498db; }
    .yaml-editor { width: 100%; height: 500px; font-family: 'Courier New', monospace; font-size: 14px; padding: 1rem; border: 1px solid #ddd; border-radius: 4px; }
  `;
  
  @state() config: any = {};
  @state() message = '';
  @state() messageType: 'success' | 'error' | '' = '';
  @state() viewMode: 'ui' | 'yaml' = 'ui';
  @state() yamlContent = '';
  
  private client = new ClawLayerClient();
  
  async connectedCallback() {
    super.connectedCallback();
    await this.loadConfig();
  }
  
  async loadConfig() {
    try {
      this.config = await this.client.getConfig();
      this.yamlContent = this.configToYaml(this.config);
    } catch (e) {
      this.showMessage('Failed to load config', 'error');
    }
  }
  
  async save() {
    try {
      let configToSave = this.config;
      if (this.viewMode === 'yaml') {
        configToSave = this.yamlToConfig(this.yamlContent);
      }
      await this.client.saveConfig(configToSave);
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
  
  updateProviderCapability(providerName: string, capType: string, value: any) {
    if (!this.config.providers[providerName].capabilities) {
      this.config.providers[providerName].capabilities = {};
    }
    this.config.providers[providerName].capabilities[capType] = value;
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
  
  updateStage(routerName: string, stageIndex: number, field: string, value: any) {
    if (!this.config.routers.semantic[routerName].stages) {
      this.config.routers.semantic[routerName].stages = [];
    }
    if (!this.config.routers.semantic[routerName].stages[stageIndex]) {
      this.config.routers.semantic[routerName].stages[stageIndex] = {};
    }
    this.config.routers.semantic[routerName].stages[stageIndex][field] = value;
    this.requestUpdate();
  }
  
  updateUtterances(routerName: string, value: string) {
    this.config.routers.semantic[routerName].utterances = value.split('\n').filter(u => u.trim());
    this.requestUpdate();
  }
  
  moveRouter(type: string, index: number, direction: number) {
    const priority = [...(this.config.routers[type]?.priority || [])];
    const newIndex = index + direction;
    if (newIndex >= 0 && newIndex < priority.length) {
      [priority[index], priority[newIndex]] = [priority[newIndex], priority[index]];
      if (!this.config.routers[type]) this.config.routers[type] = {};
      this.config.routers[type].priority = priority;
      this.requestUpdate();
    }
  }
  
  addFastRouter() {
    const name = prompt('Router name:');
    if (name) {
      if (!this.config.routers.fast) this.config.routers.fast = { priority: [] };
      this.config.routers.fast.priority.push(name);
      this.config.routers.fast[name] = { enabled: true };
      this.requestUpdate();
    }
  }
  
  addSemanticRouter() {
    const name = prompt('Router name:');
    if (name) {
      if (!this.config.routers.semantic) this.config.routers.semantic = { priority: [] };
      this.config.routers.semantic.priority.push(name);
      this.config.routers.semantic[name] = {
        enabled: true,
        stages: [{ provider: '', model: '', threshold: 0.7 }],
        utterances: []
      };
      this.requestUpdate();
    }
  }
  
  addStage(routerName: string) {
    if (!this.config.routers.semantic[routerName].stages) {
      this.config.routers.semantic[routerName].stages = [];
    }
    this.config.routers.semantic[routerName].stages.push({
      provider: '',
      model: '',
      threshold: 0.7
    });
    this.requestUpdate();
  }
  
  removeStage(routerName: string, stageIndex: number) {
    this.config.routers.semantic[routerName].stages.splice(stageIndex, 1);
    this.requestUpdate();
  }
  
  addRouterProperty(type: string, routerName: string) {
    const key = prompt('Property name:');
    if (key) {
      const value = prompt('Property value:') || '';
      this.updateRouter(type, routerName, key, value);
    }
  }
  
  removeRouterProperty(type: string, routerName: string, key: string) {
    delete this.config.routers[type][routerName][key];
    this.requestUpdate();
  }
  
  handleDragStart(e: DragEvent, type: string, index: number) {
    e.dataTransfer!.setData('text/plain', `${type}:${index}`);
  }
  
  handleDrop(e: DragEvent, type: string, dropIndex: number) {
    e.preventDefault();
    const data = e.dataTransfer!.getData('text/plain');
    const [dragType, dragIndexStr] = data.split(':');
    const dragIndex = parseInt(dragIndexStr);
    
    if (dragType === type && dragIndex !== dropIndex) {
      const priority = [...(this.config.routers[type]?.priority || [])];
      const [moved] = priority.splice(dragIndex, 1);
      priority.splice(dropIndex, 0, moved);
      
      if (!this.config.routers[type]) this.config.routers[type] = {};
      this.config.routers[type].priority = priority;
      this.requestUpdate();
    }
  }
  
  switchView(mode: 'ui' | 'yaml') {
    if (mode === 'yaml' && this.viewMode === 'ui') {
      this.yamlContent = this.configToYaml(this.config);
    } else if (mode === 'ui' && this.viewMode === 'yaml') {
      try {
        this.config = this.yamlToConfig(this.yamlContent);
      } catch (e) {
        this.showMessage('Invalid YAML format', 'error');
        return;
      }
    }
    this.viewMode = mode;
    this.requestUpdate(); // Force re-render
  }
  
  configToYaml(config: any): string {
    return this.objectToYaml(config, 0);
  }
  
  objectToYaml(obj: any, indent: number): string {
    const spaces = '  '.repeat(indent);
    const lines: string[] = [];
    
    Object.entries(obj).forEach(([key, value]) => {
      if (value === null || value === undefined) {
        lines.push(`${spaces}${key}: null`);
      } else if (Array.isArray(value)) {
        lines.push(`${spaces}${key}:`);
        value.forEach(item => {
          if (typeof item === 'object') {
            lines.push(`${spaces}  -`);
            lines.push(this.objectToYaml(item, indent + 2).replace(/^  /, '    '));
          } else {
            lines.push(`${spaces}  - ${item}`);
          }
        });
      } else if (typeof value === 'object') {
        lines.push(`${spaces}${key}:`);
        lines.push(this.objectToYaml(value, indent + 1));
      } else {
        lines.push(`${spaces}${key}: ${value}`);
      }
    });
    
    return lines.join('\n');
  }
  
  yamlToConfig(yaml: string): any {
    // Simple YAML parser for basic config structure
    const lines = yaml.split('\n');
    const config: any = {};
    let currentSection: any = config;
    let sectionStack: any[] = [config];
    
    lines.forEach(line => {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) return;
      
      const indent = line.length - line.trimStart().length;
      const level = Math.floor(indent / 2);
      
      // Adjust section stack based on indentation
      while (sectionStack.length > level + 1) {
        sectionStack.pop();
      }
      currentSection = sectionStack[sectionStack.length - 1];
      
      if (trimmed.includes(':')) {
        const [key, ...valueParts] = trimmed.split(':');
        const value = valueParts.join(':').trim();
        
        if (value) {
          // Parse value
          if (value === 'true') currentSection[key] = true;
          else if (value === 'false') currentSection[key] = false;
          else if (!isNaN(Number(value))) currentSection[key] = Number(value);
          else currentSection[key] = value;
        } else {
          // New section
          currentSection[key] = {};
          sectionStack.push(currentSection[key]);
        }
      }
    });
    
    return config;
  }
  
  render() {
    const providers = this.config.providers || {};
    const defaults = this.config.defaults || {};
    const server = this.config.server || {};
    const routers = this.config.routers || {};
    
    return html`
      <h1>Configuration Editor</h1>
      
      <div class="view-toggle">
        <button class="toggle-btn ${this.viewMode === 'ui' ? 'active' : ''}" 
                @click=${() => this.switchView('ui')}>UI Editor</button>
        <button class="toggle-btn ${this.viewMode === 'yaml' ? 'active' : ''}" 
                @click=${() => this.switchView('yaml')}>YAML Editor</button>
      </div>
      
      ${this.viewMode === 'ui' ? this.renderUIEditor() : this.renderYAMLEditor()}
      
      <div class="actions">
        <button class="btn-primary" @click=${this.save}>Save Configuration</button>
        <button class="btn-secondary" @click=${this.loadConfig}>Reload</button>
      </div>
      
      ${this.message ? html`
        <div class="message ${this.messageType}">${this.message}</div>
      ` : ''}
    `;
  }
  
  renderYAMLEditor() {
    return html`
      <textarea class="yaml-editor" 
                .value=${this.yamlContent} 
                @input=${(e: any) => this.yamlContent = e.target.value}
                placeholder="Enter YAML configuration..."></textarea>
    `;
  }
  
  renderUIEditor() {
    const providers = this.config.providers || {};
    const defaults = this.config.defaults || {};
    const server = this.config.server || {};
    const routers = this.config.routers || {};
    
    console.log('Defaults:', defaults); // Debug log
    
    return html`
      
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
            
            <div class="provider-row">
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
              <label>Provider Type</label>
              <select .value=${provider.provider_type || 'embedding'} 
                      @change=${(e: any) => this.updateProvider(name, 'provider_type', e.target.value)}>
                <option value="embedding">Embedding</option>
                <option value="llm">LLM</option>
              </select>
            </div>
            
            <div class="form-group">
              <label>Models</label>
              <div class="provider-models">
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
                <div>
                  <label>Vision Model</label>
                  <input .value=${provider.models?.vision || ''} 
                         @input=${(e: any) => this.updateProviderModel(name, 'vision', e.target.value)}>
                </div>
              </div>
            </div>
            
            ${provider.capabilities ? html`
              <div class="form-group">
                <label>Capabilities</label>
                <div class="form-row">
                  <div>
                    <label>Max Context</label>
                    <input type="number" .value=${provider.capabilities.max_context || ''} 
                           @input=${(e: any) => this.updateProviderCapability(name, 'max_context', parseInt(e.target.value))}>
                  </div>
                  <div>
                    <label>
                      <input type="checkbox" class="checkbox" 
                             .checked=${provider.capabilities.tool_use || false}
                             @change=${(e: any) => this.updateProviderCapability(name, 'tool_use', e.target.checked)}>
                      Tool Use
                    </label>
                  </div>
                </div>
              </div>
            ` : ''}
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
            <select @change=${(e: any) => this.updateDefault('embedding_provider', e.target.value)}>
              <option value="">Select...</option>
              ${Object.keys(providers).map(name => html`<option value="${name}" ?selected=${defaults.embedding_provider === name}>${name}</option>`)}
            </select>
          </div>
          <div class="form-group">
            <label>Text Provider</label>
            <select @change=${(e: any) => this.updateDefault('text_provider', e.target.value)}>
              <option value="">Select...</option>
              ${Object.keys(providers).map(name => html`<option value="${name}" ?selected=${defaults.text_provider === name}>${name}</option>`)}
            </select>
          </div>
        </div>
        <div class="form-group">
          <label>Vision Provider</label>
          <select @change=${(e: any) => this.updateDefault('vision_provider', e.target.value)}>
            <option value="">Select...</option>
            ${Object.keys(providers).map(name => html`<option value="${name}" ?selected=${defaults.vision_provider === name}>${name}</option>`)}
          </select>
        </div>
      </div>
      
      <!-- Router Configuration -->
      <div class="section">
        <h2>Routers</h2>
        
        <h3>Fast Routers</h3>
        <div class="router-priority">
          ${(Array.isArray(routers.fast?.priority) ? routers.fast.priority : ['echo', 'command']).map((name: string, index: number) => html`
            <div class="draggable">
              <div class="router-header">
                <span>📋 ${name} Router</span>
                <div class="router-controls">
                  <button class="move-btn" ?disabled=${index === 0} @click=${() => this.moveRouter('fast', index, -1)}>↑</button>
                  <button class="move-btn" ?disabled=${index === (Array.isArray(routers.fast?.priority) ? routers.fast.priority : ['echo', 'command']).length - 1} @click=${() => this.moveRouter('fast', index, 1)}>↓</button>
                  <label>
                    <input type="checkbox" class="checkbox" 
                           .checked=${routers.fast?.[name]?.enabled !== false}
                           @change=${(e: any) => this.updateRouter('fast', name, 'enabled', e.target.checked)}>
                    Enabled
                  </label>
                </div>
              </div>
              <div>
                <h4>Properties</h4>
                ${Object.entries(routers.fast?.[name] || {}).filter(([key]) => key !== 'enabled').map(([key, value]) => html`
                  <div class="form-group">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                      <label>${key}</label>
                      <button class="remove-btn" @click=${() => this.removeRouterProperty('fast', name, key)}>Remove</button>
                    </div>
                    <input .value=${value || ''} 
                           @input=${(e: any) => this.updateRouter('fast', name, key, e.target.value)}>
                  </div>
                `)}
                <button class="add-btn" @click=${() => this.addRouterProperty('fast', name)}>Add Property</button>
              </div>
            </div>
          `)}}
        </div>
        <button class="add-btn" @click=${this.addFastRouter}>Add Fast Router</button>
        
        <h3>Semantic Routers</h3>
        <div class="router-priority">
          ${(Array.isArray(routers.semantic?.priority) ? routers.semantic.priority : ['greeting', 'summarize']).map((name: string, index: number) => html`
            <div class="draggable">
              <div class="router-header">
                <span>🧠 ${name} Router</span>
                <div class="router-controls">
                  <button class="move-btn" ?disabled=${index === 0} @click=${() => this.moveRouter('semantic', index, -1)}>↑</button>
                  <button class="move-btn" ?disabled=${index === (Array.isArray(routers.semantic?.priority) ? routers.semantic.priority : ['greeting', 'summarize']).length - 1} @click=${() => this.moveRouter('semantic', index, 1)}>↓</button>
                  <label>
                    <input type="checkbox" class="checkbox" 
                           .checked=${routers.semantic?.[name]?.enabled !== false}
                           @change=${(e: any) => this.updateRouter('semantic', name, 'enabled', e.target.checked)}>
                    Enabled
                  </label>
                </div>
              </div>
              
              <div>
                <h4>Stages</h4>
                ${(Array.isArray(routers.semantic?.[name]?.stages) ? routers.semantic[name].stages : []).map((stage: any, i: number) => html`
                  <div class="stage-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                      <span>Stage ${i + 1}</span>
                      <button class="remove-btn" @click=${() => this.removeStage(name, i)}>Remove</button>
                    </div>
                    <div class="stage-row">
                      <div>
                        <label>Provider</label>
                        <select @change=${(e: any) => this.updateStage(name, i, 'provider', e.target.value)}>
                          <option value="">Select...</option>
                          ${Object.keys(providers).map(pname => html`<option value="${pname}" ?selected=${stage.provider === pname}>${pname}</option>`)}
                        </select>
                      </div>
                      <div>
                        <label>Model</label>
                        <input placeholder="Model" .value=${stage.model || ''} 
                               @input=${(e: any) => this.updateStage(name, i, 'model', e.target.value)}>
                      </div>
                      <div>
                        <label>Threshold: ${stage.threshold || 0}</label>
                        <input type="range" min="0" max="1" step="0.1" .value=${stage.threshold || 0} 
                               @input=${(e: any) => this.updateStage(name, i, 'threshold', parseFloat(e.target.value))}>
                      </div>
                    </div>
                  </div>
                `)}
                <button class="add-btn" @click=${() => this.addStage(name)}>Add Stage</button>
                
                <h4>Utterances</h4>
                <textarea .value=${(Array.isArray(routers.semantic?.[name]?.utterances) ? routers.semantic[name].utterances : []).join('\n')} 
                          @input=${(e: any) => this.updateUtterances(name, e.target.value)}
                          placeholder="One utterance per line"></textarea>
              </div>
            </div>
          `)}
        </div>
        <button class="add-btn" @click=${this.addSemanticRouter}>Add Semantic Router</button>
      </div>
    `;
  }
}
