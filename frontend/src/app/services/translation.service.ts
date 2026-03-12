import { Injectable } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { BehaviorSubject, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class TranslationService {
  private currentLanguageSubject = new BehaviorSubject<string>('en');
  public currentLanguage$ = this.currentLanguageSubject.asObservable();

  private currentDirectionSubject = new BehaviorSubject<'ltr' | 'rtl'>('ltr');
  public currentDirection$ = this.currentDirectionSubject.asObservable();

  private supportedLanguages = [
    { code: 'en', label: 'English', dir: 'ltr' as const },
    { code: 'ar', label: 'العربية', dir: 'rtl' as const }
  ];

  constructor(private translateService: TranslateService) {
    this.initializeLanguage();
  }

  private initializeLanguage(): void {
    const savedLanguage = localStorage.getItem('language') || 'en';
    this.setLanguage(savedLanguage);
  }

  setLanguage(languageCode: string): void {
    const language = this.supportedLanguages.find(l => l.code === languageCode);
    
    if (language) {
      this.translateService.use(languageCode);
      this.currentLanguageSubject.next(languageCode);
      this.currentDirectionSubject.next(language.dir);
      
      // Update HTML attributes
      document.documentElement.lang = languageCode;
      document.documentElement.dir = language.dir;
      
      // Save preference
      localStorage.setItem('language', languageCode);
    }
  }

  getCurrentLanguage(): string {
    return this.currentLanguageSubject.value;
  }

  getCurrentDirection(): 'ltr' | 'rtl' {
    return this.currentDirectionSubject.value;
  }

  getSupportedLanguages() {
    return this.supportedLanguages;
  }

  getTranslation(key: string, interpolateParams?: any): Observable<string> {
    return this.translateService.get(key, interpolateParams);
  }

  instantTranslate(key: string, interpolateParams?: any): string {
    return this.translateService.instant(key, interpolateParams);
  }
}
