import { html } from 'lit';

export function renderHandlersTab(config: any, handlers: any) {
  const handlersConfig = config.handlers || {};
  const priority = Array.isArray(handlersConfig.priority) ? handlersConfig.priority : [];
  
  return html`
    <div class="section">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
        <h2 style="margin: 0;">Handlers</h2>
        <button class="add-btn" style="margin: 0;" @click=${handlers.addHandler}>Add Handler</button>
      </div>
      <div class="router-priority">
        ${priority.map((name: string, index: number) => html`
          <div class="draggable">
            <div class="router-header">
              <span>📋 ${name}</span>
              <div class="router-controls">
                <button class="remove-btn" @click=${() => handlers.removeRouter('handlers', name)}>Delete</button>
                <button class="move-btn" ?disabled=${index === 0} @click=${() => handlers.moveRouter('handlers', index, -1)}>↑</button>
                <button class="move-btn" ?disabled=${index === priority.length - 1} @click=${() => handlers.moveRouter('handlers', index, 1)}>↓</button>
                <label>
                  <input type="checkbox" class="checkbox" 
                         .checked=${handlersConfig[name]?.enabled !== false}
                         @change=${(e: any) => handlers.updateRouter('handlers', name, 'enabled', e.target.checked)}>
                  Enabled
                </label>
                <label>
                  <input type="checkbox" class="checkbox" 
                         .checked=${handlersConfig[name]?.terminal !== false}
                         @change=${(e: any) => handlers.updateRouter('handlers', name, 'terminal', e.target.checked)}>
                  Terminal
                </label>
              </div>
            </div>
            ${renderHandlerProperties(handlersConfig[name] || {}, name, handlers)}
          </div>
        `)}
      </div>
    </div>
  `;
}

function renderHandlerProperties(handler: any, name: string, handlers: any) {
  return html`
    <div>
      <h4>Properties</h4>
      ${Object.entries(handler).filter(([key]) => key !== 'enabled').map(([key, value]) => {
        const propType = handlers.inferPropertyType(name, key, value);
        const schema = handlers.routerSchemas[name]?.[key];
        return html`
        <div class="form-group">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <label>${key}</label>
            <button class="remove-btn" @click=${() => handlers.removeRouterProperty('handlers', name, key)}>Remove</button>
          </div>
          ${propType === 'structured-array' ? renderStructuredArray(value, key, name, schema, handlers) : 
            propType === 'array' ? renderArray(value, key, name, handlers) : 
            renderPrimitive(value, key, name, handlers)}
        </div>
      `})}
      <button class="add-btn" @click=${() => handlers.addRouterProperty('handlers', name)}>Add Property</button>
    </div>
  `;
}

function renderStructuredArray(value: any[], key: string, name: string, schema: any, handlers: any) {
  const items = Array.isArray(value) ? value : [];
  return html`
    ${items.map((item: any, i: number) => html`
      <div class="stage-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
          <span>Item ${i + 1}</span>
          <button class="remove-btn" @click=${() => {
            handlers.config.routers.handlers[name][key].splice(i, 1);
            handlers.requestUpdate();
          }}>Remove</button>
        </div>
        ${Object.entries(schema?.items?.properties || {}).map(([field, fieldSchema]: [string, any]) => html`
          <div class="form-group">
            <label>${fieldSchema.label || field}</label>
            ${field === 'response' ? html`
              <textarea .value=${item[field] || ''} 
                        @input=${(e: any) => {
                          handlers.config.routers.handlers[name][key][i][field] = e.target.value;
                          handlers.requestUpdate();
                        }}></textarea>
            ` : html`
              <input .value=${item[field] || ''} 
                     @input=${(e: any) => {
                       handlers.config.routers.handlers[name][key][i][field] = e.target.value;
                       handlers.requestUpdate();
                     }}>
            `}
          </div>
        `)}
      </div>
    `)}
    <button class="add-btn" @click=${() => handlers.addArrayItem('handlers', name, key, {})}>Add Item</button>
  `;
}

function renderArray(value: any, key: string, name: string, handlers: any) {
  return html`
    <textarea .value=${JSON.stringify(value, null, 2)} 
              @input=${(e: any) => {
                try {
                  handlers.updateRouter('handlers', name, key, JSON.parse(e.target.value));
                } catch {}
              }}></textarea>
  `;
}

function renderPrimitive(value: any, key: string, name: string, handlers: any) {
  return html`
    <input .value=${typeof value === 'object' ? JSON.stringify(value) : value || ''} 
           @input=${(e: any) => handlers.updateRouter('handlers', name, key, e.target.value)}>
  `;
}
