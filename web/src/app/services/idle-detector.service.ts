import { Injectable } from '@angular/core';
import { BehaviorSubject, fromEvent } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class IdleDetectorService {
  public idle$: BehaviorSubject<boolean> = new BehaviorSubject(false);
  public wake$: BehaviorSubject<boolean> = new BehaviorSubject(true);

  public isIdle = false;
  private idleAfterSeconds = 5;
  private countDown: any;

  constructor() {
    fromEvent(document, 'mousemove').subscribe(() => this.onInteraction());
    fromEvent(document, 'keydown').subscribe(() => this.onInteraction());
  }

  onInteraction() {
    // Is idle and interacting, emit Wake
    if (this.isIdle) {
      this.isIdle = false;
      this.wake$.next(true);
    }

    clearTimeout(this.countDown);
    this.countDown = setTimeout(() => {
      this.isIdle = true;
      this.idle$.next(true);
    }, this.idleAfterSeconds * 1000);
  }
}
