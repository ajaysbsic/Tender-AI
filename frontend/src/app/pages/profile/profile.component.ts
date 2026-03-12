import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ApiService } from '@services/api.service';
import { AuthService } from '@services/auth.service';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-profile',
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.scss']
})
export class ProfileComponent implements OnInit, OnDestroy {
  profileForm: FormGroup;
  isLoading = false;
  isSaving = false;
  userEmail = '';
  private destroy$ = new Subject<void>();

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    private authService: AuthService,
    private snackBar: MatSnackBar
  ) {
    this.profileForm = this.fb.group({
      companyName: ['', [Validators.required, Validators.minLength(2)]],
      industry: ['', Validators.required],
      companySize: ['', Validators.required],
      expertise: ['', [Validators.required, Validators.minLength(20)]],
      contactPerson: ['', Validators.required],
      phone: ['', [Validators.required, Validators.pattern(/^\+?[0-9]{10,}$/)]],
      website: ['', Validators.pattern(/^(https?:\/\/)?.+\..+$/)]
    });
  }

  ngOnInit(): void {
    this.loadUserEmail();
    this.loadProfile();
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

  private loadProfile(): void {
    this.isLoading = true;
    this.apiService.getCompanyProfile()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (profile) => {
          this.profileForm.patchValue(profile);
          this.isLoading = false;
        },
        error: (error) => {
          this.isLoading = false;
          this.snackBar.open('Failed to load profile', 'Close', { duration: 5000 });
          console.error('Profile error:', error);
        }
      });
  }

  onSubmit(): void {
    if (this.profileForm.invalid) {
      this.snackBar.open('Please fill in all required fields correctly', 'Close', { duration: 5000 });
      return;
    }

    this.isSaving = true;
    this.apiService.updateCompanyProfile(this.profileForm.value)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.isSaving = false;
          this.snackBar.open('Profile updated successfully!', 'Close', { duration: 3000 });
        },
        error: (error) => {
          this.isSaving = false;
          const errorMessage = error?.error?.detail || 'Failed to update profile';
          this.snackBar.open(errorMessage, 'Close', { duration: 5000 });
        }
      });
  }

  reset(): void {
    this.profileForm.reset();
    this.loadProfile();
  }

  logout(): void {
    this.authService.logout();
  }

  get companyNameError(): string {
    const control = this.profileForm.get('companyName');
    if (control?.hasError('required')) return 'Company name is required';
    if (control?.hasError('minlength')) return 'Company name must be at least 2 characters';
    return '';
  }

  get phoneError(): string {
    const control = this.profileForm.get('phone');
    if (control?.hasError('required')) return 'Phone number is required';
    if (control?.hasError('pattern')) return 'Please enter a valid phone number';
    return '';
  }

  get websiteError(): string {
    const control = this.profileForm.get('website');
    if (control?.hasError('pattern')) return 'Please enter a valid website URL';
    return '';
  }
}
