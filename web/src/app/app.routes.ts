import { Routes } from '@angular/router';
import { AuthComponent } from './components/auth/auth.component';
import { AuthGuard } from './services/auth.guard';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { CaseComponent } from './components/case/case.component';

export const routes: Routes = [
  { path: 'login', component: AuthComponent, title: 'Carbon - Authentication' },

  {
    path: '',
    canActivateChild: [AuthGuard],
    children: [
      { path: 'home', component: DashboardComponent, title: 'Carbon - Dashboard' },
      { path: 'case/:guid', component: CaseComponent, title: 'Carbon - Case' },
      { path: '**', redirectTo: '/home', pathMatch: 'full' },
    ],
  },

  { path: '**', redirectTo: '/login', pathMatch: 'full' },
];
