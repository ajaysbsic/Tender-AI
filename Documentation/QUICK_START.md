# TenderIQ Frontend - Quick Start Guide

Get the TenderIQ Angular frontend running in minutes!

## ⚡ 5-Minute Setup

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Configure Backend URL
Edit `src/environments/environment.ts`:
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api'
};
```

### 3. Start Development Server
```bash
npm start
```

Open browser: http://localhost:4200

### 4. Login
- **Email**: any email address
- **Password**: any password (6+ chars)
- Or register a new account

## 📂 Key Files to Know

| File | Purpose |
|------|---------|
| `src/app/app.module.ts` | Main application module |
| `src/app/app-routing.module.ts` | Route configuration |
| `src/app/services/auth.service.ts` | Authentication logic |
| `src/app/services/api.service.ts` | Backend API calls |
| `src/environments/environment.ts` | Configuration |
| `angular.json` | Build configuration |
| `package.json` | Dependencies |

## 🔑 Core Services

### AuthService
Located at `src/app/services/auth.service.ts`
```typescript
this.authService.login(email, password).subscribe(...)
this.authService.register(email, password, company).subscribe(...)
this.authService.logout()
```

### ApiService
Located at `src/app/services/api.service.ts`
```typescript
this.apiService.uploadTender(file, description).subscribe(...)
this.apiService.getEvaluation(tenderId).subscribe(...)
this.apiService.downloadPdfReport(tenderId, company).subscribe(...)
```

## 🛣️ Pages/Routes

| Route | Component | Purpose |
|-------|-----------|---------|
| `/login` | LoginComponent | User authentication |
| `/dashboard` | DashboardComponent | Main overview |
| `/tender` | TenderComponent | Upload documents |
| `/evaluations/:id` | EvaluationsComponent | View results |
| `/profile` | ProfileComponent | Company settings |

## 🔒 Route Protection

- **Login page**: Protected by `NoAuthGuard` (can't access if logged in)
- **Other pages**: Protected by `AuthGuard` (require login)
- **Token storage**: localStorage key `tender_iq_token`

## 🎯 Development Workflow

### Create a New Service
```typescript
// src/app/services/new.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '@environments/environment';

@Injectable({ providedIn: 'root' })
export class NewService {
  constructor(private http: HttpClient) { }
  
  getData() {
    return this.http.get(`${environment.apiUrl}/endpoint`);
  }
}
```

### Create a New Component
```bash
ng generate component pages/new-page
```

### Add a New Route
In `app-routing.module.ts`:
```typescript
{
  path: 'new',
  loadChildren: () => import('./pages/new-page/new-page.module')
    .then(m => m.NewPageModule),
  canActivate: [AuthGuard]
}
```

## 🐛 Common Issues & Solutions

### Issue: "Cannot find module" error
**Solution**: Check path aliases in `tsconfig.json`
```json
{
  "compilerOptions": {
    "paths": {
      "@app/*": ["src/app/*"],
      "@services/*": ["src/app/services/*"]
    }
  }
}
```

### Issue: CORS errors from backend
**Solution**: Ensure backend has CORS headers:
```python
# Backend (FastAPI)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: Token not persisting
**Solution**: Check browser localStorage
```javascript
// In browser console
localStorage.getItem('tender_iq_token')
```

## 📦 Build & Deployment

### Development Build
```bash
npm start
```

### Production Build
```bash
npm run build:prod
```
Output: `dist/tender-iq/`

### Docker Build
```bash
docker build -t tender-iq-frontend .
docker run -p 4200:80 tender-iq-frontend
```

## 🧪 Testing

### Run Unit Tests
```bash
npm test
```

### Run E2E Tests
```bash
npm run e2e
```

### Lint Code
```bash
npm run lint
```

## 📊 Environment Setup

### Development
```
API URL: http://localhost:8000/api
Debug: enabled
Production: false
```

### Production
```
API URL: https://api.tenderiq.com/api
Debug: disabled
Production: true
```

## 🎨 Material Theme

Default theme: **Indigo + Purple**

To customize, edit `app.module.ts`:
```typescript
import '@angular/material/prebuilt-themes/indigo-pink.css';
```

Available themes:
- indigo-pink
- deeppurple-amber
- pink-bluegrey
- purple-green

## 📱 Responsive Breakpoints

| Device | Width |
|--------|-------|
| Mobile | < 768px |
| Tablet | 768px - 1024px |
| Desktop | > 1024px |

## 🔌 API Integration

### Request Example
```typescript
// In any component
constructor(private api: ApiService) { }

ngOnInit() {
  this.api.getEvaluation(tenderId).subscribe({
    next: (evaluation) => {
      console.log(evaluation);
    },
    error: (err) => {
      console.error(err);
    }
  });
}
```

### Expected API Response
```json
{
  "tender_id": "123",
  "overall_score": 85,
  "bid_recommendation": "RECOMMENDED",
  "scores": {
    "eligibility": { "score": 90, "category": "HIGH" },
    "risk": { "score": 75, "category": "MEDIUM" },
    "effort": { "score": 85, "category": "MODERATE" }
  }
}
```

## 💡 Tips & Tricks

### Hot Module Replacement
Changes auto-reload during development:
```bash
npm start
# Make changes, file auto-saves and refreshes
```

### Chrome DevTools
- Angular DevTools extension for debugging
- Network tab to inspect API calls
- Console for error messages
- Storage tab for localStorage verification

### Performance
- Use `OnPush` change detection
- Unsubscribe from Observables with `takeUntil`
- Lazy-load feature modules
- Tree-shake unused code

## 📚 Additional Resources

- [Angular Docs](https://angular.io)
- [Material Design](https://material.angular.io)
- [TypeScript Guide](https://www.typescriptlang.org)
- [RxJS Reference](https://rxjs.dev)

---

**Need Help?** Check the main [README.md](./README.md) or contact support.
