import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ConfigEditor } from '../components/config-editor';
import { ClawLayerClient } from '../api/clawlayer-client';

// Mock the ClawLayerClient
vi.mock('../api/clawlayer-client');

describe('ConfigEditor', () => {
  let editor: ConfigEditor;
  let mockClient: any;

  beforeEach(() => {
    mockClient = {
      getConfig: vi.fn(),
      saveConfig: vi.fn(),
    };
    vi.mocked(ClawLayerClient).mockImplementation(() => mockClient);
    
    editor = new ConfigEditor();
    // Initialize config to prevent undefined errors
    editor.config = {
      providers: {},
      defaults: {},
      server: { port: 11435 },
      routers: { handlers: {}, semantic: {} }
    };
    document.body.appendChild(editor);
  });

  afterEach(() => {
    document.body.removeChild(editor);
  });

  describe('loadConfig', () => {
    it('should load config from API', async () => {
      const mockConfig = {
        providers: { local: { url: 'http://localhost:11434' } },
        defaults: { embedding_provider: 'local' },
      };
      mockClient.getConfig.mockResolvedValue(mockConfig);

      await editor.loadConfig();

      expect(mockClient.getConfig).toHaveBeenCalled();
      expect(editor.config).toEqual(mockConfig);
    });

    it('should collapse all providers by default', async () => {
      const mockConfig = {
        providers: { 
          local: { url: 'http://localhost:11434' },
          remote: { url: 'http://remote:11434' }
        },
        defaults: { embedding_provider: 'local' },
      };
      mockClient.getConfig.mockResolvedValue(mockConfig);

      await editor.loadConfig();

      expect(editor.collapsedProviders.has('local')).toBe(true);
      expect(editor.collapsedProviders.has('remote')).toBe(true);
      expect(editor.collapsedProviders.size).toBe(2);
    });

    it('should show error message on load failure', async () => {
      mockClient.getConfig.mockRejectedValue(new Error('Network error'));
      const showMessageSpy = vi.spyOn(editor, 'showMessage');

      await editor.loadConfig();

      expect(showMessageSpy).toHaveBeenCalledWith('Failed to load config', 'error');
    });
  });

  describe('save', () => {
    it('should save config via API', async () => {
      editor.config = { server: { port: 8080 } };
      mockClient.saveConfig.mockResolvedValue({ status: 'saved' });
      const showMessageSpy = vi.spyOn(editor, 'showMessage');

      await editor.save();

      expect(mockClient.saveConfig).toHaveBeenCalledWith(editor.config);
      expect(showMessageSpy).toHaveBeenCalledWith('Config saved! Restart ClawLayer to apply changes.', 'success');
    });

    it('should show error message on save failure', async () => {
      editor.config = { server: { port: 8080 } };
      mockClient.saveConfig.mockRejectedValue(new Error('Save failed'));
      const showMessageSpy = vi.spyOn(editor, 'showMessage');

      await editor.save();

      expect(showMessageSpy).toHaveBeenCalledWith('Error: Save failed', 'error');
    });
  });

  describe('updateProvider', () => {
    it('should update provider field', () => {
      editor.config = { providers: {} };
      const requestUpdateSpy = vi.spyOn(editor, 'requestUpdate');

      editor.updateProvider('test', 'url', 'http://test.com');

      expect(editor.config.providers.test.url).toBe('http://test.com');
      expect(requestUpdateSpy).toHaveBeenCalled();
    });
  });

  describe('addProvider', () => {
    it('should add new provider', () => {
      editor.config = { providers: {} };
      vi.spyOn(window, 'prompt').mockReturnValue('newProvider');
      const requestUpdateSpy = vi.spyOn(editor, 'requestUpdate');

      editor.addProvider();

      expect(editor.config.providers.newProvider).toEqual({
        url: '',
        type: 'ollama',
        models: {},
      });
      expect(requestUpdateSpy).toHaveBeenCalled();
    });

    it('should not add provider if name is empty', () => {
      editor.config = { providers: {} };
      vi.spyOn(window, 'prompt').mockReturnValue('');

      editor.addProvider();

      expect(Object.keys(editor.config.providers)).toHaveLength(0);
    });
  });

  describe('removeProvider', () => {
    it('should remove provider after confirmation', () => {
      editor.config = { providers: { test: { url: 'http://test.com' } } };
      vi.spyOn(window, 'confirm').mockReturnValue(true);
      const requestUpdateSpy = vi.spyOn(editor, 'requestUpdate');

      editor.removeProvider('test');

      expect(editor.config.providers.test).toBeUndefined();
      expect(requestUpdateSpy).toHaveBeenCalled();
    });

    it('should not remove provider if not confirmed', () => {
      editor.config = { providers: { test: { url: 'http://test.com' } } };
      vi.spyOn(window, 'confirm').mockReturnValue(false);

      editor.removeProvider('test');

      expect(editor.config.providers.test).toBeDefined();
    });
  });

  describe('moveRouter', () => {
    it('should move router up in priority', () => {
      editor.config = {
        routers: {
          handlers: {
            priority: ['echo', 'command'],
          },
        },
      };
      const requestUpdateSpy = vi.spyOn(editor, 'requestUpdate');

      editor.moveRouter('handlers', 1, -1);

      expect(editor.config.routers.handlers.priority).toEqual(['command', 'echo']);
      expect(requestUpdateSpy).toHaveBeenCalled();
    });

    it('should not move router beyond bounds', () => {
      editor.config = {
        routers: {
          handlers: {
            priority: ['echo', 'command'],
          },
        },
      };

      editor.moveRouter('handlers', 0, -1);

      expect(editor.config.routers.handlers.priority).toEqual(['echo', 'command']);
    });
  });

  describe('addStage', () => {
    it('should add new stage to semantic router', () => {
      editor.config = {
        routers: {
          semantic: {
            greeting: { stages: [] },
          },
        },
      };
      const requestUpdateSpy = vi.spyOn(editor, 'requestUpdate');

      editor.addStage('greeting');

      expect(editor.config.routers.semantic.greeting.stages).toHaveLength(1);
      expect(editor.config.routers.semantic.greeting.stages[0]).toEqual({
        provider: '',
        model: '',
        threshold: 0.7,
      });
      expect(requestUpdateSpy).toHaveBeenCalled();
    });
  });

  describe('removeStage', () => {
    it('should remove stage from semantic router', () => {
      editor.config = {
        routers: {
          semantic: {
            greeting: {
              stages: [
                { provider: 'local', model: 'test', threshold: 0.7 },
                { provider: 'remote', model: 'test2', threshold: 0.6 },
              ],
            },
          },
        },
      };
      const requestUpdateSpy = vi.spyOn(editor, 'requestUpdate');

      editor.removeStage('greeting', 0);

      expect(editor.config.routers.semantic.greeting.stages).toHaveLength(1);
      expect(editor.config.routers.semantic.greeting.stages[0].provider).toBe('remote');
      expect(requestUpdateSpy).toHaveBeenCalled();
    });
  });

  describe('addRouterProperty', () => {
    it('should add property to router', () => {
      editor.config = {
        routers: {
          handlers: {
            command: { enabled: true },
          },
        },
      };
      vi.spyOn(window, 'prompt')
        .mockReturnValueOnce('prefix')
        .mockReturnValueOnce('run:');
      const updateRouterSpy = vi.spyOn(editor, 'updateRouter');

      editor.addRouterProperty('handlers', 'command');

      expect(updateRouterSpy).toHaveBeenCalledWith('handlers', 'command', 'prefix', 'run:');
    });
  });

  describe('removeRouterProperty', () => {
    it('should remove property from router', () => {
      editor.config = {
        routers: {
          handlers: {
            command: { enabled: true, prefix: 'run:' },
          },
        },
      };
      const requestUpdateSpy = vi.spyOn(editor, 'requestUpdate');

      editor.removeRouterProperty('handlers', 'command', 'prefix');

      expect(editor.config.routers.handlers.command.prefix).toBeUndefined();
      expect(requestUpdateSpy).toHaveBeenCalled();
    });
  });

  describe('toggleProvider', () => {
    it('should collapse expanded provider', () => {
      editor.collapsedProviders = new Set();
      const requestUpdateSpy = vi.spyOn(editor, 'requestUpdate');

      editor.toggleProvider('local');

      expect(editor.collapsedProviders.has('local')).toBe(true);
      expect(requestUpdateSpy).toHaveBeenCalled();
    });

    it('should expand collapsed provider', () => {
      editor.collapsedProviders = new Set(['local']);
      const requestUpdateSpy = vi.spyOn(editor, 'requestUpdate');

      editor.toggleProvider('local');

      expect(editor.collapsedProviders.has('local')).toBe(false);
      expect(requestUpdateSpy).toHaveBeenCalled();
    });

    it('should toggle multiple providers independently', () => {
      editor.collapsedProviders = new Set(['local']);

      editor.toggleProvider('remote');
      expect(editor.collapsedProviders.has('local')).toBe(true);
      expect(editor.collapsedProviders.has('remote')).toBe(true);

      editor.toggleProvider('local');
      expect(editor.collapsedProviders.has('local')).toBe(false);
      expect(editor.collapsedProviders.has('remote')).toBe(true);
    });
  });

  describe('tab navigation', () => {
    it('should default to handlers tab', () => {
      expect(editor.activeTab).toBe('handlers');
    });

    it('should switch to semantic-routers tab', () => {
      editor.activeTab = 'semantic-routers';
      expect(editor.activeTab).toBe('semantic-routers');
    });

    it('should switch to providers tab', () => {
      editor.activeTab = 'providers';
      expect(editor.activeTab).toBe('providers');
    });

    it('should switch to system tab', () => {
      editor.activeTab = 'system';
      expect(editor.activeTab).toBe('system');
    });
  });

  describe('router schemas', () => {
    it('should fetch router schemas on load', async () => {
      const mockConfig = {
        providers: { local: { url: 'http://localhost:11434' } },
        defaults: { embedding_provider: 'local' },
      };
      const mockSchemas = {
        quick: {
          patterns: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                pattern: { type: 'string', label: 'Pattern (regex)' },
                response: { type: 'string', label: 'Response' }
              }
            }
          }
        }
      };
      
      mockClient.getConfig.mockResolvedValue(mockConfig);
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockSchemas
      });

      await editor.loadConfig();

      expect(editor.routerSchemas).toEqual(mockSchemas);
    });

    it('should infer structured-array type from schema', () => {
      editor.routerSchemas = {
        quick: {
          patterns: {
            type: 'array',
            items: { type: 'object' }
          }
        }
      };

      const type = editor.inferPropertyType('quick', 'patterns', []);
      expect(type).toBe('structured-array');
    });

    it('should fallback to array type when no schema', () => {
      editor.routerSchemas = {};
      const type = editor.inferPropertyType('unknown', 'items', []);
      expect(type).toBe('array');
    });
  });
});