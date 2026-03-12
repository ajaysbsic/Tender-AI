# TenderIQ Localization (i18n/i10n) Implementation

## Overview
TenderIQ now supports multiple languages with full internationalization (i18n) and localization (i10n) support, including RTL (Right-to-Left) layout for Arabic.

## Supported Languages

| Language | Code | Direction | Status |
|----------|------|-----------|--------|
| English | `en` | LTR | ✅ Implemented |
| Arabic | `ar` | RTL | ✅ Implemented |

## Architecture

### Translation System
- **Framework**: ngx-translate (v15)
- **Loader**: TranslateHttpLoader
- **Storage**: HTTP loader with JSON files
- **Default Language**: English (`en`)
- **Persistence**: Browser LocalStorage

### File Structure
```
frontend/src/
├── assets/
│   └── i18n/
│       ├── en.json      (English translations)
│       └── ar.json      (Arabic translations)
├── app/
│   ├── services/
│   │   └── translation.service.ts (Translation management)
│   ├── app.component.ts (Language switching)
│   └── app.module.ts (ngx-translate configuration)
```

## Translation Keys Structure

All translation keys follow a hierarchical structure:

```json
{
  "auth": {
    "title": "...",
    "email": "...",
    "errors": {
      "emailRequired": "..."
    }
  },
  "dashboard": { ... },
  "tender": { ... },
  "evaluations": { ... },
  "profile": { ... },
  "common": { ... }
}
```

### Key Categories

| Module | Keys | Purpose |
|--------|------|---------|
| `auth` | Login, signup, validation errors | Authentication pages |
| `dashboard` | Welcome, stats, navigation | Dashboard view |
| `tender` | Upload, progress, analysis | Tender upload page |
| `evaluations` | Results, scoring, report | Evaluation results |
| `profile` | Account, company info | Profile management |
| `common` | Generic labels, buttons | Reusable strings |

## Implementation Guide

### 1. Using Translations in Templates

#### Pipe Approach (Recommended)
```html
<!-- Simple translation -->
<h1>{{ 'auth.title' | translate }}</h1>

<!-- With parameters -->
<p>{{ 'dashboard.welcome' | translate: { name: userName } }}</p>

<!-- Inline fallback -->
<button>{{ 'common.submit' | translate: { defaultValue: 'Submit' } }}</button>
```

#### Component Class
```typescript
import { TranslationService } from '@services/translation.service';

export class MyComponent {
  constructor(private translationService: TranslationService) {}

  ngOnInit() {
    // Get observable translation
    this.translationService.getTranslation('auth.title').subscribe(title => {
      console.log(title);
    });

    // Instant translation (synchronous)
    const title = this.translationService.instantTranslate('auth.title');
  }
}
```

### 2. Adding New Translations

1. **Add to English file** (`en.json`):
   ```json
   {
     "myModule": {
       "myKey": "My Translation"
     }
   }
   ```

2. **Add to Arabic file** (`ar.json`):
   ```json
   {
     "myModule": {
       "myKey": "ترجمتي"
     }
   }
   ```

3. **Use in templates**:
   ```html
   {{ 'myModule.myKey' | translate }}
   ```

### 3. Language Switching

```typescript
import { TranslationService } from '@services/translation.service';

export class AppComponent {
  constructor(private translationService: TranslationService) {}

  changeLanguage(langCode: string) {
    this.translationService.setLanguage(langCode);
    // Language, direction, and localStorage updated automatically
  }
}
```

### 4. RTL Support

#### Automatic Direction Handling
- Document direction (`dir` attribute) updated automatically
- Document language (`lang` attribute) updated automatically
- CSS media queries handle layout flipping

#### CSS RTL Patterns
```scss
/* LTR default */
.button {
  margin-right: 16px;
}

/* RTL override using attribute selector */
[dir='rtl'] .button {
  margin-right: auto;
  margin-left: 16px;
}

/* Alternative: Logical properties (modern browsers) */
.button {
  margin-inline-end: 16px;  /* auto-flips in RTL */
}
```

#### Font Support
- **LTR**: Roboto font
- **RTL**: Cairo font (Google Fonts, optimized for Arabic)
- Auto-switched via CSS media queries

## Component Updates for Localization

