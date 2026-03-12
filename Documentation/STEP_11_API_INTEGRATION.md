# Step 11: Angular API Integration & UX Implementation

## Overview
This step implements real-time communication between the Angular frontend and FastAPI backend, with progress tracking, status polling, and comprehensive UX states.

## Architecture Diagram

```
Frontend (Angular)
├── Upload Service
│   ├── File upload with progress
│   ├── Progress tracking (0-100%)
│   └── Error handling
├── Polling Service
│   ├── Status check every 2 seconds
│   ├── Result retrieval
│   └── Auto-retry on failure
├── Components
│   ├── Tender Upload (progress bar)
│   ├── Dashboard (real-time status)
│   ├── Evaluations (results display)
│   └── Report Download
└── Interceptors
    └── Auth/Error handling

Backend (FastAPI)
├── /api/upload/ (POST)
├── /api/status/{job_id} (GET)
└── /api/result/{job_id} (GET)
```

## Implemented Services

### 1. Upload Service with Progress

```typescript
// upload.service.ts
uploadFile(file: File, companyDescription?: string): Observable<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (companyDescription) {
    formData.append('company_description', companyDescription);
  }

  // Upload with progress events
  return this.http.post<UploadResponse>(
    'http://localhost:8000/api/upload/',
    formData,
    {
      reportProgress: true,
      observe: 'events'
    }
  );
}

// Usage in component
uploadFile() {
  this.uploadService.uploadFile(file, description).subscribe({
    next: (event) => {
      if (event.type === HttpEventType.UploadProgress) {
        this.uploadProgress = Math.round(100 * event.loaded / event.total);
      }
      if (event.type === HttpEventType.Response) {
        this.jobId = event.body.job_id;
        this.startPolling();
      }
    },
    error: (err) => this.handleError(err)
  });
}
```

### 2. Polling Service for Status

```typescript
// polling.service.ts
pollStatus(jobId: string): Observable<StatusResponse> {
  // Poll every 2 seconds
  return interval(2000).pipe(
    switchMap(() => this.http.get<StatusResponse>(
      `http://localhost:8000/api/status/${jobId}`
    )),
    takeUntil(this.stopPolling$),
    retry({ count: 3, delay: 1000 })
  );
}

getResult(jobId: string): Observable<TenderEvaluation> {
  return this.http.get<TenderEvaluation>(
    `http://localhost:8000/api/result/${jobId}`
  );
}
```

### 3. Component State Management

```typescript
// tender-upload.component.ts
export class TenderUploadComponent implements OnInit, OnDestroy {
  uploadState: 'idle' | 'uploading' | 'processing' | 'completed' | 'error';
  uploadProgress = 0;
  processingProgress = 0;
  statusMessage = '';
  jobId: string | null = null;
  evaluationResult: TenderEvaluation | null = null;
  error: string | null = null;

  private destroy$ = new Subject<void>();

  ngOnInit() {
    this.uploadState = 'idle';
  }

  onFileSelected(event: any) {
    const file = event.target.files[0];
    if (file) {
      this.validateAndUpload(file);
    }
  }

