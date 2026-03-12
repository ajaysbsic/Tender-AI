import { Component, ViewChild, ElementRef, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from '@services/api.service';
import { UploadService, UploadState } from '@services/upload.service';
import { StatusPollingService, TenderStatus } from '@services/status-polling.service';
import { MatSnackBar } from '@angular/material/snack-bar';
import { AuthService } from '@services/auth.service';
import { HttpEvent, HttpEventType, HttpResponse } from '@angular/common/http';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-tender',
  templateUrl: './tender.component.html',
  styleUrls: ['./tender.component.scss']
})
export class TenderComponent implements OnInit, OnDestroy {
  @ViewChild('fileInput') fileInput!: ElementRef<HTMLInputElement>;

  selectedFile: File | null = null;
  companyDescription = '';
  uploadProgress = 0;
  isUploading = false;
  uploadState: UploadState | null = null;
  processingStatus: TenderStatus | null = null;
  processingProgress = 0;

  dragover = false;
  userEmail = '';
  private destroy$ = new Subject<void>();

  constructor(
    private apiService: ApiService,
    private uploadService: UploadService,
    private pollingService: StatusPollingService,
    private authService: AuthService,
    private router: Router,
    private snackBar: MatSnackBar
  ) {
    this.authService.userEmail$.subscribe(email => {
      this.userEmail = email;
    });
  }

  ngOnInit(): void {
    this.uploadService.getUploadState()
      .pipe(takeUntil(this.destroy$))
      .subscribe(state => {
        this.uploadState = state;
        if (state.progress) {
          this.uploadProgress = state.progress.percentage;
        }
      });

    this.pollingService.getLatestStatus()
      .pipe(takeUntil(this.destroy$))
      .subscribe(status => {
        if (status) {
          this.processingStatus = status;
          this.processingProgress = status.progress_percentage || 0;
        }
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.pollingService.stopAllPolls();
  }

  onFileSelected(event: Event): void {
    const target = event.target as HTMLInputElement;
    const files = target.files;
    if (files && files.length > 0) {
      this.selectFile(files[0]);
    }
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.dragover = true;
  }

  onDragLeave(): void {
    this.dragover = false;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.dragover = false;

    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      this.selectFile(files[0]);
    }
  }

  selectFile(file: File): void {
    // Validate file type
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain'
    ];

    if (!allowedTypes.includes(file.type)) {
      this.snackBar.open('Please upload a PDF, Word document, or text file', 'Close', { duration: 5000 });
      return;
    }

    // Validate file size (max 500MB)
    if (file.size > 500 * 1024 * 1024) {
      this.snackBar.open('File size must be less than 500MB', 'Close', { duration: 5000 });
      return;
    }

    this.selectedFile = file;
  }

  clearFile(): void {
    this.selectedFile = null;
    if (this.fileInput) {
      this.fileInput.nativeElement.value = '';
    }
  }

  browseFiles(): void {
    this.fileInput.nativeElement.click();
  }

  onSubmit(): void {
    if (!this.selectedFile) {
      this.snackBar.open('Please select a file', 'Close', { duration: 5000 });
      return;
    }

    this.isUploading = true;
    this.uploadProgress = 0;
    this.processingProgress = 0;

    // Start upload with progress tracking
    this.uploadService.uploadTenderWithProgress(this.selectedFile, this.companyDescription)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (event: HttpEvent<any>) => {
          // Track upload progress
          if (event.type === HttpEventType.UploadProgress && event.total) {
            this.uploadService.updateProgress(event.loaded, event.total);
          }
          // Handle response
          else if (event instanceof HttpResponse) {
            this.isUploading = false;
            this.uploadProgress = 100;
            const response = event.body;
            this.uploadService.setCompleted(response.tender_id);
            
            this.snackBar.open('Upload complete! Analyzing document...', 'Close', { duration: 3000 });
            
            // Start polling for processing status
            this.startProcessingPolling(response.tender_id);
          }
        },
        error: (error) => {
          this.isUploading = false;
          this.uploadProgress = 0;
          this.uploadService.setError(error.message || 'Upload failed');
          const errorMessage = error?.error?.detail || 'Upload failed. Please try again.';
          this.snackBar.open(errorMessage, 'Close', { duration: 5000, panelClass: ['error-snackbar'] });
        }
      });
  }

  private startProcessingPolling(tenderId: string): void {
    this.pollingService.startPolling(tenderId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (status) => {
          if (status.status === 'completed') {
            this.snackBar.open('Analysis complete!', 'Close', { duration: 3000 });
            // Redirect to evaluation view
            setTimeout(() => {
              this.router.navigate(['/evaluations', tenderId]);
            }, 1000);
          } else if (status.status === 'error') {
            this.snackBar.open(
              `Processing failed: ${status.error_message}`,
              'Close',
              { duration: 5000, panelClass: ['error-snackbar'] }
            );
          }
        },
        error: (error) => {
          console.error('Polling error:', error);
          this.snackBar.open('Error tracking processing status', 'Close', { duration: 5000 });
        }
      });
  }

  goToDashboard(): void {
    this.router.navigate(['/dashboard']);
  }

  get fileSize(): string {
    if (!this.selectedFile) return '';
    const bytes = this.selectedFile.size;
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  }
}
