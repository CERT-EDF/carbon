import { inject, Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { Title } from '@angular/platform-browser';
import { MessageService } from 'primeng/api';
import { CaseMetadata } from '../types/case';
import { CaseEvent } from '../types/event';
import { version } from '../../../public/version';

const DARK = 'DARK';
const BANNER = 'CARBON_BANNER';
const CASE_EVENTS = 'CARBON_CASE_EVENTS';
const CACHED_EVENT = 'CARBON_CACHED_EVENT';

@Injectable({
  providedIn: 'root',
})
export class UtilsService {
  messageService = inject(MessageService);
  private router = inject(Router);
  private title = inject(Title);
  private bannerText: string = '';
  readonly frontendVersion: string = version;
  isDarkMode = false;
  tz = 'Europe/Paris';

  calculateSimpleChecksum(input: string): number {
    let checksum = 0;
    for (let i = 0; i < input.length; i++) {
      checksum ^= input.charCodeAt(i);
    }
    return checksum;
  }

  get banner(): string {
    const storedChecksum = +(localStorage.getItem(BANNER) || '0');
    if (this.calculateSimpleChecksum(this.bannerText) === storedChecksum) return '';
    return this.bannerText;
  }

  set banner(str: string) {
    this.bannerText = str;
  }

  ackBanner(bannerText: string): void {
    localStorage.setItem(BANNER, this.calculateSimpleChecksum(bannerText).toString());
  }

  toast(severity = 'info', summary = 'Info', detail = '', life = 3000): void {
    this.messageService.add({
      severity,
      summary,
      detail,
      life,
      sticky: life == -1,
    });
  }

  navigateHomeWithError(msg = ''): void {
    if (msg) this.toast('error', 'Unauthorized', msg);
    this.router.navigate(['/home']);
  }

  isDarkModeEnabled(): boolean {
    return !!localStorage.getItem(DARK);
  }

  toggleDarkMode(): void {
    this.isDarkMode = !this.isDarkMode;
    if (this.isDarkMode) localStorage.removeItem(DARK);
    else localStorage.setItem(DARK, '1');
    const element = document.documentElement;
    element.classList.toggle('dark');
  }

  getLocalStorageCaseEvents(): { [key: string]: number } {
    return JSON.parse(localStorage.getItem(CASE_EVENTS) || '{}');
  }

  initLocalStorageCaseEvents(cases: CaseMetadata[]): void {
    if (localStorage.getItem(CASE_EVENTS) === null) {
      try {
        let dctCases: { [key: string]: number } = {};
        cases.forEach((c) => {
          if (c.guid) dctCases[c.guid!] = c.eventsTotal || 0;
        });
        localStorage.setItem(CASE_EVENTS, JSON.stringify(dctCases));
      } catch {
        this.toast('error', 'Error', 'localStorage was not initialized. Error.');
      }
    }
  }

  resetLocalStorageCaseEvents(cases: CaseMetadata[]): void {
    if (localStorage.getItem(CASE_EVENTS) !== null) localStorage.removeItem(CASE_EVENTS);
    this.initLocalStorageCaseEvents(cases);
  }

  putLocalStorageCaseEvents(caseGuid: string, eventCount?: number): void {
    try {
      const storedEvents = this.getLocalStorageCaseEvents();
      if (typeof eventCount !== 'undefined' && eventCount > -1) {
        storedEvents[caseGuid] = eventCount;
      } else {
        storedEvents[caseGuid] = (storedEvents[caseGuid] || 0) + 1;
      }
      localStorage.setItem(CASE_EVENTS, JSON.stringify(storedEvents));
    } catch {
      this.toast('error', 'Error', 'Failed to update case events storage.');
    }
  }

  set cachedEventBeforeUpload(event: CaseEvent | null) {
    if (event) localStorage.setItem(CACHED_EVENT, JSON.stringify(event));
    else localStorage.removeItem(CACHED_EVENT);
  }

  get cachedEventBeforeUpload(): CaseEvent | null {
    const stored = localStorage.getItem(CACHED_EVENT);
    return stored ? JSON.parse(stored) : null;
  }

  dateToLocaleString(date: string, tz: string = this.tz): string {
    return new Date(date).toLocaleString('en-US', { timeZone: tz });
  }

  dateToLocaleDateString(date: string, tz: string = this.tz): string {
    return new Date(date).toLocaleDateString('en-US', {
      timeZone: tz,
      month: '2-digit',
      day: '2-digit',
      year: 'numeric',
    });
  }

  dateToUTCString(date: string): string {
    return new Date(date).toLocaleDateString('en-US', {
      timeZone: 'UTC',
      month: '2-digit',
      day: '2-digit',
      year: 'numeric',
    });
  }

  setTitle(title: string) {
    this.title.setTitle(title);
  }
}
