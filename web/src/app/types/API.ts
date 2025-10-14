import { EventCategory } from './event';

export interface APIResponse<T> {
  data: T;
  count: number;
}

export interface User {
  username: string;
  groups: string[];
}

export interface Identity {
  users: string[];
  groups: string[];
}

export interface SearchPattern {
  name: string;
  pattern: string;
}

export interface Constant {
  banner?: string;
  categories: { [category: string]: EventCategory };
  search_patterns: SearchPattern[];
  allow_empty_acs?: boolean;
}

export interface Info {
  api: string;
  version: string;
}
