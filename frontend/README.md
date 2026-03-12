# TenderIQ Frontend - Angular Application

Modern, enterprise-grade Angular frontend for TenderIQ, the AI-powered tender and RFP analysis platform.

## 🎯 Overview

The TenderIQ frontend provides a professional user interface for:
- **User Authentication** - Secure login and registration
- **Dashboard** - Overview of recent evaluations and statistics
- **Tender Upload** - Drag-and-drop document upload interface
- **Evaluation Viewer** - Detailed tender analysis with multiple views
- **Company Profile** - Manage company information and settings

## 🏗️ Architecture

### Technology Stack
- **Angular 17** - Latest LTS version
- **TypeScript 5.2** - Strict mode enabled
- **Angular Material 17** - Enterprise-grade UI components
- **RxJS 7.8** - Reactive programming
- **SCSS** - Component styling

### Project Structure
```
frontend/
├── src/
│   ├── app/
│   │   ├── pages/              # Feature modules
│   │   │   ├── login/
│   │   │   ├── dashboard/
│   │   │   ├── tender/
│   │   │   ├── evaluations/
│   │   │   └── profile/
│   │   ├── services/           # API and business logic
│   │   │   ├── auth.service.ts
│   │   │   └── api.service.ts
│   │   ├── guards/             # Route guards
│   │   │   └── auth.guard.ts
│   │   ├── interceptors/       # HTTP interceptors
│   │   │   └── auth.interceptor.ts
│   │   ├── app.component.*     # Root component
│   │   └── app-routing.module.ts
│   ├── environments/           # Environment config
│   ├── styles.scss            # Global styles
│   ├── main.ts               # Application entry
│   └── index.html
├── angular.json              # Angular config
├── tsconfig.json            # TypeScript config
├── package.json             # Dependencies
└── README.md               # This file
```

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ (LTS)
- npm 9+ or yarn 3+

### Installation

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure API endpoint**
   
   Update `src/environments/environment.ts`:
   ```typescript
   export const environment = {
     production: false,
     apiUrl: 'http://localhost:8000/api'  // Your backend URL
   };
   ```

3. **Start development server**
   ```bash
   npm start
   ```
   
   Application opens at `http://localhost:4200`

### Build for Production
```bash
npm run build:prod
# Output: dist/tender-iq/
```

## 🔐 Authentication

### Flow
1. User navigates to login page
2. Enters credentials or registers
3. AuthService calls backend `/auth/login` or `/auth/register`
4. JWT token stored in localStorage
5. AuthInterceptor automatically adds token to all API requests

### Services

#### AuthService
```typescript
// Core methods
login(email: string, password: string): Observable<LoginResponse>
register(email: string, password: string, companyName: string): Observable<LoginResponse>
logout(): void
getToken(): string | null

// Observable streams
isLoggedIn$: Observable<boolean>
userEmail$: Observable<string>
```

#### ApiService
```typescript
// Tender operations
uploadTender(file: File, companyDescription?: string): Observable<UploadResponse>
getTenderStatus(tenderId: string): Observable<any>

// Evaluations
getEvaluation(tenderId: string): Observable<TenderEvaluation>
getEligibilityDetails(tenderId: string): Observable<EligibilityDetails>
getRiskAssessment(tenderId: string): Observable<any>
getEffortAssessment(tenderId: string): Observable<any>
downloadPdfReport(tenderId: string, companyName: string): Observable<Blob>

// Profile
getCompanyProfile(): Observable<any>
updateCompanyProfile(profile: any): Observable<any>
```

## 📄 Pages Overview

### Login Page
- Email/password authentication
- Registration form
- Validation and error handling
- Professional Material Design UI

### Dashboard
- Statistics cards (total tenders, recommended bids, high-risk items)
- Recent evaluations list
- Quick navigation to upload or view details
- Responsive grid layout

### Tender Upload
- Drag-and-drop file upload
- Support for PDF, DOCX, DOC, TXT
- Optional company description
- Upload progress indication
- Automatic redirection to evaluation

### Evaluations
- Overall bid recommendation
- Three dimension scores:
  - Eligibility assessment
  - Risk analysis
  - Effort estimation
- Tabbed interface for details
- Eligibility requirements breakdown
- PDF report download
- Streaming PDF download

