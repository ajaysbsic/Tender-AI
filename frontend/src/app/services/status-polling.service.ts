import { Injectable, OnDestroy } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject, interval, BehaviorSubject, of } from 'rxjs';
import { takeUntil, switchMap, tap, catchError, debounceTime, map } from 'rxjs/operators';
import { environment } from '@environments/environment';

export interface TenderStatus {
  tender_id: string;
  status: 'pending' | 'uploaded' | 'processing' | 'completed' | 'failed' | 'error';
  progress_percentage?: number;
  message?: string;
  evaluation_id?: string;
  error_message?: string;
  processing_time_seconds?: number;
}

@Injectable({
  providedIn: 'root'
})
export class StatusPollingService implements OnDestroy {
  private apiUrl = environment.apiUrl;
  private destroy$ = new Subject<void>();
  private activePolls = new Map<string, Subject<void>>();
  private tenderStatus$ = new BehaviorSubject<TenderStatus | null>(null);
  private pollingResults$ = new Subject<TenderStatus>();
  
  // Configuration
  private readonly POLL_INTERVAL_MS = 2000; // 2 seconds
  private readonly MAX_POLLS = 300; // 10 minutes max (300 * 2s)
  private pollCounts = new Map<string, number>();

  constructor(private http: HttpClient) { }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.stopAllPolls();
  }

  /**
   * Start polling for tender status
   */
  startPolling(tenderId: string): Observable<TenderStatus> {
    // Stop any existing poll for this tender
    this.stopPolling(tenderId);

    // Create new cancellation subject for this poll
    const pollCancel$ = new Subject<void>();
    this.activePolls.set(tenderId, pollCancel$);
    this.pollCounts.set(tenderId, 0);

    return interval(this.POLL_INTERVAL_MS).pipe(
      debounceTime(100),
      switchMap(() => {
        const count = (this.pollCounts.get(tenderId) || 0) + 1;
        this.pollCounts.set(tenderId, count);

        // Stop polling if max attempts reached
        if (count > this.MAX_POLLS) {
          this.stopPolling(tenderId);
          return of({
            tender_id: tenderId,
            status: 'error' as const,
            error_message: 'Polling timeout: Processing is taking longer than expected'
          } as TenderStatus);
        }

        return this.getTenderStatus(tenderId);
      }),
      tap(status => {
        this.tenderStatus$.next(status);
        this.pollingResults$.next(status);

        // Stop polling when server reaches terminal state
        if (status.status === 'completed' || status.status === 'error' || status.status === 'failed') {
          this.stopPolling(tenderId);
        }
      }),
      catchError(error => {
        console.error('Polling error:', error);
        this.stopPolling(tenderId);
        return of({
          tender_id: tenderId,
          status: 'error' as const,
          error_message: error.message || 'Polling failed'
        } as TenderStatus);
      }),
      takeUntil(pollCancel$)
    );
  }

  /**
   * Stop polling for a specific tender
   */
  stopPolling(tenderId: string): void {
    const pollCancel$ = this.activePolls.get(tenderId);
    if (pollCancel$) {
      pollCancel$.next();
      pollCancel$.complete();
      this.activePolls.delete(tenderId);
      this.pollCounts.delete(tenderId);
    }
  }

  /**
   * Stop all active polls
   */
  stopAllPolls(): void {
    this.activePolls.forEach((poll$) => {
      poll$.next();
      poll$.complete();
    });
    this.activePolls.clear();
    this.pollCounts.clear();
  }

  /**
   * Get current tender status
   */
  getTenderStatus(tenderId: string): Observable<TenderStatus> {
    return this.http.get<TenderStatus>(
      `${this.apiUrl}/tender/${tenderId}/status`
    ).pipe(
      map((status) => {
        if (status.status === 'failed') {
          return {
            ...status,
            status: 'error',
            error_message: status.error_message || 'Processing failed on server'
          } as TenderStatus;
        }

        if (status.status === 'uploaded') {
          return {
            ...status,
            status: 'processing',
            message: status.message || 'Queued for processing...'
          } as TenderStatus;
        }

        return status;
      })
    );
  }

  /**
   * Get latest status from polling
   */
  getLatestStatus(): Observable<TenderStatus | null> {
    return this.tenderStatus$.asObservable();
  }

  /**
   * Get all polling results
   */
  getPollingResults(): Observable<TenderStatus> {
    return this.pollingResults$.asObservable();
  }

  /**
   * Check if currently polling a tender
   */
  isPolling(tenderId: string): boolean {
    return this.activePolls.has(tenderId);
  }

  /**
   * Get active tender IDs being polled
   */
  getActiveTenderIds(): string[] {
    return Array.from(this.activePolls.keys());
  }
}
