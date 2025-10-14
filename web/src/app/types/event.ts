export interface CaseEvent {
  guid: string;
  title: string;
  creator: string;
  closes?: string;
  created?: string; // Injected from backend
  date: string; // Ev. Date
  duedate?: string;
  starred: boolean;
  trashed: boolean;
  category: string;
  assignees: string[];
  description: string;

  case_guid?: string; // Injected for cached event
  closedBy?: CaseEvent; // Injected in case detail
}

export interface EventCategory {
  name: string;
  icon: string;
  color: string;
  description?: string;
  groups?: string[];
}
