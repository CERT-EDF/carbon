import { HttpErrorResponse, HttpEvent, HttpHandlerFn, HttpRequest } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, Observable, throwError } from 'rxjs';
import { UtilsService } from './utils.service';
import { ApiService } from './api.service';

export const Interceptor = (req: HttpRequest<unknown>, next: HttpHandlerFn): Observable<HttpEvent<unknown>> => {
  const apiService = inject(ApiService);
  const utilsService = inject(UtilsService);

  if (!req.headers.has('Content-Type')) {
    req = req.clone({ setHeaders: { 'Content-Type': 'application/json' } });
  }

  return next(req).pipe(
    catchError((err: HttpErrorResponse) => {
      if (err.status == 400) {
        console.error(err);
        utilsService.toast('error', 'Bad Request', `${err.error || 'Unknown error, check console for details'}`);
      }

      if (err.status == 401) {
        apiService.unauthorizedRedirectLogin();
      }

      if (err.status == 403) {
        utilsService.navigateHomeWithError();
      }

      if (err.status == 404) {
        utilsService.toast('error', 'Not found', `${err.error || 'Entity not found, check console for details'}`, 3500);
        utilsService.navigateHomeWithError();
      }

      if (err.status == 502) {
        utilsService.toast('error', 'Bad Gateway', 'Verify the server is up and running');
        apiService.unauthorizedRedirectLogin();
        return throwError(() => `Bad Gateway: ${err.error || 'Unknown error, check console for details'}`);
      }

      return throwError(() => err);
    }),
  );
};
