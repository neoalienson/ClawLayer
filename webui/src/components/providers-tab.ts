import { html } from 'lit';

export function renderProvidersTab(config: any, handlers: any) {
  const providers = config.providers || {};
  const defaults = config.defaults || {};
  
  return html`
    <div class="section">
      <h2>Providers</h2>
      ${Object.entries(providers).map(([name, provider]: [string, any]) => 
        renderProviderItem(name, provider, handlers)
      )}
      <button class="add-btn" @click=${handlers.addProvider}>Add Provider</button>
    </div>
    
    <div class="section">
      <h2>Default Provider Assignments</h2>
      <div class="form-row">
        <div class="form-group">
          <label>Embedding Provider</label>
          <select @change=${(e: any) => handlers.updateDefault('embedding_provider', e.target.value)}>
            <option value="">Select...</option>
            ${Object.keys(providers).map(name => html`<option value="${name}" ?selected=${defaults.embedding_provider === name}>${name}</option>`)}
          </select>
        </div>
        <div class="form-group">
          <label>Text Provider</label>
          <select @change=${(e: any) => handlers.updateDefault('text_provider', e.target.value)}>
            <option value="">Select...</option>
            ${Object.keys(providers).map(name => html`<option value="${name}" ?selected=${defaults.text_provider === name}>${name}</option>`)}
          </select>
        </div>
      </div>
      <div class="form-group">
        <label>Vision Provider</label>
        <select @change=${(e: any) => handlers.updateDefault('vision_provider', e.target.value)}>
          <option value="">Select...</option>
          ${Object.keys(providers).map(name => html`<option value="${name}" ?selected=${defaults.vision_provider === name}>${name}</option>`)}
        </select>
      </div>
    </div>
  `;
}

function renderProviderItem(name: string, provider: any, handlers: any) {
  const isCollapsed = handlers.collapsedProviders.has(name);
  
  return html`
    <div class="provider-item">
      <div class="provider-header" @click=${() => handlers.toggleProvider(name)}>
        <span class="provider-name">
          <span class="collapse-icon ${isCollapsed ? 'collapsed' : ''}">▼</span>
          ${name}
        </span>
      </div>
      
      <div class="provider-content ${isCollapsed ? 'collapsed' : ''}">
        <div style="display: flex; justify-content: flex-end; margin-bottom: 1rem;">
          <button class="remove-btn" @click=${() => handlers.removeProvider(name)}>Remove Provider</button>
        </div>
        ${renderProviderFields(name, provider, handlers)}
      </div>
    </div>
  `;
}

function renderProviderFields(name: string, provider: any, handlers: any) {
  return html`
    <div class="provider-row">
      <div class="form-group">
        <label>URL</label>
        <input .value=${provider.url || ''} 
               @input=${(e: any) => handlers.updateProvider(name, 'url', e.target.value)}>
      </div>
      <div class="form-group">
        <label>API Key</label>
        <input type="password" .value=${provider.api_key || ''} 
               placeholder="Optional" 
               @input=${(e: any) => handlers.updateProvider(name, 'api_key', e.target.value)}>
      </div>
    </div>
    
    <div class="provider-row">
      <div class="form-group">
        <label>Type</label>
        <select .value=${provider.type || 'ollama'} 
                @change=${(e: any) => handlers.updateProvider(name, 'type', e.target.value)}>
          <option value="ollama">Ollama</option>
          <option value="openai">OpenAI</option>
        </select>
      </div>
      <div class="form-group">
        <label>Provider Type</label>
        <select .value=${provider.provider_type || 'embedding'} 
                @change=${(e: any) => handlers.updateProvider(name, 'provider_type', e.target.value)}>
          <option value="embedding">Embedding</option>
          <option value="llm">LLM</option>
        </select>
      </div>
    </div>
    
    <div class="form-group">
      <label>Models</label>
      <div class="provider-models">
        <div>
          <label>Text Model</label>
          <input .value=${provider.models?.text || ''} 
                 @input=${(e: any) => handlers.updateProviderModel(name, 'text', e.target.value)}>
        </div>
        <div>
          <label>Embed Model</label>
          <input .value=${provider.models?.embed || ''} 
                 @input=${(e: any) => handlers.updateProviderModel(name, 'embed', e.target.value)}>
        </div>
        <div>
          <label>Vision Model</label>
          <input .value=${provider.models?.vision || ''} 
                 @input=${(e: any) => handlers.updateProviderModel(name, 'vision', e.target.value)}>
        </div>
      </div>
    </div>
    
    ${provider.capabilities ? html`
      <div class="form-group">
        <label>Capabilities</label>
        <div class="form-row">
          <div>
            <label>Context Window</label>
            <input type="number" .value=${provider.capabilities.max_context || ''} 
                   placeholder="e.g. 131072"
                   @input=${(e: any) => handlers.updateProviderCapability(name, 'max_context', parseInt(e.target.value))}>
          </div>
          <div>
            <label>
              <input type="checkbox" class="checkbox" 
                     .checked=${provider.capabilities.tool_use || false}
                     @change=${(e: any) => handlers.updateProviderCapability(name, 'tool_use', e.target.checked)}>
              Tool Use
            </label>
          </div>
        </div>
      </div>
    ` : html`
      <div class="form-group">
        <label>Context Window</label>
        <input type="number" .value=${''} 
               placeholder="e.g. 131072 (optional)"
               @input=${(e: any) => handlers.updateProviderCapability(name, 'max_context', parseInt(e.target.value))}>
      </div>
    `}
  `;
}
