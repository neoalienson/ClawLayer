import { LitElement, html, css, unsafeCSS } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { ClawLayerClient } from '../api/clawlayer-client';
import { renderHandlersTab } from './handlers-tab';
import { renderSemanticRoutersTab } from './semantic-routers-tab';
import { renderProvidersTab } from './providers-tab';
import { validateAndFixPriorities } from '../utils/config-validator';
import configEditorStyles from '../styles/config-editor.css?inline';

@customElement('cl-config-editor')
export class ConfigEditor extends LitElement {
  static styles = css`${unsafeCSS(configEditorStyles)}`;
  
  @state() config: any = {};
  @state() message = '';
  @state() messageType: 'success' | 'error' | '' = '';
  @state() viewMode: 'ui' | 'yaml' = 'ui';
  @state() yamlContent = '';
  @state() collapsedProviders: Set<string> = new Set();
  @state() activeTab: 'handlers' | 'semantic-routers' | 'providers' | 'system' = 'handlers';
  @state() routerSchemas: Record<string, any> = {};
  
  private client = new ClawLayerClient();
  
  async connectedCallback() {
    super.connectedCallback();
    await this.loadConfig();
  }
  
  async loadConfig() {
    try {
      this.config = await this.client.getConfig();
      validateAndFixPriorities(this.config);
      this.yamlContent = this.configToYaml(this.config);
      this.collapsedProviders = new Set(Object.keys(this.config.providers || {}));
      
      const schemasRes = await fetch('/api/router-schemas');
      this.routerSchemas = await schemasRes.json();
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
      validateAndFixPriorities(configToSave);
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
  
  toggleProvider(name: string) {
    if (this.collapsedProviders.has(name)) {
      this.collapsedProviders.delete(name);
    } else {
      this.collapsedProviders.add(name);
    }
    this.requestUpdate();
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
    if (type === 'handlers') {
      if (!this.config.handlers) this.config.handlers = {};
      if (!this.config.handlers[name]) this.config.handlers[name] = {};
      this.config.handlers[name][field] = value;
    } else {
      if (!this.config.routers) this.config.routers = {};
      if (!this.config.routers[type]) this.config.routers[type] = {};
      if (!this.config.routers[type][name]) this.config.routers[type][name] = {};
      this.config.routers[type][name][field] = value;
    }
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
  
  removeRouter(type: string, name: string) {
    if (confirm(`Delete router "${name}"?`)) {
      if (type === 'handlers') {
        delete this.config.handlers[name];
        const priority = this.config.handlers.priority || [];
        this.config.handlers.priority = priority.filter((n: string) => n !== name);
      } else {
        delete this.config.routers[type][name];
        const priority = this.config.routers[type].priority || [];
        this.config.routers[type].priority = priority.filter((n: string) => n !== name);
      }
      this.requestUpdate();
    }
  }
  
  moveRouter(type: string, index: number, direction: number) {
    const priority = type === 'handlers' 
      ? [...(this.config.handlers?.priority || [])]
      : [...(this.config.routers[type]?.priority || [])];
    const newIndex = index + direction;
    if (newIndex >= 0 && newIndex < priority.length) {
      [priority[index], priority[newIndex]] = [priority[newIndex], priority[index]];
      if (type === 'handlers') {
        if (!this.config.handlers) this.config.handlers = {};
        this.config.handlers.priority = priority;
      } else {
        if (!this.config.routers[type]) this.config.routers[type] = {};
        this.config.routers[type].priority = priority;
      }
      this.requestUpdate();
    }
  }
  
  addHandler() {
    const name = prompt('Router name:');
    if (name) {
      if (!this.config.handlers) this.config.handlers = { priority: [] };
      this.config.handlers.priority.push(name);
      this.config.handlers[name] = { enabled: true };
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
    // Ensure stages is an array
    if (!Array.isArray(this.config.routers.semantic[routerName].stages)) {
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
    if (type === 'handlers') {
      delete this.config.handlers[routerName][key];
    } else {
      delete this.config.routers[type][routerName][key];
    }
    this.requestUpdate();
  }
  
  inferPropertyType(routerName: string, propKey: string, value: any): string {
    const schema = this.routerSchemas[routerName]?.[propKey];
    if (schema?.type === 'array' && schema?.items?.type === 'object') {
      return 'structured-array';
    }
    if (Array.isArray(value)) {
      return 'array';
    }
    if (typeof value === 'object' && value !== null) {
      return 'object';
    }
    return 'primitive';
  }
  
  addArrayItem(type: string, routerName: string, key: string, template: any) {
    const router = type === 'handlers' ? this.config.handlers[routerName] : this.config.routers[type][routerName];
    const currentValue = router[key];
    if (!Array.isArray(currentValue)) {
      router[key] = [];
    }
    router[key].push(template);
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
      const priority = type === 'handlers'
        ? [...(this.config.handlers?.priority || [])]
        : [...(this.config.routers[type]?.priority || [])];
      const [moved] = priority.splice(dragIndex, 1);
      priority.splice(dropIndex, 0, moved);
      
      if (type === 'handlers') {
        if (!this.config.handlers) this.config.handlers = {};
        this.config.handlers.priority = priority;
      } else {
        if (!this.config.routers[type]) this.config.routers[type] = {};
        this.config.routers[type].priority = priority;
      }
      this.requestUpdate();
    }
  }
  
  switchView(mode: 'ui' | 'yaml') {
    if (mode === 'yaml' && this.viewMode === 'ui') {
      this.yamlContent = this.configToYaml(this.config);
    } else if (mode === 'ui' && this.viewMode === 'yaml') {
      // Reload config from server instead of parsing YAML
      // This ensures we get the correct structure
      this.loadConfig();
      this.viewMode = mode;
      return;
    }
    this.viewMode = mode;
    this.requestUpdate();
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
    if (!this.config) {
      return html`<div>Loading configuration...</div>`;
    }
    
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
      
      ${this.viewMode === 'ui' ? html`
        <div class="tabs">
          <button class="tab ${this.activeTab === 'handlers' ? 'active' : ''}" 
                  @click=${() => this.activeTab = 'handlers'}>Handlers</button>
          <button class="tab ${this.activeTab === 'semantic-routers' ? 'active' : ''}" 
                  @click=${() => this.activeTab = 'semantic-routers'}>Semantic Routers</button>
          <button class="tab ${this.activeTab === 'providers' ? 'active' : ''}" 
                  @click=${() => this.activeTab = 'providers'}>Providers</button>
          <button class="tab ${this.activeTab === 'system' ? 'active' : ''}" 
                  @click=${() => this.activeTab = 'system'}>System</button>
        </div>
      ` : ''}
      
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
    if (this.activeTab === 'handlers') {
      return renderHandlersTab(this.config, this);
    } else if (this.activeTab === 'semantic-routers') {
      return renderSemanticRoutersTab(this.config, this);
    } else if (this.activeTab === 'providers') {
      return renderProvidersTab(this.config, this);
    } else {
      return this.renderSystemTab();
    }
  }
  
  renderSystemTab() {
    const server = this.config.server || {};
    return html`
      <div class="section">
        <h2>Server Configuration</h2>
        <div class="form-group">
          <label>Port</label>
          <input type="number" .value=${server.port || 11435} 
                 @input=${(e: any) => this.updateServer('port', parseInt(e.target.value))}>
        </div>
      </div>
    `;
  }
  

  

  

}