### Example: Dashboard Component
```typescript
import { TranslateModule } from '@ngx-translate/core';
import { TranslationService } from '@services/translation.service';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  imports: [CommonModule, TranslateModule]
})
export class DashboardComponent {
  currentDirection$ = this.translationService.currentDirection$;

  constructor(private translationService: TranslationService) {}

  // Components automatically re-render when language changes
}
```

## Testing Translations

### Manual Testing
1. Open browser DevTools console
2. Run: `localStorage.setItem('language', 'ar')`
3. Refresh page
4. Verify:
   - Page displays Arabic text
   - Document direction is RTL
   - Cairo font loads
   - Layout flips correctly

### Automated Testing
```typescript
describe('Translations', () => {
  it('should switch to Arabic', () => {
    translationService.setLanguage('ar');
    expect(translationService.getCurrentLanguage()).toBe('ar');
    expect(translationService.getCurrentDirection()).toBe('rtl');
  });
});
```

## Best Practices

### ✅ Do's
- Store all user-facing text in translation files
- Use hierarchical key naming
- Keep translations concise and clear
- Test RTL layout with actual language
- Use semantic HTML for screen readers
- Include translation keys in commit messages

### ❌ Don'ts
- Don't hardcode strings in components
- Don't use single-level key names
- Don't forget to add both EN and AR translations
- Don't assume text length in layouts
- Don't use images for text
- Don't forget RTL margin/padding adjustments

## Missing Translations Handling

If a translation key is missing:
- English fallback used automatically
- Warning logged to console (development)
- Key displayed in UI as `[MISSING_KEY]` (development)
- Empty string shown in production

## Performance Considerations

1. **Lazy Loading**: Translations loaded once at startup
2. **Caching**: Browser caches translation files
3. **No Network Calls**: After initial load, cached locally
4. **Instant Switching**: Language changes don't reload page

## Accessibility

### Screen Reader Support
- Proper `lang` attribute on HTML element
- Semantic HTML maintained in all translations
- ARIA labels translated appropriately
- Direction respected in keyboard navigation

### Keyboard Navigation
- Tab order correct for both LTR and RTL
- Focus indicators visible in all directions
- Escape key closes menus correctly

## Adding New Languages

### Steps:
1. Create new translation file: `src/assets/i18n/{language-code}.json`
2. Copy English structure and translate
3. Update `TranslationService.supportedLanguages`:
   ```typescript
   private supportedLanguages = [
     { code: 'en', label: 'English', dir: 'ltr' },
     { code: 'ar', label: 'العربية', dir: 'rtl' },
     { code: 'fr', label: 'Français', dir: 'ltr' }  // New
   ];
   ```
4. Add language option to UI switcher
5. Test thoroughly

## Troubleshooting

### Issue: Translations not loading
- Check browser network tab for 404 on `/assets/i18n/*.json`
- Verify TranslateModule imported in component
- Check console for errors

### Issue: RTL layout broken
- Verify `[dir='rtl']` CSS rules applied
- Check for hardcoded `margin-right` or `margin-left`
- Use logical properties or attribute selectors

### Issue: Font not switching
- Check Google Fonts loaded correctly
- Verify CSS media queries for `[dir='rtl']`
- Clear browser cache

## Resources

- [ngx-translate Documentation](https://github.com/ngx-translate/core)
- [Angular i18n Guide](https://angular.io/guide/i18n)
- [RTL Best Practices](https://www.w3.org/International/questions/qa-what-is-bidi-text)
- [Web Accessibility WCAG](https://www.w3.org/WAI/WCAG21/quickref/)

## Localization Checklist

- [ ] English translations complete
- [ ] Arabic translations complete
- [ ] RTL CSS styles applied
- [ ] Fonts load correctly for both languages
- [ ] Language switcher works
- [ ] LocalStorage persistence verified
- [ ] Components re-render on language change
- [ ] RTL layout tested in browser
- [ ] Text length variations handled
- [ ] Accessibility verified with screen reader
- [ ] Performance acceptable
- [ ] Mobile layout works in both directions

## Future Enhancements

1. **Additional Languages**
   - Spanish (es)
   - French (fr)
   - German (de)

2. **Translation Management**
   - Integration with translation management platform (Phrase, Crowdin)
   - Automated translation updates
   - Community translations

3. **Advanced Features**
   - Locale-specific formatting (dates, numbers, currency)
   - Pluralization rules
   - Date/time localization
   - Number formatting per locale

4. **Performance**
   - Dynamic chunk loading for languages
   - Lazy-load languages on demand
   - Pre-translate common keys
