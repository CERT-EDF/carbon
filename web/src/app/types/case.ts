export interface CaseMetadata {
  guid: string;
  created?: string;
  updated?: string;
  closed?: string;
  tsid?: string;
  name: string;
  description?: string;
  acs: string[];
  utc_display: boolean;
  managed: boolean;

  imgUrl?: string; //Injected value in API getCases
  eventsTotal?: number; //Injected value in API getCases
  eventsPending?: number; //Injected value in API getCases
  unseenNew?: boolean; //Injected value in API getCases
  unseenTotal?: number; //Injected value in API getCases
}

export interface CaseStat {
  guid: string;
  pending: number;
  total: number;
}

export interface FusionEvent {
  source: string;
  category: string;
  case: CaseMetadata;
  ext: any;
}
