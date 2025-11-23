# Comprehensive Testing Plan for Volunteer Management App

## 1. Backend Testing Plan

### Areas to Cover
- **User Authentication**
  - Registration with valid/invalid input
  - Login success/failure (wrong password, inactive users)
  - Logout flows
- **Role-based Access and Authorization**
  - Validate admin-only pages return 403 for non-admins
  - Volunteers restricted from admin workflows
- **Dashboard Endpoints**
  - Verify data display matches roles and assignments
- **Activity Management**
  - Activity creation (valid data, invalid inputs, duplicates)
  - Activity listing and filtering
  - Volunteer inscription in activities; duplicate inscription prevention
- **Attendance Management**
  - Recording attendance with validation (no duplicate records, positive hours)
  - Handling invalid input and error paths
- **Notification Sending**
  - Form validation
  - Email sending error simulation (BadHeaderError, SMTP failures)
- **Certificate Generation**
  - Valid volunteer PDF generation
  - Invalid volunteer or permissions error handling
  - PDF content validity

### Test Types
- Unit Tests (Model and util functions)
- Integration Tests (Database and View interaction)
- Functional Tests (User flows and form submissions)
- Edge Case and Error Path Tests

---

## 2. Frontend/UI Testing Plan

### Manual Test Areas
- **Authentication Pages:** Register, Login, Logout buttons, error messages
- **Dashboards:** Data accuracy and UI elements for admins and volunteers
- **Forms:** Validation messages are shown correctly, required fields
- **Navigation:** All links/buttons function properly
- **Conditional Content:** Role-based content visibility
- **Responsive Design:** UI display on various screen sizes
- **Certificate View:** PDF displayed in browser or downloaded correctly

### Recommended Tools
- Browser DevTools for responsive testing
- Manual step-through guided by test cases
- Optional: Automate via Selenium or Cypress in future

---

## 3. WeasyPrint Installation & Troubleshooting (Windows)

### Required Dependencies
- Install GTK3 and libraries:
  - Use MSYS2: `pacman -S mingw-w64-x86_64-gtk3`
- Add GTK bin folder to system PATH:
  ```
  C:\msys64\mingw64\bin
  ```
- Verify installation:
  - Run `weasyprint --version` in terminal

### Common Issues
- Missing DLL or shared libraries for libgobject, pangocairo, gdk-pixbuf
- Incompatibilities on Windows; ensure correct architecture version (64-bit vs 32-bit)

---

## 4. Alternative PDF Generation Approaches

- Use ReportLab to generate certificates programmatically (better controlled, no external dependencies)
- Use Headless Browser (Puppeteer/Playwright) to print HTML pages to PDF
- Convert using wkhtmltopdf CLI tool and subprocess calls in Django

---

## 5. Performance Testing Recommendations

- Use Locust or JMeter to simulate user load on:
  - Login, Registration
  - Dashboard data fetch
  - Attendance recording
  - Notification sending
- Monitor response times and database query counts
- Optimize slow queries or caching where appropriate

---

Please confirm which testing plan areas or steps you want help executing first, or if you want detailed code examples for automated backend tests or other tools.
