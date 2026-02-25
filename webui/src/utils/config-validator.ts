/**
 * Config validation and reconciliation utilities
 */

export interface RouterConfig {
  priority?: string[];
  [key: string]: any;
}

export interface Config {
  handlers?: RouterConfig;
  routers?: {
    semantic?: RouterConfig;
    [key: string]: RouterConfig | undefined;
  };
  [key: string]: any;
}

/**
 * Validates and fixes priority arrays in router configurations
 * Ensures all routers are included in the priority array
 */
export function validateAndFixPriorities(config: Config): void {
  if (!config.routers) config.routers = {};
  
  // Handle handlers at root level
  if (config.handlers) {
    const routerNames = Object.keys(config.handlers).filter(k => k !== 'priority');
    const priority = Array.isArray(config.handlers.priority) ? config.handlers.priority : [];
    const missing = routerNames.filter(name => !priority.includes(name));
    
    if (missing.length > 0) {
      config.handlers.priority = [...priority, ...missing];
      console.log(`Reconstructed handlers priority: added ${missing.join(', ')}`);
    }
  }
  
  // Handle semantic under routers
  if (config.routers.semantic) {
    const routerNames = Object.keys(config.routers.semantic).filter(k => k !== 'priority');
    const priority = Array.isArray(config.routers.semantic.priority) ? config.routers.semantic.priority : [];
    const missing = routerNames.filter(name => !priority.includes(name));
    
    if (missing.length > 0) {
      config.routers.semantic.priority = [...priority, ...missing];
      console.log(`Reconstructed semantic priority: added ${missing.join(', ')}`);
    }
  }
}
