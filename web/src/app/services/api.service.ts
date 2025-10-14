import { Injectable, inject } from '@angular/core';
import { BehaviorSubject, Observable, combineLatest, distinctUntilChanged, map, of, shareReplay, tap } from 'rxjs';
import { HttpClient, HttpParams } from '@angular/common/http';
import { UtilsService } from './utils.service';
import { APIResponse, Constant, Identity, Info, User } from '../types/API';
import { Router } from '@angular/router';
import { AuthParams } from '../types/OIDC';
import { CaseEvent, EventCategory } from '../types/event';
import { CaseMetadata, CaseStat } from '../types/case';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private utils = inject(UtilsService);
  private http = inject(HttpClient);
  private router = inject(Router);
  public apiBaseUrl: string = '/api';

  private _userSubject$ = new BehaviorSubject<string>('');
  readonly user$ = this._userSubject$.asObservable();

  private _userGroups$ = new BehaviorSubject<string[]>([]);
  readonly groups$ = this._userGroups$.asObservable();

  private infoCache: Info | undefined;
  private constantCache: Constant | undefined;

  login(data: Object): Observable<APIResponse<User>> {
    return this.http.post<APIResponse<User>>(`${this.apiBaseUrl}/auth/login`, { data }).pipe(
      tap((resp) => {
        if (resp.data) {
          this._userSubject$.next(resp.data.username);
          this._userGroups$.next(resp.data.groups);
        }
      }),
    );
  }

  unauthorizedRedirectLogin(): void {
    this.router.navigate(['/login']);
  }

  logout(): Observable<APIResponse<null>> {
    return this.http.get<APIResponse<null>>(`${this.apiBaseUrl}/auth/logout`).pipe(
      tap(() => {
        this._userSubject$.next('');
        this.utils.toast('success', 'Logged out', 'Logged out successfully');
        this.router.navigate(['/login']);
      }),
    );
  }

  getAuthParams(): Observable<APIResponse<AuthParams>> {
    return this.http.get<APIResponse<AuthParams>>(`${this.apiBaseUrl}/auth/config`);
  }

  getInfo(): Observable<Info> {
    if (this.infoCache) return of(this.infoCache);
    return this.http.get<APIResponse<Info>>(`${this.apiBaseUrl}/info`).pipe(
      tap((resp) => (this.infoCache = resp.data)),
      map((resp) => resp.data),
    );
  }

  getConstant(): Observable<Constant> {
    if (this.constantCache) return of(this.constantCache);
    return this.http.get<APIResponse<Constant>>(`${this.apiBaseUrl}/constant`).pipe(
      tap((resp) => {
        this.constantCache = resp.data;
        if (resp.data.banner && this.utils.banner !== resp.data.banner) {
          this.utils.banner = resp.data.banner;
        }
      }),
      map((resp) => resp.data),
    );
  }

  isLogged(): Observable<boolean> {
    if (this._userSubject$.value) return of(true);
    return this.http.get<APIResponse<{ username: string }>>(`${this.apiBaseUrl}/auth/is_logged`).pipe(
      tap((resp) => {
        if (resp.data?.username) this._userSubject$.next(resp.data.username);
      }),
      map(() => true),
      distinctUntilChanged(),
      shareReplay({ bufferSize: 1, refCount: true }),
    );
  }

  getIdentities(): Observable<Identity> {
    return this.http.get<APIResponse<User[]>>(`${this.apiBaseUrl}/auth/identities`).pipe(
      map((resp) => {
        const users = resp.data.map((u) => u.username);
        const groups = Array.from(new Set(resp.data.flatMap((u) => u.groups)));
        return { users, groups };
      }),
      distinctUntilChanged(),
      shareReplay({ bufferSize: 1, refCount: true }),
    );
  }

  getCase(caseGuid: string): Observable<CaseMetadata> {
    return this.http.get<APIResponse<CaseMetadata>>(`${this.apiBaseUrl}/case/${caseGuid}`).pipe(
      map((resp) => resp.data),
      distinctUntilChanged(),
      shareReplay({ bufferSize: 1, refCount: true }),
    );
  }

  getCases(): Observable<CaseMetadata[]> {
    const cases$ = this.http.get<APIResponse<CaseMetadata[]>>(`${this.apiBaseUrl}/cases`);
    const stats$ = this.http.get<APIResponse<CaseStat[]>>(`${this.apiBaseUrl}/cases/stats`);

    return combineLatest([cases$, stats$]).pipe(
      map(([casesResponse, statsResponse]) => {
        const cases = casesResponse.data || [];
        const stats = statsResponse.data || [];

        const previousEventCounts = this.utils.getLocalStorageCaseEvents();
        this.utils.initLocalStorageCaseEvents(cases);

        const statsMap = stats.reduce<{ [guid: string]: { pending: number; total: number } }>((acc, stat) => {
          acc[stat.guid] = { pending: stat.pending, total: stat.total };
          return acc;
        }, {});

        return cases.map((c: CaseMetadata) => {
          let enrichedCase = { ...c };
          if (statsMap.hasOwnProperty(c.guid)) {
            const stat = statsMap[c.guid];
            enrichedCase.eventsPending = stat.pending;
            enrichedCase.eventsTotal = stat.total || 0;
          }

          if (previousEventCounts.hasOwnProperty(c.guid)) {
            enrichedCase.unseenTotal = (enrichedCase.eventsTotal || 0) - previousEventCounts[c.guid];
          } else {
            enrichedCase.unseenNew = true;
          }
          return enrichedCase;
        });
      }),
      distinctUntilChanged(),
      shareReplay({ bufferSize: 1, refCount: true }),
    );
  }

  getCaseCategories(guid: string): Observable<EventCategory[]> {
    return this.http.get<APIResponse<EventCategory[]>>(`${this.apiBaseUrl}/case/${guid}/categories`).pipe(
      map((resp) => {
        return resp.data?.sort((a: EventCategory, b: EventCategory) => (a.name > b.name ? 1 : -1)) || [];
      }),
      distinctUntilChanged(),
      shareReplay(),
    );
  }

  postCase(caseData: CaseMetadata): Observable<CaseMetadata> {
    return this.http.post<APIResponse<CaseMetadata>>(`${this.apiBaseUrl}/case`, caseData).pipe(
      tap((resp) => this.utils.putLocalStorageCaseEvents(resp.data.guid, 0)),
      map((resp) => resp.data),
    );
  }

  putCase(caseGuid: string, caseData: Partial<CaseMetadata>): Observable<CaseMetadata> {
    return this.http
      .put<APIResponse<CaseMetadata>>(`${this.apiBaseUrl}/case/${caseGuid}`, caseData)
      .pipe(map((resp) => resp.data));
  }

  postCaseEvent(eventData: Partial<CaseEvent>, caseGuid: string): Observable<CaseEvent> {
    return this.http
      .post<APIResponse<CaseEvent>>(`${this.apiBaseUrl}/case/${caseGuid}/event`, { ...eventData })
      .pipe(map((resp) => resp.data));
  }

  getCaseTrash(case_guid: string): Observable<CaseEvent[]> {
    return this.http
      .get<APIResponse<CaseEvent[]>>(`${this.apiBaseUrl}/case/${case_guid}/trash`)
      .pipe(map((resp) => resp.data));
  }

  restoreEvent(event_guid: string, case_guid: string): Observable<CaseEvent> {
    return this.http
      .put<APIResponse<CaseEvent>>(`${this.apiBaseUrl}/case/${case_guid}/event/${event_guid}/restore`, {})
      .pipe(map((resp) => resp.data));
  }

  starEventToggle(event_guid: string, case_guid: string): Observable<any> {
    return this.http.put<APIResponse<CaseEvent>>(`${this.apiBaseUrl}/case/${case_guid}/event/${event_guid}/star`, {});
  }

  trashEvent(case_guid: string, event_guid: string): Observable<any> {
    return this.http.put<APIResponse<CaseEvent>>(`${this.apiBaseUrl}/case/${case_guid}/event/${event_guid}/trash`, {});
  }

  getCaseEventsSSE(guid: string): EventSource {
    const eventSource = new EventSource(`${this.apiBaseUrl}/case/${guid}/subscribe`);
    eventSource.onerror = () => {
      this.utils.toast('error', 'Error', `EventSource disconnected`);
    };
    return eventSource;
  }

  exportCaseEvents(caseGuid: string, starredOnly: boolean, fields?: string[]): Observable<Blob> {
    let params = new HttpParams();
    if (fields) {
      fields.forEach((field) => {
        params = params.append('fields', field);
      });
    }

    if (starredOnly) params = params.set('starred', '1');
    return this.http.get<Blob>(`${this.apiBaseUrl}/case/${caseGuid}/events/export`, {
      params,
      responseType: 'blob' as 'json',
    });
  }

  getCaseAvailableUsers(guid: string): Observable<string[]> {
    return this.http.get<APIResponse<User[]>>(`${this.apiBaseUrl}/case/${guid}/users`).pipe(
      map((resp) => {
        return resp.data.map((d) => d.username).sort((a: string, b: string) => (a > b ? 1 : -1));
      }),
    );
  }

  getCaseActiveUsers(guid: string): Observable<string[]> {
    return this.http.get<APIResponse<User[]>>(`${this.apiBaseUrl}/case/${guid}/users?active`).pipe(
      map((resp) => {
        return resp.data.map((d) => d.username).sort((a: string, b: string) => (a > b ? 1 : -1));
      }),
    );
  }

  getCaseEvents(guid: string): Observable<APIResponse<CaseEvent[]>> {
    return this.http.get<APIResponse<CaseEvent[]>>(`${this.apiBaseUrl}/case/${guid}/events`).pipe(
      tap((resp) => {
        this.utils.putLocalStorageCaseEvents(guid, resp.data.length);
      }),
      distinctUntilChanged(),
      shareReplay({ bufferSize: 1, refCount: true }),
    );
  }
}
