import { ChangeDetectorRef, Component, OnDestroy, ViewChild } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { FloatLabelModule } from 'primeng/floatlabel';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { TextareaModule } from 'primeng/textarea';
import { SkeletonModule } from 'primeng/skeleton';
import { FocusTrapModule } from 'primeng/focustrap';
import { ApiService } from '../../services/api.service';
import { FormBuilder, FormControl, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { ClipboardModule } from '@angular/cdk/clipboard';
import { DialogService } from 'primeng/dynamicdialog';
import { Menu, MenuModule } from 'primeng/menu';
import { UtilsService } from '../../services/utils.service';
import { AsyncPipe, DatePipe, KeyValue, KeyValuePipe } from '@angular/common';
import { MessageModule } from 'primeng/message';
import { TabsModule } from 'primeng/tabs';
import { InputGroupModule } from 'primeng/inputgroup';
import { CaseMetadata, FusionEvent } from '../../types/case';
import { IdleDetectorService } from '../../services/idle-detector.service';
import { debounceTime, map, Observable, skip, Subscription, take } from 'rxjs';
import { CaseEvent, EventCategory } from '../../types/event';
import { TooltipModule } from 'primeng/tooltip';
import { OverlayBadgeModule } from 'primeng/overlaybadge';
import { MenuItem, SelectItemGroup } from 'primeng/api';
import { EventCreateModalComponent } from '../../modals/create-event-modal/event-create-modal.component';
import { YesNoModalComponent } from '../../modals/yes-no-modal/yes-no-modal.component';
import { CaseEventDetailsModalComponent } from '../../modals/case-event-details-modal/case-event-details-modal.component';
import { SearchPattern } from '../../types/API';
import { animate, style, transition, trigger } from '@angular/animations';
import { DialogModule } from 'primeng/dialog';
import { MultiSelectModule } from 'primeng/multiselect';
import { SelectButtonModule } from 'primeng/selectbutton';
import { ToggleSwitchModule } from 'primeng/toggleswitch';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { DeleteConfirmModalComponent } from '../../modals/delete-confirm-modal/delete-confirm-modal.component';

export interface Regex {
  regex: RegExp;
  dispV: string;
  id: number;
}

@Component({
  selector: 'app-case',
  standalone: true,
  imports: [
    RouterLink,
    FloatLabelModule,
    InputTextModule,
    ButtonModule,
    SelectModule,
    ReactiveFormsModule,
    TabsModule,
    AsyncPipe,
    KeyValuePipe,
    TooltipModule,
    MultiSelectModule,
    InputGroupModule,
    OverlayBadgeModule,
    MenuModule,
    TextareaModule,
    SelectButtonModule,
    FocusTrapModule,
    MessageModule,
    ToggleSwitchModule,
    FormsModule,
    SkeletonModule,
    ClipboardModule,
    MenuModule,
    DatePipe,
    ButtonModule,
    DialogModule,
    InputGroupModule,
  ],
  templateUrl: './case.component.html',
  styleUrl: './case.component.scss',
  animations: [
    trigger('backslideY', [
      transition(':leave', [animate('.2s', style({ transform: 'translateY(-20px)', opacity: 0 }))]),
    ]),
  ],
})
export class CaseComponent implements OnDestroy {
  @ViewChild('categoryMenu') categoryMenu!: Menu;

  caseForm: FormGroup;
  eventForm: FormGroup;
  timezone = 'Europe/Paris';
  isFilterMode = false;
  now = new Date();
  username = '';
  acsGroups: SelectItemGroup[] = [];
  closedEventsGUID = new Set<string>();
  isDisplayingSplash = false;
  isReadonly = true;
  eventSource!: Subscription;
  activeUsers: string[] = [];
  isShowingTaskPanel = false;
  isTrashOpened = false;
  trashEvents$?: Observable<(CaseEvent & { gray?: boolean })[]>;
  trashSearchInput = new FormControl('');
  isSettingsOpened = false;
  isExportsOpened = false;
  exportOptionEventValue = 'all';
  exportOptionsEvent: any[] = [
    { name: 'All', value: 'all' },
    { name: 'Starred', value: 'starred' },
  ];
  exportOptionFormatValue = 'md';
  exportOptionsFormat: any[] = [
    { name: 'Markdown', value: 'md' },
    { name: 'JSON', value: 'json' },
  ];
  mdOptionFieldsInput = new FormControl<string[]>([]);
  mdOptionFields: { label: string; value: string }[] = [];
  displayedEventsByDate: { [date: string]: CaseEvent[] } = {};
  filteredCategories: string[] = [];
  searchInputRegex = new FormControl('');
  selectedSearchPattern: { [name: string]: string } = {};
  searchPatterns: SearchPattern[] = [];
  searchPatternMenuItems: MenuItem[] = [];
  caseMeta?: CaseMetadata;
  unseenEvents: string[] = [];
  events: CaseEvent[] = [];
  eventsByDate: { [date: string]: CaseEvent[] } = {};
  categories: EventCategory[] = [];
  categoryMenuItems: MenuItem[] = [];
  subscriptions: Subscription[] = [];

  constructor(
    private apiService: ApiService,
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private idleService: IdleDetectorService,
    private utilsService: UtilsService,
    private cdr: ChangeDetectorRef,
    private dialogService: DialogService,
    private router: Router,
  ) {
    const caseGuid = this.route.snapshot.paramMap.get('guid')!;
    this.timezone = this.utilsService.tz;
    this.apiService.user$.pipe(take(1)).subscribe({
      next: (user) => {
        this.username = user;
        this.activeUsers.push(user);
      },
    });

    this.caseForm = this.fb.group({
      tsid: '',
      name: ['', Validators.required],
      description: '',
      acs: [[], Validators.required],
    });

    this.eventForm = this.fb.group({
      title: '',
      category: 'INFO',
    });
    this.searchInputRegex.valueChanges
      .pipe(debounceTime(400), takeUntilDestroyed())
      .subscribe(() => this.applyFilters());

    this.idleService.wake$.pipe(skip(1), takeUntilDestroyed()).subscribe(() => {
      setTimeout(() => {
        this.unseenEvents.forEach((eventGuid) => {
          if (eventGuid) {
            document.getElementById(eventGuid)?.classList.add('caseEventFadeIn');
          }
        });
      }, 200);

      setTimeout(() => {
        this.unseenEvents = [];
      }, 1000);
    });

    this.apiService
      .getCaseCategories(caseGuid)
      .pipe(take(1))
      .subscribe({
        next: (categories) => (this.categories = categories),
      });

    this.apiService
      .getCase(caseGuid)
      .pipe(take(1))
      .subscribe({
        next: (caseMetadata) => {
          this.caseMeta = caseMetadata;

          this.eventSource = this.apiService.getCaseEventsSSE(this.caseMeta!.guid).subscribe({
            next: (event) => this.handleSSEEvent(event),
            error: (error) => console.error('SSE error:', error),
          });

          this.utilsService.setTitle(`Carbon - ${caseMetadata.name}`);

          this.setTimezoneUTC(caseMetadata.utc_display);
          if (caseMetadata.closed) this.isDisplayingSplash = true;
          else {
            this.isReadonly = false;
            this.subscribeToCaseEvents();
            // Verify if a cached event exist, meaning the user got disconnected before he could upload
            const cachedEvent = this.utilsService.cachedEventBeforeUpload;
            if (cachedEvent && cachedEvent.case_guid === caseMetadata.guid) {
              this.openEventModal(cachedEvent);
            }
          }
        },
        error: () => this.utilsService.navigateHomeWithError('Error while retrieving case'),
      });

    this.apiService
      .getConstant()
      .pipe(take(1))
      .subscribe((constant) => {
        if (!constant.search_patterns.length) return;

        this.searchPatterns = constant.search_patterns;
        constant.search_patterns.forEach((pattern) => {
          this.searchPatternMenuItems.push({
            label: pattern.name,
            icon: 'pi pi-filter',
          });
        });
      });
  }

  subscribeToCaseEvents(): void {
    this.isDisplayingSplash = false;
    this.apiService
      .getCaseEvents(this.caseMeta!.guid)
      .pipe(take(1))
      .subscribe({
        next: (resp) => {
          this.events = resp.data as CaseEvent[];
          this.transformEventsToEventsByDate();
        },
      });
  }

  handleSSEEvent(messageEvent: MessageEvent): void {
    if (!messageEvent.data) return;
    const event: FusionEvent = JSON.parse(messageEvent.data);
    const ext = event.ext;
    console.log('event:', event);
    switch (event.category) {
      case 'subscribers':
        this.activeUsers = ext.usernames;
        break;
      case 'subscribe':
        if (!this.activeUsers.includes(ext.username)) this.activeUsers.push(ext.username);
        break;
      case 'unsubscribe':
        this.activeUsers = this.activeUsers.filter((u) => u !== ext.username);
        break;
      case 'create_event':
        this.addEventToArray(ext);
        if (ext.category === 'TASK' && ext.assignees?.includes(this.username))
          this.utilsService.toast('info', 'New task!', 'You have been assigned to a new task');
        break;
      case 'star_event':
        const eventToStar = this.events.find((e) => e.guid === ext.guid);
        if (eventToStar) eventToStar.starred = ext.starred ?? false;
        break;
      case 'trash_event':
        this.events = this.events.filter((e) => e.guid !== ext.guid);
        this.transformEventsToEventsByDate();
        break;
      case 'delete_event':
        this.events = this.events.filter((e) => e.guid !== ext.guid);
        this.transformEventsToEventsByDate();
        break;
      case 'restore_event':
        const restoredEventExists = this.events.find((e) => e.guid === ext.guid);
        if (!restoredEventExists) this.addEventToArray(ext);
        break;
      case 'update_case':
        console.log('update case event:', event);
        console.log('params:', event.case.guid, event.case.guid !== this.caseMeta?.guid);
        if (event.case.guid && event.case.guid !== this.caseMeta?.guid) {
          this.utilsService.toast(
            'info',
            'Info',
            'Case was re-attached and its ID changed. You were redirected automatically.',
            5000,
          );
          this.router.navigate(['/case/' + event.case.guid]);
        }
        if (event.case.acs) {
          const acs = event.case.acs;
          this.apiService.groups$.pipe(take(1)).subscribe({
            next: (groups) => {
              const allowed = acs.includes(this.username) || groups.some((g) => acs.includes(g));
              if (!allowed) {
                this.utilsService.toast(
                  'error',
                  'Error',
                  'Case groups were modified, you are not allowed to view the case anymore',
                  4500,
                );
                this.utilsService.navigateHomeWithError();
              }
            },
          });
        }

        if (event.case.closed) {
          this.utilsService.toast('error', 'Error', 'This case was closed', 3500);
          this.isDisplayingSplash = true;
          this.isReadonly = true;
          this.isFilterMode = false;
          this.events = [];
          this.displayedEventsByDate = {};
        } else if (!event.case.closed) {
          this.utilsService.toast('info', 'Info', 'This case was reopened', 3500);
          if (this.caseMeta) this.caseMeta.closed = undefined;
          this.isDisplayingSplash = false;
          this.isReadonly = false;
          this.subscribeToCaseEvents();
        }
        this.caseMeta = event.case;
        if (ext.case.utc_display) this.setTimezoneUTC(ext.case.utc_display);
        break;
      case 'delete_case':
        this.utilsService.toast('info', 'Case deleted', 'This case was deleted', 3500);
        this.utilsService.navigateHomeWithError();
        break;
      default:
        break;
    }
    this.cdr.markForCheck();
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach((s) => s.unsubscribe());
    if (this.eventSource) this.eventSource.unsubscribe();
  }

  updateCase(data: Partial<CaseMetadata>): void {
    this.apiService
      .putCase(this.caseMeta!.guid, data)
      .pipe(take(1))
      .subscribe(() => (this.isSettingsOpened = false));
  }

  transformEventsToEventsByDate() {
    this.closedEventsGUID.clear();

    this.eventsByDate = this.events.reduce((acc, event) => {
      if (event.closes) this.closedEventsGUID.add(event.closes);
      const date = this.caseMeta?.utc_display
        ? this.utilsService.dateToUTCString(event.date)
        : this.utilsService.dateToLocaleDateString(event.date, this.timezone);
      acc[date] = acc[date] || [];
      acc[date].push(event);
      return acc;
    }, Object.create(null));

    Object.keys(this.eventsByDate).forEach((date) => {
      this.eventsByDate[date].sort((a, b) => (new Date(b.date).getTime() > new Date(a.date).getTime() ? 1 : -1));
    });

    if (this.isFilterMode) {
      this.applyFilters();
    } else {
      this.displayedEventsByDate = { ...this.eventsByDate };
    }

    this.utilsService.putLocalStorageCaseEvents(this.caseMeta!.guid, this.events.length);
  }

  addEventToArray(event: CaseEvent): void {
    if (!event.creator) event.creator = this.username;
    this.events.push(event);
    this.transformEventsToEventsByDate();
    if (this.idleService.isIdle) this.unseenEvents.push(event.guid);
  }

  scrollToEvent(guid: string): void {
    const eventElement = document.getElementById(guid);
    eventElement?.scrollIntoView({ block: 'center' });
    eventElement?.classList.add('font-bold');
    setTimeout(() => {
      eventElement?.classList.remove('font-bold');
    }, 1500);
  }

  getPendingDateObject(dateString?: string): Date {
    return dateString ? new Date(dateString) : new Date();
  }

  get taskEvents(): CaseEvent[] {
    return this.events.filter((event) => event.category === 'TASK').sort((a, b) => (b.date > a.date ? 1 : -1));
  }

  keyDescOrder = (a: KeyValue<string, any>, b: KeyValue<string, any>): number => {
    return new Date(a.key).getTime() > new Date(b.key).getTime() ? -1 : 1;
  };

  setTimezoneUTC(useUTC = false): void {
    this.timezone = useUTC ? 'UTC' : 'Europe/Paris';
  }

  openDetailsIfNotSelecting(clickEvent: any, event: CaseEvent): void {
    if (clickEvent.view.getSelection().toString().length === 0) {
      this.openEventDetails(event);
    }
  }

  createEvent(eventFormData?: CaseEvent): void {
    if (!this.caseMeta?.guid) return;

    const hasTitle = eventFormData?.title || this.eventForm.get('title')?.value;
    if (!hasTitle) return;

    let eventToCreate: CaseEvent;
    if (eventFormData) eventToCreate = eventFormData;
    else eventToCreate = this.eventForm.value;

    //Cache event in case the user session is not valid anymore to prevent data loss
    this.utilsService.cachedEventBeforeUpload = {
      ...eventToCreate,
      case_guid: this.caseMeta.guid,
    };

    this.apiService
      .postCaseEvent(eventToCreate, this.caseMeta.guid)
      .pipe(take(1))
      .subscribe(() => {
        this.utilsService.cachedEventBeforeUpload = null;
        this.resetEventForm();
      });
  }

  resetEventForm(): void {
    this.eventForm.reset();
    this.eventForm.get('category')?.setValue('INFO');
  }

  applyFilters() {
    let filteredEventsByDate: { [date: string]: CaseEvent[] } = {};
    const hasMatch = this.searchInputRegex.value || Object.keys(this.selectedSearchPattern).length;
    if (hasMatch) {
      const patterns: RegExp[] = [];
      try {
        Object.values(this.selectedSearchPattern).forEach((pattern) => patterns.push(new RegExp(pattern)));
        if (this.searchInputRegex.value) patterns.push(new RegExp(this.searchInputRegex.value, 'i'));
      } catch (e) {
        this.utilsService.toast('error', 'Error', 'Error while parsing Regex expression');
        console.error(e);
        return;
      }

      Object.keys(this.eventsByDate).forEach((date) => {
        const matchedEvents = this.eventsByDate[date].filter(
          (event) =>
            this.filteredCategories.includes(event.category) &&
            patterns.some((regex) => regex.test(event.title) || regex.test(event.description || '')),
        );
        if (matchedEvents.length) {
          filteredEventsByDate[date] = matchedEvents;
        }
      });
    } else {
      Object.keys(this.eventsByDate).forEach((date) => {
        const matchedEvents = this.eventsByDate[date].filter((event) =>
          this.filteredCategories.includes(event.category),
        );
        if (matchedEvents.length) {
          filteredEventsByDate[date] = matchedEvents;
        }
      });
      this.selectedSearchPattern = {};
    }
    this.displayedEventsByDate = filteredEventsByDate;
  }

  toggleRegexFilter(key: string): void {
    if (key in this.selectedSearchPattern) {
      delete this.selectedSearchPattern[key];
      this.applyFilters();
      return;
    }

    const pattern = this.searchPatterns.find((sp) => sp.name === key)?.pattern;
    if (!pattern) return;

    this.selectedSearchPattern[key] = pattern;
    this.applyFilters();
  }

  resetRegexFilter(): void {
    this.searchInputRegex.setValue('');
    this.selectedSearchPattern = {};
    this.applyFilters();
  }

  toggleCategoryFilter(category: string): void {
    const index = this.filteredCategories.indexOf(category);
    if (index > -1) {
      this.filteredCategories.splice(index, 1);
    } else {
      this.filteredCategories.push(category);
    }
    this.applyFilters();
  }

  selectAllCategories(): void {
    this.filteredCategories = this.categories.map((c) => c.name);
    this.applyFilters();
  }

  deselectAllCategories(): void {
    this.filteredCategories = [];
    this.applyFilters();
  }

  openEventDetails(event: CaseEvent): void {
    const eventCopy = { ...event };
    if (eventCopy.closes) {
      eventCopy.closes = this.events.find((e) => e.guid === eventCopy.closes)?.title || undefined;
    }

    if (eventCopy.category === 'TASK' && this.closedEventsGUID.has(eventCopy.guid)) {
      eventCopy.closedBy = this.events.find((e) => e.closes === eventCopy.guid) || undefined;
    }

    this.dialogService.open(CaseEventDetailsModalComponent, {
      header: 'Ev. details',
      modal: true,
      appendTo: 'body',
      closable: true,
      focusOnShow: false,
      width: '50vw',
      dismissableMask: true,
      breakpoints: { '960px': '90vw' },
      data: { tz: this.timezone, event: eventCopy },
    });
  }

  toggleFilterMode(): void {
    if (this.isFilterMode) {
      this.filteredCategories = [];
      this.displayedEventsByDate = { ...this.eventsByDate };
      this.isFilterMode = false;
    } else {
      this.filteredCategories = this.categories.map((c) => c.name);
      this.searchInputRegex.setValue('');
      this.selectedSearchPattern = {};
      this.isFilterMode = true;
    }
  }

  openEventModal(injectedEvent: CaseEvent | null = null, currentForm: Partial<CaseEvent> | null = null): void {
    const modal = this.dialogService.open(EventCreateModalComponent, {
      header: 'Create Event',
      modal: true,
      appendTo: 'body',
      closable: true,
      focusOnShow: false,
      width: '50vw',
      breakpoints: { '960px': '90vw' },
      data: {
        caseID: this.caseMeta?.guid,
        categories: this.categories,
        pending: this.taskEvents.filter((ev) => !this.closedEventsGUID.has(ev.guid)),
        currentForm: currentForm ?? { ...this.eventForm.value },
        injEvent: injectedEvent,
      },
    });

    modal.onClose.pipe(take(1)).subscribe((data) => {
      if (!data) return;
      this.createEvent(data);
    });
  }

  closeTask(event: CaseEvent): void {
    this.openEventModal(null, { title: `[OK] ${event.title}`, closes: event.guid });
  }

  clonEdit(eventToClone: CaseEvent) {
    const eventCopy = { ...eventToClone };
    if (eventCopy.closes) eventCopy.closes = this.events.find((ev) => ev.guid === eventCopy.closes)?.guid;

    const modal = this.dialogService.open(EventCreateModalComponent, {
      header: 'Clone Event',
      modal: true,
      appendTo: 'body',
      closable: true,
      focusOnShow: false,
      width: '50vw',
      breakpoints: { '960px': '90vw' },
      data: {
        caseID: this.caseMeta?.guid,
        categories: [...this.categories],
        pending: this.taskEvents.filter((ev) => !this.closedEventsGUID.has(ev.guid) || ev.guid === eventToClone.closes),
        currentForm: { ...this.eventForm.value },
        injEvent: eventCopy,
      },
    });

    modal.onClose.pipe(take(1)).subscribe({
      next: (data) => {
        if (!data) return;

        if (data['closes']) {
          let eventClosed = this.events.find((e) => e.guid == data['closes']);
          if (eventClosed) {
            if (new Date(eventClosed.date)?.getTime() > new Date(data.date).getTime()) {
              this.utilsService.toast(
                'error',
                'Error',
                'Task is newer than Event: closing Event date cannot be inferior to Task date',
                6000,
              );
              return;
            }
          }
        }

        this.apiService
          .trashEvent(this.caseMeta?.guid!, eventToClone.guid)
          .pipe(take(1))
          .subscribe({
            complete: () => {
              this.apiService.postCaseEvent(data, this.caseMeta!.guid).pipe(take(1)).subscribe();
            },
          });
      },
    });
  }

  getCategoryIcon(category: string): string {
    return this.categories.find((c) => c.name === category)?.icon || '';
  }

  openCategoryMenu(event: any): void {
    this.categoryMenuItems = [
      {
        label: 'Categories',
        items: this.categories.map((c) => ({
          label: c.name,
          icon: c.icon,
          command: () => this.eventForm.get('category')?.setValue(c.name),
        })),
      },
    ];
    this.categoryMenu.toggle(event);
  }

  trashEvent(event: CaseEvent): void {
    const modal = this.dialogService.open(YesNoModalComponent, {
      header: 'Trash Event',
      modal: true,
      closable: true,
      focusOnShow: false,
      dismissableMask: true,
      breakpoints: { '640px': '90vw' },
      data: `You are about to trash ${event.title.substring(0, Math.min(event.title.length, 20))}... Are you sure?`,
    });

    modal.onClose.pipe(take(1)).subscribe((confirmed) => {
      if (!confirmed) return;

      this.apiService.trashEvent(this.caseMeta!.guid, event.guid).pipe(take(1)).subscribe();
    });
  }

  toggleStarEvent(event: CaseEvent): void {
    this.apiService.starEventToggle(event.guid, this.caseMeta!.guid).pipe(take(1)).subscribe();
  }

  openSettingsModal(): void {
    if (!this.caseMeta) return;

    this.caseForm.setValue({
      name: this.caseMeta.name,
      acs: this.caseMeta.acs,
      tsid: this.caseMeta.tsid,
      description: this.caseMeta.description,
    });

    this.apiService
      .getIdentities()
      .pipe(take(1))
      .subscribe((identities) => {
        this.acsGroups = [
          {
            label: 'Users',
            items: identities.users.map((u) => ({ label: u, value: u })).sort((a, b) => (a.label > b.label ? 1 : -1)),
          },
          {
            label: 'Groups',
            items: identities.groups.map((g) => ({ label: g, value: g })).sort((a, b) => (a.label > b.label ? 1 : -1)),
          },
        ];
      });

    this.apiService
      .getConstant()
      .pipe(take(1))
      .subscribe({
        next: (constant) => {
          if (constant.allow_empty_acs) {
            this.caseForm.get('acs')?.removeValidators(Validators.required);
            this.caseForm.get('acs')?.updateValueAndValidity();
          }
        },
      });

    if (this.caseMeta.managed || this.caseMeta.closed) this.caseForm.disable();
    this.isSettingsOpened = true;
  }

  enableCaseForm() {
    if (this.caseMeta?.closed) {
      this.utilsService.toast('error', 'Error', 'Case is closed');
      return;
    }
    this.caseForm.enable();
  }

  toggleUTCDisplay(): void {
    this.updateCase({ utc_display: this.caseMeta!.utc_display });
  }

  closeCase(): void {
    this.updateCase({ closed: new Date().toISOString() });

    setTimeout(() => {
      if (!this.caseMeta?.closed) return;
      this.isDisplayingSplash = true;
      this.isReadonly = true;
      this.events = [];
      this.transformEventsToEventsByDate();
    }, 200);
  }

  reopenCase(): void {
    this.updateCase({ closed: '' });

    setTimeout(() => {
      if (this.caseMeta?.closed) return;
      this.isDisplayingSplash = false;
      this.isReadonly = false;
      this.subscribeToCaseEvents();
    }, 200);
  }

  openTrashModal(): void {
    this.trashEvents$ = this.apiService
      .getCaseTrash(this.caseMeta!.guid)
      .pipe(map((events) => events.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())));
    this.isTrashOpened = true;
  }

  restoreEvent(ev: CaseEvent & { gray?: boolean }): void {
    ev.gray = true;
    this.apiService.restoreEvent(ev.guid, this.caseMeta!.guid).pipe(take(1)).subscribe();
  }

  deleteEvent(ev: CaseEvent) {
    if (!this.caseMeta || !this.caseMeta.name) return;
    const modal = this.dialogService.open(DeleteConfirmModalComponent, {
      header: 'Confirm to delete',
      modal: true,
      closable: true,
      dismissableMask: true,
      breakpoints: {
        '640px': '90vw',
      },
      data: ev.title.substring(0, Math.min(ev.title.length, 20)),
    });

    modal.onClose.pipe(take(1)).subscribe((confirmed: boolean) => {
      if (!confirmed) return;
      this.apiService
        .deleteEvent(this.caseMeta!.guid, ev.guid)
        .pipe(take(1))
        .subscribe({
          next: () =>
            (this.trashEvents$ = this.apiService
              .getCaseTrash(this.caseMeta!.guid)
              .pipe(map((events) => events.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())))),
        });
    });
  }

  deleteCase() {
    if (!this.caseMeta || !this.caseMeta.name) return;
    const modal = this.dialogService.open(DeleteConfirmModalComponent, {
      header: 'Confirm to delete',
      modal: true,
      closable: true,
      dismissableMask: true,
      breakpoints: {
        '640px': '90vw',
      },
      data: this.caseMeta?.name,
    });

    modal.onClose.pipe(take(1)).subscribe((confirmed: boolean) => {
      if (!confirmed) return;
      this.apiService.deleteCase(this.caseMeta!.guid).pipe(take(1)).subscribe();
    });
  }

  openExportModal(): void {
    if (!this.events.length) {
      this.utilsService.toast('warn', 'Warning', 'No event to export');
      return;
    }
    this.mdOptionFields = Object.keys(this.events[0]).map((k) => ({
      label: k,
      value: k,
    }));
    this.mdOptionFieldsInput.setValue(['date', 'description', 'title']);
    this.isExportsOpened = true;
  }

  generateExport(): void {
    if (this.exportOptionFormatValue === 'md') {
      this.apiService
        .exportCaseEvents(
          this.caseMeta!.guid,
          this.exportOptionEventValue === 'starred',
          this.mdOptionFieldsInput.value as string[],
        )
        .pipe(take(1))
        .subscribe((blob) => {
          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `Carbon_${this.caseMeta!.guid}_${new Date().toISOString().split('T')[0]}.md`;
          link.click();
          link.remove();
          URL.revokeObjectURL(url);
        });
    } else {
      const starredOnly = this.exportOptionEventValue === 'starred';
      const dataToExport = this.events.filter((e) => (starredOnly ? e.starred : true));
      const blob = new Blob([JSON.stringify(dataToExport, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `Carbon_${this.caseMeta!.guid}_${new Date().toISOString().split('T')[0]}.json`;
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    }
  }
}
