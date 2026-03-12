import { Injectable } from '@angular/core';
import { HttpClient, HttpRequest, HttpEvent } from '@angular/common/http';
import { Observable, Subject, BehaviorSubject } from 'rxjs';
import { environment } from '@environments/environment';

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

export interface UploadState {
  status: 'idle' | 'uploading' | 'completed' | 'error';
  progress: UploadProgress | null;
  error: string | null;
  tenderId: string | null;
}

@Injectable({
  providedIn: 'root'
})
export class UploadService {
  private apiUrl = environment.apiUrl;
  private uploadState$ = new BehaviorSubject<UploadState>({
    status: 'idle',
    progress: null,
    error: null,
    tenderId: null
  });

  private cancelUpload$ = new Subject<void>();

  constructor(private http: HttpClient) { }

  getUploadState(): Observable<UploadState> {
    return this.uploadState$.asObservable();
  }

  uploadTenderWithProgress(
    file: File,
    companyDescription?: string
  ): Observable<HttpEvent<any>> {
    const formData = new FormData();
    formData.append('file', file);
    if (companyDescription) {
      formData.append('company_description', companyDescription);
    }

    const req = new HttpRequest('POST', `${this.apiUrl}/tender/upload`, formData, {
      reportProgress: true,
      responseType: 'json'
    });

    this.updateState({ status: 'uploading', error: null });

    return this.http.request(req);
  }

  resetUploadState(): void {
    this.updateState({
      status: 'idle',
      progress: null,
      error: null,
      tenderId: null
    });
  }

  private updateState(partial: Partial<UploadState>): void {
    const current = this.uploadState$.value;
    this.uploadState$.next({ ...current, ...partial });
  }

  updateProgress(loaded: number, total: number): void {
    const percentage = Math.round((loaded / total) * 100);
    this.updateState({
      progress: { loaded, total, percentage }
    });
  }

  setCompleted(tenderId: string): void {
    this.updateState({
      status: 'completed',
      tenderId
    });
  }

  setError(error: string): void {
    this.updateState({
      status: 'error',
      error
    });
  }
}
