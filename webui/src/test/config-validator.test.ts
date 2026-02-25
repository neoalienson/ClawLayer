import { describe, it, expect } from 'vitest';
import { validateAndFixPriorities } from '../utils/config-validator';

describe('config-validator', () => {
  describe('validateAndFixPriorities', () => {
    it('should reconstruct empty handlers priority', () => {
      const config = {
        handlers: {
          priority: [],
          quick: { enabled: true },
          echo: { enabled: true }
        }
      };

      validateAndFixPriorities(config);

      expect(config.handlers.priority).toEqual(['quick', 'echo']);
    });

    it('should reconstruct empty semantic priority', () => {
      const config = {
        routers: {
          semantic: {
            priority: [],
            greeting: { enabled: true },
            summarize: { enabled: true }
          }
        }
      };

      validateAndFixPriorities(config);

      expect(config.routers.semantic.priority).toEqual(['greeting', 'summarize']);
    });

    it('should fix null priority', () => {
      const config = {
        handlers: {
          priority: null,
          quick: { enabled: true }
        }
      };

      validateAndFixPriorities(config);

      expect(Array.isArray(config.handlers.priority)).toBe(true);
      expect(config.handlers.priority).toEqual(['quick']);
    });

    it('should preserve existing priority order', () => {
      const config = {
        handlers: {
          priority: ['echo'],
          echo: { enabled: true },
          quick: { enabled: true }
        }
      };

      validateAndFixPriorities(config);

      expect(config.handlers.priority).toEqual(['echo', 'quick']);
    });

    it('should handle missing routers section', () => {
      const config = {};

      expect(() => validateAndFixPriorities(config)).not.toThrow();
    });

    it('should handle missing handlers section', () => {
      const config = {
        routers: {
          semantic: {
            priority: [],
            greeting: { enabled: true }
          }
        }
      };

      validateAndFixPriorities(config);

      expect(config.routers.semantic.priority).toEqual(['greeting']);
    });

    it('should not modify valid priority', () => {
      const config = {
        handlers: {
          priority: ['quick', 'echo'],
          quick: { enabled: true },
          echo: { enabled: true }
        }
      };

      validateAndFixPriorities(config);

      expect(config.handlers.priority).toEqual(['quick', 'echo']);
    });
  });
});