### Company Profile
- Edit company information
- Industry and company size selection
- Contact details and expertise
- Form validation
- Menu options for reload and logout

## 🎨 Material Design

### Theme Colors
- **Primary**: `#667eea` (Indigo)
- **Accent**: `#764ba2` (Purple)
- **Warn**: `#f57c00` (Orange)

### Components Used
- MatToolbar, MatSidenav - Navigation
- MatCard - Content containers
- MatForm, MatInput - Forms
- MatButton - Actions
- MatIcon - Icons
- MatList - Lists
- MatTabs - Tabbed content
- MatMenu - Dropdown menus
- MatProgressBar - Loading states
- MatSnackBar - Toast notifications

## 🛡️ Route Guards

### AuthGuard
Protects routes requiring authentication. Redirects to login if not authenticated.

### NoAuthGuard
Prevents logged-in users from accessing login/register pages.

## ⚙️ HTTP Interceptors

### AuthInterceptor
- Adds JWT token to all requests
- Handles 401 errors
- Manages token refresh (can be extended)

### Error Handling
- Global error display via MatSnackBar
- Detailed error messages from backend
- Graceful degradation for missing data

## 🔧 Configuration

### Environment Variables
```typescript
// development
{
  production: false,
  apiUrl: 'http://localhost:8000/api'
}

// production
{
  production: true,
  apiUrl: 'https://api.tenderiq.com/api'
}
```

### TypeScript Paths
```
@app/*        → src/app/
@services/*   → src/app/services/
@models/*     → src/app/models/
@components/* → src/app/components/
@interceptors/* → src/app/interceptors/
@guards/*     → src/app/guards/
@environments/* → src/environments/
```

## 📦 Dependencies

### Production
- @angular/animations: 17.x
- @angular/common: 17.x
- @angular/compiler: 17.x
- @angular/core: 17.x
- @angular/forms: 17.x
- @angular/platform-browser: 17.x
- @angular/platform-browser-dynamic: 17.x
- @angular/router: 17.x
- @angular/material: 17.x
- rxjs: 7.8.x
- tslib: ^2.x
- zone.js: ~0.14.x

### Development
- @angular-devkit/build-angular: 17.x
- @angular/cli: 17.x
- @angular/compiler-cli: 17.x
- typescript: 5.2.x

## 🧪 Testing

### Unit Tests
```bash
npm test
```

### E2E Tests
```bash
npm run e2e
```

### Linting
```bash
npm run lint
```

## 📝 Code Standards

### TypeScript
- Strict mode enabled
- Type hints for all functions
- Interface-based design
- Observable-first reactive code

### Angular
- Standalone components (modern approach)
- Lazy-loaded feature modules
- Smart/presentation component separation
- OnPush change detection where applicable

### SCSS
- BEM-style class naming
- Mobile-first responsive design
- Utility classes for common patterns
- SCSS variables for theming

## 🚢 Deployment

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY . .
RUN npm ci
RUN npm run build:prod
```

### Deployment Steps
1. Build for production: `npm run build:prod`
2. Deploy `dist/tender-iq/` to static hosting
3. Configure API endpoint in environment
4. Ensure CORS enabled on backend
5. Set up SSL/TLS for production

## 🔗 Integration with Backend

### API Expectations
All endpoints should return JSON in this format:
```json
{
  "data": {},
  "status": "success|error",
  "detail": "Optional error message"
}
```

### Authentication Flow
1. Backend returns JWT token on login/register
2. Frontend stores in localStorage with key `tender_iq_token`
3. Interceptor adds `Authorization: Bearer <token>` header
4. Backend validates token and returns 401 if expired

## 📚 Resources

- [Angular Documentation](https://angular.io/docs)
- [Angular Material](https://material.angular.io)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [RxJS Documentation](https://rxjs.dev/)

## 🤝 Contributing

### Code Review Checklist
- [ ] TypeScript strict mode compliant
- [ ] All functions have type hints
- [ ] RxJS Observables properly unsubscribed
- [ ] Responsive design tested
- [ ] Material Design conventions followed
- [ ] Error handling implemented
- [ ] Unit tests written
- [ ] Documentation updated

## 📄 License

MIT License - See LICENSE file for details

## 👥 Support

For support, contact: support@tenderiq.com

---

**Last Updated**: 2024
**Angular Version**: 17.x
**Maintenance Status**: Active
