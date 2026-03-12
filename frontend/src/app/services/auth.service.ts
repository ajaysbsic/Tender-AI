import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { tap, map } from 'rxjs/operators';
import { environment } from '@environments/environment';

interface LoginRequest {
  email: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
  user_email: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = `${environment.apiUrl}/auth`;
  private tokenKey = 'tender_iq_token';
  private userKey = 'tender_iq_user';

  private isLoggedInSubject = new BehaviorSubject<boolean>(this.hasToken());
  private userEmailSubject = new BehaviorSubject<string>(this.getStoredEmail());

  isLoggedIn$ = this.isLoggedInSubject.asObservable();
  userEmail$ = this.userEmailSubject.asObservable();

  constructor(private http: HttpClient) {}

  login(email: string, password: string): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.apiUrl}/login`, {
      email,
      password
    }).pipe(
      tap(response => {
        this.setToken(response.access_token);
        this.setUserEmail(response.user_email);
        this.isLoggedInSubject.next(true);
        this.userEmailSubject.next(response.user_email);
      })
    );
  }

  register(email: string, password: string, companyName: string): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.apiUrl}/register`, {
      email,
      password,
      company_name: companyName
    }).pipe(
      tap(response => {
        this.setToken(response.access_token);
        this.setUserEmail(response.user_email);
        this.isLoggedInSubject.next(true);
        this.userEmailSubject.next(response.user_email);
      })
    );
  }

  logout(): void {
    this.clearToken();
    this.clearUserEmail();
    this.isLoggedInSubject.next(false);
    this.userEmailSubject.next('');
  }

  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  private setToken(token: string): void {
    localStorage.setItem(this.tokenKey, token);
  }

  private clearToken(): void {
    localStorage.removeItem(this.tokenKey);
  }

  private hasToken(): boolean {
    return !!localStorage.getItem(this.tokenKey);
  }

  private getStoredEmail(): string {
    return localStorage.getItem(this.userKey) || '';
  }

  private setUserEmail(email: string): void {
    localStorage.setItem(this.userKey, email);
  }

  private clearUserEmail(): void {
    localStorage.removeItem(this.userKey);
  }
}
