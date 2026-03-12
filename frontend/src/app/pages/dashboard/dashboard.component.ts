import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService, TenderEvaluation } from '@services/api.service';
import { StatusPollingService, TenderStatus } from '@services/status-polling.service';
import { AuthService } from '@services/auth.service';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit, OnDestroy {
  recentEvaluations: TenderEvaluation[] = [];
  isLoading = true;
  userEmail: string = '';
  private destroy$ = new Subject<void>();

  // Statistics
  totalTenders = 0;
  recommendedBids = 0;
  highRiskItems = 0;

  // Real-time processing
  processingTenders: Map<string, TenderStatus> = new Map();

  constructor(
    private apiService: ApiService,
    private authService: AuthService,
    private pollingService: StatusPollingService,
    private router: Router,
    private snackBar: MatSnackBar
  ) { }

  ngOnInit(): void {
    this.loadUserEmail();
    this.loadDashboardData();
    this.watchProcessingTenders();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadUserEmail(): void {
    this.authService.userEmail$
      .pipe(takeUntil(this.destroy$))
      .subscribe(email => {
        this.userEmail = email;
      });
  }

  private loadDashboardData(): void {
    this.isLoading = true;
    this.apiService.listEvaluations(undefined, 10, 0)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          this.recentEvaluations = response.evaluations || [];
          this.totalTenders = response.total || 0;
          this.calculateStatistics();
          this.isLoading = false;
        },
        error: (error) => {
          this.isLoading = false;
          this.snackBar.open('Failed to load dashboard data', 'Close', { duration: 5000 });
          console.error('Dashboard error:', error);
        }
      });
  }

  private calculateStatistics(): void {
    this.recommendedBids = this.recentEvaluations.filter(
      e => e.bid_recommendation === 'RECOMMENDED'
    ).length;

    this.highRiskItems = this.recentEvaluations.filter(
      e => e.scores.risk.score < 40
    ).length;
  }

  private watchProcessingTenders(): void {
    // Subscribe to polling results
    this.pollingService.getPollingResults()
      .pipe(takeUntil(this.destroy$))
      .subscribe(status => {
        this.processingTenders.set(status.tender_id, status);
        
        // Auto-refresh evaluations if any completed
        if (status.status === 'completed') {
          setTimeout(() => {
            this.loadDashboardData();
            this.processingTenders.delete(status.tender_id);
          }, 1000);
        }
      });
  }

  viewEvaluation(tenderId: string): void {
    this.router.navigate(['/evaluations', tenderId]);
  }

  navigateToUpload(): void {
    this.router.navigate(['/tender']);
  }

  getRecommendationColor(recommendation: string): string {
    switch (recommendation) {
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

  getScoreBadgeColor(score: number): string {
    if (score >= 75) return 'success';
    if (score >= 50) return 'warning';
    return 'error';
  }

  getProcessingStatus(tenderId: string): TenderStatus | undefined {
    return this.processingTenders.get(tenderId);
  }

  isProcessing(tenderId: string): boolean {
    const status = this.processingTenders.get(tenderId);
    return status?.status === 'processing';
  }
}
