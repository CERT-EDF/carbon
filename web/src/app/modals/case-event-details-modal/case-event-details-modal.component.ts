import { Component } from '@angular/core';
import { ClipboardModule } from '@angular/cdk/clipboard';
import { DatePipe } from '@angular/common';
import { ButtonModule } from 'primeng/button';
import { CaseEvent } from '../../types/event';
import { DynamicDialogConfig, DynamicDialogRef } from 'primeng/dynamicdialog';
import { AvatarModule } from 'primeng/avatar';
import { AvatarGroupModule } from 'primeng/avatargroup';
import { MarkdownModule } from 'ngx-markdown';
import { TooltipModule } from 'primeng/tooltip';

@Component({
  selector: 'app-case-event-detail-modal',
  standalone: true,
  imports: [ButtonModule, DatePipe, ClipboardModule, MarkdownModule, TooltipModule, AvatarModule, AvatarGroupModule],
  templateUrl: './case-event-details-modal.component.html',
  styleUrls: ['./case-event-details-modal.component.scss'],
})
export class CaseEventDetailsModalComponent {
  tz: string = 'UTC';
  event: CaseEvent | undefined;

  constructor(
    private ref: DynamicDialogRef,
    private config: DynamicDialogConfig,
  ) {
    this.event = this.config.data.event;
    if (!this.event) this.close();
    this.tz = this.config.data.tz;
  }

  close(): void {
    this.ref.close();
  }
}