  validateAndUpload(file: File) {
    // Validation...
    this.uploadState = 'uploading';
    this.error = null;

    this.uploadService.uploadFile(file, this.companyDescription)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (event) => this.handleUploadEvent(event),
        error: (err) => this.handleError(err)
      });
  }

  private handleUploadEvent(event: HttpEvent<any>) {
    if (event.type === HttpEventType.UploadProgress) {
      this.uploadProgress = Math.round(100 * event.loaded / event.total);
      this.statusMessage = `Uploading: ${this.uploadProgress}%`;
    } else if (event.type === HttpEventType.Response) {
      this.uploadState = 'processing';
      this.jobId = event.body.job_id;
      this.startProcessingPolling();
    }
  }

  private startProcessingPolling() {
    this.pollingService.pollStatus(this.jobId!)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (status) => {
          this.processingProgress = status.progress;
          this.statusMessage = status.message;

          if (status.status === 'completed') {
            this.completeAnalysis();
          } else if (status.status === 'failed') {
            this.handleError(new Error(status.error));
          }
        },
        error: (err) => this.handleError(err)
      });
  }

  private completeAnalysis() {
    this.uploadState = 'completed';
    this.pollingService.getResult(this.jobId!)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (result) => {
          this.evaluationResult = result;
          this.statusMessage = 'Analysis complete!';
        },
        error: (err) => this.handleError(err)
      });
  }

  private handleError(error: any) {
    this.uploadState = 'error';
    this.error = error.message || 'An error occurred';
    this.statusMessage = '';
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
```

## UX States Flowchart

```
┌─────────────┐
│   IDLE      │ Initial state
└──────┬──────┘
       │ File selected
       ▼
┌─────────────────────┐
│   UPLOADING         │ File upload in progress
│ 0% ████░░░░░░ 100%  │ Progress bar updates
└──────┬──────────────┘
       │ Upload complete
       ▼
┌──────────────────────┐
│   PROCESSING         │ Server analyzing
│ ░░░░░░░░░░░░░░░░░░  │ Status polling
└──────┬───────────────┘
       │ Analysis complete
       ├─────────────────┬──────────────────┐
       │                 │                  │
       ▼                 ▼                  ▼
  ┌─────────┐      ┌──────────┐      ┌──────────┐
  │COMPLETED│      │  ERROR   │      │ TIMEOUT  │
  │ Results │      │Show error│      │ Retry    │
  └─────────┘      └──────────┘      └──────────┘
```

## HTTP Endpoints Used

### 1. File Upload
```
POST /api/upload/
Content-Type: multipart/form-data

Form Data:
- file: File
- company_description: string (optional)

Response:
{
  "job_id": "uuid-string",
  "status": "queued"
}
```

### 2. Status Check
```
GET /api/status/{job_id}

Response:
{
  "job_id": "uuid-string",
  "status": "processing|completed|failed",
  "progress": 0-100,
  "message": "Processing eligibility requirements..."
}
```

### 3. Get Results
```
GET /api/result/{job_id}

Response:
{
  "job_id": "uuid-string",
  "document_name": "tender.pdf",
  "overall_score": 78,
  "bid_recommendation": "RECOMMENDED",
  "eligibility": { ... },
  "risks": [ ... ],
  "effort_estimate": { ... },
  "created_at": "2024-01-15T10:30:00"
}
```

## Material Progress Components

### Upload Progress
```html
<mat-card *ngIf="uploadState !== 'idle'">
  <mat-card-title>{{ 'tender.uploadingDocument' | translate }}</mat-card-title>
  
  <mat-progress-bar 
    *ngIf="uploadState === 'uploading'"
    mode="determinate" 
    [value]="uploadProgress"
    color="primary">
  </mat-progress-bar>
  
  <div class="progress-text">
    {{ uploadProgress }}% {{ 'tender.uploaded' | translate }}
  </div>
</mat-card>
```

### Processing Progress
```html
<mat-card *ngIf="uploadState === 'processing'">
  <mat-card-title>{{ 'tender.analyzeDocument' | translate }}</mat-card-title>
  
  <mat-progress-spinner
    mode="indeterminate"
    diameter="50"
    color="primary">
  </mat-progress-spinner>
  
  <p>{{ statusMessage }}</p>
  <small>{{ 'tender.mayTakeTime' | translate }}</small>
</mat-card>
```

### Completed State
```html
<mat-card *ngIf="uploadState === 'completed'">
  <mat-card-title>{{ 'tender.analysisComplete' | translate }}</mat-card-title>
  
  <div class="results-summary">
    <div class="score">{{ evaluationResult.overall_score }}</div>
    <div class="recommendation">
      {{ evaluationResult.bid_recommendation }}
    </div>
  </div>
  
  <button mat-raised-button 
          color="primary"
          [routerLink]="['/evaluations', jobId]">
    {{ 'evaluations.viewDetails' | translate }}
  </button>
</mat-card>
```

### Error State
```html
<mat-card *ngIf="uploadState === 'error'">
  <mat-card-title class="error">
    {{ 'tender.processingFailed' | translate }}
  </mat-card-title>
  
  <mat-error>{{ error }}</mat-error>
  
  <button mat-raised-button color="warn" (click)="reset()">
    {{ 'tender.tryAgain' | translate }}
  </button>
</mat-card>
```

## Error Handling Strategy

### 1. Network Errors
```typescript
if (!navigator.onLine) {
  this.error = 'No internet connection';
  return;
}
```

### 2. Upload Errors
```typescript
uploadError$ = this.uploadService.error$.pipe(
  catchError(err => {
    if (err.status === 413) {
      return 'File too large';
    }
    if (err.status === 415) {
      return 'Invalid file type';
    }
    return 'Upload failed';
  })
);
```

### 3. Polling Timeout
```typescript
pollStatus(jobId: string): Observable<StatusResponse> {
  return interval(2000).pipe(
    timeout(30000), // 30 second timeout
    switchMap(() => this.statusCheck(jobId)),
    retry({ count: 3, delay: 1000 }),
    catchError(err => {
      if (err instanceof TimeoutError) {
        this.error = 'Analysis taking longer than expected';
      }
      throw err;
    })
  );
}
```

## Dashboard Real-Time Updates

```typescript
// dashboard.component.ts
export class DashboardComponent implements OnInit {
  pendingTenders$: Observable<TenderJob[]>;

  constructor(private pollingService: PollingService) {}

  ngOnInit() {
    // Refresh pending tenders every 5 seconds
    this.pendingTenders$ = interval(5000).pipe(
      startWith(0),
      switchMap(() => this.pollingService.getPendingJobs()),
      shareReplay(1)
    );
  }
}
```

Template:
```html
<mat-card class="pending-tenders">
  <mat-card-title>{{ 'dashboard.processingTenders' | translate }}</mat-card-title>
  
  <mat-list>
    <mat-list-item *ngFor="let job of pendingTenders$ | async">
      <mat-icon matListItemIcon>hourglass_bottom</mat-icon>
      
      <div matListItemTitle>{{ job.document_name }}</div>
      
      <mat-progress-bar 
        matListItemMeta
        mode="determinate"
        [value]="job.progress">
      </mat-progress-bar>
      
      <span>{{ job.progress }}%</span>
    </mat-list-item>
  </mat-list>
</mat-card>
```

## Report Download

```typescript
downloadReport(jobId: string): void {
  this.http.get(
    `http://localhost:8000/api/report/${jobId}`,
    { responseType: 'blob' }
  ).subscribe(blob => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `tender-evaluation-${jobId}.pdf`;
    link.click();
    window.URL.revokeObjectURL(url);
  });
}
```

## Testing Checklist

- [ ] File upload shows progress bar
- [ ] Progress updates correctly (0-100%)
- [ ] Status polling starts after upload
- [ ] Processing progress shows
- [ ] Results display when complete
- [ ] Error handling works
- [ ] Timeout handled gracefully
- [ ] Dashboard updates in real-time
- [ ] Report downloads correctly
- [ ] All UI states visible and functional
- [ ] Keyboard navigation works
- [ ] Mobile layout responsive

## Performance Considerations

1. **Polling Interval**: 2 seconds (balance between freshness and load)
2. **Timeout**: 30 seconds (configurable per requirements)
3. **Retry Logic**: 3 attempts with 1 second delay
4. **Result Caching**: Store results locally to avoid re-fetching
5. **Memory Management**: Unsubscribe on component destroy

## Future Enhancements

1. **WebSocket**: Real-time updates instead of polling
2. **Background Tasks**: Notify when results ready
3. **Bulk Upload**: Multiple files simultaneously
4. **Progress Persistence**: Resume interrupted uploads
5. **Advanced Analytics**: Track upload/processing times
