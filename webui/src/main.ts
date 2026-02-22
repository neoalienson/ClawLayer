import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import './components/dashboard';
import './components/config-editor';
import './components/log-viewer';

@customElement('cl-app')
export class App extends LitElement {
  static styles = css`
    :host { display: block; min-height: 100vh; background: #f5f6fa; }
    nav { background: #2c3e50; color: white; padding: 1rem 2rem; display: flex; align-items: center; gap: 2rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    h1 { margin: 0; font-size: 1.5rem; }
    .tabs { display: flex; gap: 0.5rem; }
    button { background: none; border: none; color: white; padding: 0.75rem 1.5rem; cursor: pointer; border-radius: 4px; font-size: 14px; transition: background 0.2s; }
    button:hover { background: rgba(255,255,255,0.1); }
    button.active { background: #34495e; }
    main { max-width: 1200px; margin: 0 auto; }
  `;
  
  @state() currentTab = 'dashboard';
  
  render() {
    return html`
      <nav>
        <h1>🦞🍽️ ClawLayer</h1>
        <div class="tabs">
          <button 
            class=${this.currentTab === 'dashboard' ? 'active' : ''} 
            @click=${() => this.currentTab = 'dashboard'}>
            Dashboard
          </button>
          <button 
            class=${this.currentTab === 'config' ? 'active' : ''} 
            @click=${() => this.currentTab = 'config'}>
            Config
          </button>
          <button 
            class=${this.currentTab === 'logs' ? 'active' : ''} 
            @click=${() => this.currentTab = 'logs'}>
            Logs
          </button>
        </div>
      </nav>
      
      <main>
        ${this.currentTab === 'dashboard' ? html`<cl-dashboard></cl-dashboard>` : ''}
        ${this.currentTab === 'config' ? html`<cl-config-editor></cl-config-editor>` : ''}
        ${this.currentTab === 'logs' ? html`<cl-log-viewer></cl-log-viewer>` : ''}
      </main>
    `;
  }
}
