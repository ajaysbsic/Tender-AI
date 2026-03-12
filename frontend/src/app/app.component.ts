import { Component, OnInit, ViewChild } from '@angular/core';
import { Router } from '@angular/router';
import { MatSidenav } from '@angular/material/sidenav';
import { TranslateService } from '@ngx-translate/core';
import { AuthService } from '@services/auth.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {
  @ViewChild('sidenav') sidenav!: MatSidenav;

  title = 'TenderIQ';
  isLoggedIn = false;
  userEmail = '';
  currentLanguage = 'en';

  navItems = [
    { label: 'Dashboard', route: '/dashboard', icon: 'dashboard' },
    { label: 'Upload Tender', route: '/tender', icon: 'upload_file' },
    { label: 'Evaluations', route: '/evaluations', icon: 'assessment' },
    { label: 'Profile', route: '/profile', icon: 'person' }
  ];

  languages = [
    { code: 'en', label: 'English', dir: 'ltr' },
    { code: 'ar', label: 'العربية', dir: 'rtl' }
  ];

  constructor(
    private authService: AuthService,
    private router: Router,
    private translateService: TranslateService
  ) {
    this.initializeLanguage();
  }

  ngOnInit(): void {
    this.authService.isLoggedIn$.subscribe(loggedIn => {
      this.isLoggedIn = loggedIn;
    });

    this.authService.userEmail$.subscribe(email => {
      this.userEmail = email;
    });
  }

  private initializeLanguage(): void {
    const savedLanguage = localStorage.getItem('language') || 'en';
    this.currentLanguage = savedLanguage;
    this.translateService.use(savedLanguage);
    const direction = savedLanguage === 'ar' ? 'rtl' : 'ltr';
    document.documentElement.dir = direction;
    document.documentElement.lang = savedLanguage;
  }

  changeLanguage(lang: string): void {
    this.translateService.use(lang);
    this.currentLanguage = lang;
    const direction = lang === 'ar' ? 'rtl' : 'ltr';
    document.documentElement.dir = direction;
    document.documentElement.lang = lang;
    localStorage.setItem('language', lang);
  }

  navigateTo(route: string): void {
    this.router.navigate([route]);
    this.sidenav.close();
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
