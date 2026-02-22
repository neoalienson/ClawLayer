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
          fast: {
            priority: ['echo', 'command'],
          },
        },
      };
      const requestUpdateSpy = vi.spyOn(editor, 'requestUpdate');

      editor.moveRouter('fast', 1, -1);

      expect(editor.config.routers.fast.priority).toEqual(['command', 'echo']);
      expect(requestUpdateSpy).toHaveBeenCalled();
    });

    it('should not move router beyond bounds', () => {
      editor.config = {
        routers: {
          fast: {
            priority: ['echo', 'command'],
          },
        },
      };

      editor.moveRouter('fast', 0, -1);

      expect(editor.config.routers.fast.priority).toEqual(['echo', 'command']);
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
          fast: {
            command: { enabled: true },
          },
        },
      };
      vi.spyOn(window, 'prompt')
        .mockReturnValueOnce('prefix')
        .mockReturnValueOnce('run:');
      const updateRouterSpy = vi.spyOn(editor, 'updateRouter');

      editor.addRouterProperty('fast', 'command');

      expect(updateRouterSpy).toHaveBeenCalledWith('fast', 'command', 'prefix', 'run:');
    });
  });

  describe('removeRouterProperty', () => {
    it('should remove property from router', () => {
      editor.config = {
        routers: {
          fast: {
            command: { enabled: true, prefix: 'run:' },
          },
        },
      };
      const requestUpdateSpy = vi.spyOn(editor, 'requestUpdate');

      editor.removeRouterProperty('fast', 'command', 'prefix');

      expect(editor.config.routers.fast.command.prefix).toBeUndefined();
      expect(requestUpdateSpy).toHaveBeenCalled();
    });
  });
});