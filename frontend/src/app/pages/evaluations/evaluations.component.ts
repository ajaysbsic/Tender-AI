import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService, TenderEvaluation, EligibilityDetails } from '@services/api.service';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-evaluations',
  templateUrl: './evaluations.component.html',
  styleUrls: ['./evaluations.component.scss']
})
export class EvaluationsComponent implements OnInit, OnDestroy {
  tenderId: string = '';
  evaluation: TenderEvaluation | null = null;
  eligibilityDetails: EligibilityDetails | null = null;
  isLoading = true;
  selectedTab = 0;
  isDownloadingPdf = false;
  private destroy$ = new Subject<void>();

  constructor(
    private apiService: ApiService,
    private route: ActivatedRoute,
    private router: Router,
    private snackBar: MatSnackBar
  ) { }

  ngOnInit(): void {
    this.route.params.pipe(takeUntil(this.destroy$)).subscribe(params => {
      this.tenderId = params['id'];
      if (this.tenderId) {
        this.loadEvaluation();
      }
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadEvaluation(): void {
    this.isLoading = true;
    this.apiService.getEvaluation(this.tenderId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (evaluation) => {
          this.evaluation = evaluation;
          this.loadEligibilityDetails();
        },
        error: (error) => {
          this.isLoading = false;
          this.snackBar.open('Failed to load evaluation', 'Close', { duration: 5000 });
          console.error('Evaluation error:', error);
        }
      });
  }

  private loadEligibilityDetails(): void {
    this.apiService.getEligibilityDetails(this.tenderId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (details) => {
          this.eligibilityDetails = details;
          this.isLoading = false;
        },
        error: (error) => {
          this.isLoading = false;
          console.error('Eligibility details error:', error);
        }
      });
  }

  downloadPdf(): void {
    if (!this.evaluation) return;

    this.isDownloadingPdf = true;
    // You would need to pass the company name from profile
    const companyName = 'Your Company';

    this.apiService.downloadPdfReport(this.tenderId, companyName)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (blob) => {
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `tender_evaluation_${this.tenderId}.pdf`;
          link.click();
          window.URL.revokeObjectURL(url);
          this.isDownloadingPdf = false;
          this.snackBar.open('Report downloaded successfully', 'Close', { duration: 3000 });
        },
        error: (error) => {
          this.isDownloadingPdf = false;
          this.snackBar.open('Failed to download report', 'Close', { duration: 5000 });
          console.error('Download error:', error);
        }
      });
  }

  getRecommendationIcon(): string {
    switch (this.evaluation?.bid_recommendation) {
      case 'RECOMMENDED':
        return 'thumb_up';
      case 'CONSIDER_WITH_CAUTION':
        return 'help';
      case 'NOT_RECOMMENDED':
        return 'thumb_down';
      default:
        return 'info';
    }
  }

  getRecommendationColor(): string {
    switch (this.evaluation?.bid_recommendation) {
      case 'RECOMMENDED':
        return 'accent';
      case 'CONSIDER_WITH_CAUTION':
        return 'warn';
      case 'NOT_RECOMMENDED':
        return 'error';
      default:
        return 'primary';
    }
  }

  formatRecommendation(recommendation: string): string {
    return recommendation.replace(/_/g, ' ');
  }

  getScoreBgClass(score: number): string {
    if (score >= 75) return 'score-success';
    if (score >= 50) return 'score-warning';
    return 'score-error';
  }

  backToDashboard(): void {
    this.router.navigate(['/dashboard']);
  }
}
