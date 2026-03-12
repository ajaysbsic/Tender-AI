import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { AuthService } from '@services/auth.service';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent {
  loginForm: FormGroup;
  registerMode = false;
  isLoading = false;
  returnUrl = '/dashboard';

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute,
    private snackBar: MatSnackBar
  ) {
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      companyName: ['']
    });

    this.returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/dashboard';
  }

  toggleMode(): void {
    this.registerMode = !this.registerMode;
    const companyControl = this.loginForm.get('companyName');
    if (this.registerMode) {
      companyControl?.setValidators([Validators.required]);
      companyControl?.enable();
    } else {
      companyControl?.clearValidators();
      companyControl?.disable();
    }
    companyControl?.updateValueAndValidity();
    this.loginForm.reset();
  }

  onSubmit(): void {
    if (this.loginForm.invalid) {
      return;
    }

    this.isLoading = true;
    const { email, password, companyName } = this.loginForm.value;

    const operation = this.registerMode
      ? this.authService.register(email, password, companyName)
      : this.authService.login(email, password);

    operation.subscribe({
      next: () => {
        const message = this.registerMode ? 'Registration successful!' : 'Login successful!';
        this.snackBar.open(message, 'Close', { duration: 3000 });
        this.router.navigateByUrl(this.returnUrl);
      },
      error: (error) => {
        this.isLoading = false;
        const errorMessage = error?.error?.detail || 'Authentication failed. Please try again.';
        this.snackBar.open(errorMessage, 'Close', { duration: 5000, panelClass: ['error-snackbar'] });
      }
    });
  }

  get emailError(): string {
    const control = this.loginForm.get('email');
    if (control?.hasError('required')) return 'Email is required';
    if (control?.hasError('email')) return 'Please enter a valid email';
    return '';
  }

  get passwordError(): string {
    const control = this.loginForm.get('password');
    if (control?.hasError('required')) return 'Password is required';
    if (control?.hasError('minlength')) return 'Password must be at least 6 characters';
    return '';
  }

  get companyError(): string {
    const control = this.loginForm.get('companyName');
    if (control?.hasError('required')) return 'Company name is required';
    return '';
  }
}
