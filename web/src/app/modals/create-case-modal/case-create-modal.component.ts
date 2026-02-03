import { Component } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { DatePickerModule } from 'primeng/datepicker';
import { DynamicDialogRef } from 'primeng/dynamicdialog';
import { FloatLabelModule } from 'primeng/floatlabel';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { TabsModule } from 'primeng/tabs';
import { TextareaModule } from 'primeng/textarea';
import { CheckboxModule } from 'primeng/checkbox';
import { ApiService } from '../../services/api.service';
import { FocusTrapModule } from 'primeng/focustrap';
import { MultiSelectModule } from 'primeng/multiselect';
import { SelectItemGroup } from 'primeng/api';
import { Identity } from '../../types/API';
import { take } from 'rxjs';

@Component({
  selector: 'app-case-create-modal',
  imports: [
    TabsModule,
    CardModule,
    FloatLabelModule,
    InputTextModule,
    ButtonModule,
    CheckboxModule,
    SelectModule,
    DatePickerModule,
    ReactiveFormsModule,
    TextareaModule,
    FocusTrapModule,
    MultiSelectModule,
  ],
  standalone: true,
  templateUrl: './case-create-modal.component.html',
  styleUrl: './case-create-modal.component.scss',
})
export class CaseCreateModalComponent {
  caseForm: FormGroup;
  acsGroups: SelectItemGroup[] = [];

  constructor(
    private ref: DynamicDialogRef,
    private apiService: ApiService,
    private fb: FormBuilder,
  ) {
    this.caseForm = this.fb.group({
      tsid: '',
      name: ['', Validators.required],
      description: [''],
      acs: [null, Validators.required],
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

    this.apiService
      .getIdentities()
      .pipe(take(1))
      .subscribe({
        next: (identities: Identity) => {
          this.acsGroups = [];
          this.acsGroups.push({
            label: 'Users',
            items: identities.users
              .map((u) => {
                return { label: u, value: u };
              })
              .sort((a, b) => (a.label > b.label ? 1 : -1)),
          });
          this.acsGroups.push({
            label: 'Groups',
            items: identities.groups
              .map((g) => {
                return { label: g, value: g };
              })
              .sort((a, b) => (a.label > b.label ? 1 : -1)),
          });
        },
      });
  }

  closeDialog() {
    let ret = this.caseForm.value;
    if (!ret['acs']) ret['acs'] = [];
    this.ref.close(ret);
  }
}
