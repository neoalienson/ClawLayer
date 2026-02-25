import { html } from 'lit';

export function renderSemanticRoutersTab(config: any, handlers: any) {
  const providers = config.providers || {};
  const routers = config.routers || {};
  const priority = Array.isArray(routers.semantic?.priority) ? routers.semantic.priority : [];
  
  return html`
    <div class="section">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
        <h2 style="margin: 0;">Semantic Routers</h2>
        <button class="add-btn" style="margin: 0;" @click=${handlers.addSemanticRouter}>Add Semantic Router</button>
      </div>
      <div class="router-priority">
        ${priority.map((name: string, index: number) => html`
          <div class="draggable">
            <div class="router-header">
              <span>🧠 ${name} Router</span>
              <div class="router-controls">
                <button class="remove-btn" @click=${() => handlers.removeRouter('semantic', name)}>Delete</button>
                <button class="move-btn" ?disabled=${index === 0} @click=${() => handlers.moveRouter('semantic', index, -1)}>↑</button>
                <button class="move-btn" ?disabled=${index === priority.length - 1} @click=${() => handlers.moveRouter('semantic', index, 1)}>↓</button>
                <label>
                  <input type="checkbox" class="checkbox" 
                         .checked=${routers.semantic?.[name]?.enabled !== false}
                         @change=${(e: any) => handlers.updateRouter('semantic', name, 'enabled', e.target.checked)}>
                  Enabled
                </label>
              </div>
            </div>
            ${renderSemanticRouterContent(routers.semantic?.[name] || {}, name, providers, handlers)}
          </div>
        `)}
      </div>
    </div>
  `;
}

function renderSemanticRouterContent(router: any, name: string, providers: any, handlers: any) {
  const stages = Array.isArray(router.stages) ? router.stages : [];
  const utterances = Array.isArray(router.utterances) ? router.utterances : [];
  
  return html`
    <div>
      <h4>Stages</h4>
      ${stages.map((stage: any, i: number) => html`
        <div class="stage-card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <span>Stage ${i + 1}</span>
            <button class="remove-btn" @click=${() => handlers.removeStage(name, i)}>Remove</button>
          </div>
          <div class="stage-row">
            <div>
              <label>Provider</label>
              <select @change=${(e: any) => handlers.updateStage(name, i, 'provider', e.target.value)}>
                <option value="">Select...</option>
                ${Object.keys(providers).map(pname => html`<option value="${pname}" ?selected=${stage.provider === pname}>${pname}</option>`)}
              </select>
            </div>
            <div>
              <label>Model</label>
              <input placeholder="Model" .value=${stage.model || ''} 
                     @input=${(e: any) => handlers.updateStage(name, i, 'model', e.target.value)}>
            </div>
            <div>
              <label>Threshold: ${stage.threshold || 0}</label>
              <input type="range" min="0" max="1" step="0.1" .value=${stage.threshold || 0} 
                     @input=${(e: any) => handlers.updateStage(name, i, 'threshold', parseFloat(e.target.value))}>
            </div>
          </div>
        </div>
      `)}
      <button class="add-btn" @click=${() => handlers.addStage(name)}>Add Stage</button>
      
      <h4>Utterances</h4>
      <textarea .value=${utterances.join('\n')} 
                @input=${(e: any) => handlers.updateUtterances(name, e.target.value)}
                placeholder="One utterance per line"></textarea>
    </div>
  `;
}
