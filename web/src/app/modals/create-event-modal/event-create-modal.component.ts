import { Component } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { DatePickerModule } from 'primeng/datepicker';
import { DynamicDialogConfig, DynamicDialogRef } from 'primeng/dynamicdialog';
import { FloatLabelModule } from 'primeng/floatlabel';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { TabsModule } from 'primeng/tabs';
import { TextareaModule } from 'primeng/textarea';
import { FocusTrapModule } from 'primeng/focustrap';
import { ApiService } from '../../services/api.service';
import { CaseEvent, EventCategory } from '../../types/event';
import { map, Observable } from 'rxjs';
import { AsyncPipe, DatePipe } from '@angular/common';
import { MultiSelectModule } from 'primeng/multiselect';

@Component({
  selector: 'app-event-create-modal',
  imports: [
    TabsModule,
    CardModule,
    FloatLabelModule,
    InputTextModule,
    ButtonModule,
    SelectModule,
    DatePipe,
    DatePickerModule,
    ReactiveFormsModule,
    TextareaModule,
    FocusTrapModule,
    AsyncPipe,
    MultiSelectModule,
  ],
  standalone: true,
  templateUrl: './event-create-modal.component.html',
  styleUrl: './event-create-modal.component.scss',
})
export class EventCreateModalComponent {
  eventForm: FormGroup;
  users$: Observable<string[]>;
  today = new Date();
  cloneEvent: boolean = false;

  categories: EventCategory[];
  pending: CaseEvent[] = [];
  currentForm?: CaseEvent & { linkedEventID?: number };
  injEvent: CaseEvent | null = null;

  constructor(
    private apiService: ApiService,
    private ref: DynamicDialogRef,
    private config: DynamicDialogConfig,
    private fb: FormBuilder,
  ) {
    this.eventForm = this.fb.group({
      title: ['', Validators.required],
      category: [null, Validators.required],
      date: null,
      dateHour: ['', Validators.pattern(/([0-1]?[0-9]|2[0-3]):[0-5][0-9]/)],
      dueDate: null,
      description: '',
      assignees: '',
      closes: null,
    });

    let c = this.config.data;
    if (c.isPublicCase) {
      this.users$ = this.apiService.getCaseAvailableUsers(this.config.data.caseID);
    } else {
      this.users$ = this.apiService.getIdentities().pipe(map((identity) => identity.users));
    }

    this.categories = c.categories;
    this.pending = c.pending;

    if (c.currentForm) {
      this.eventForm.get('category')?.setValue(c.currentForm.category);
      if (c.currentForm?.closes) this.eventForm.get('closes')?.setValue(c.currentForm.closes);
      if (c.currentForm?.title) this.eventForm.get('title')?.setValue(c.currentForm.title);
    } else this.eventForm.get('category')?.setValue('INFO');

    if (c.injEvent) {
      if (c.injEvent.guid) this.cloneEvent = true;

      Object.entries(c.injEvent).forEach(([k, v]) => {
        if (this.eventForm.get(k)) {
          this.eventForm.get(k)?.setValue(v);
        }
      });

      if (c.injEvent.date) {
        let date = new Date(c.injEvent.date);
        this.eventForm.get('date')?.setValue(new Date(date));
        this.eventForm.get('dateHour')?.setValue(new Date(date));
      }
    }
  }

  closeDialog(exit: boolean = false) {
    if (exit) {
      this.ref.close(undefined);
      return;
    }

    //Normalize date/dateHour to created
    let ret = this.eventForm.value;
    if (ret['dateHour']) {
      let date = new Date(ret['date']);
      let datetime = new Date(ret['dateHour']);
      date.setHours(datetime.getHours(), datetime.getMinutes());
      ret['date'] = date;
      delete ret['dateHour'];
    } else delete ret['dateHour'];

    if (!ret['duedate']) delete ret['duedate'];
    if (!ret['closes']) delete ret['closes'];

    this.ref.close(ret);
  }
}
