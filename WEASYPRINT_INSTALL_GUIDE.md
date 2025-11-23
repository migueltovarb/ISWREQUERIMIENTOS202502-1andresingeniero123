# WeasyPrint Installation and Troubleshooting Guide (Windows)

## Overview
WeasyPrint requires several external binary dependencies to be installed on Windows to work correctly, especially GTK and related libraries.

## Steps to Install WeasyPrint Dependencies

1. Install MSYS2 (Minimal SYStem 2):
   - Download and install from https://www.msys2.org/
   - Follow the installation instructions on the MSYS2 website.

2. Update MSYS2 and install GTK3:
   - Open "MSYS2 MSYS" terminal.
   - Update package databases and base packages:
     ```
     pacman -Syu
     ```
   - Restart MSYS2 terminal.
   - Update rest of the packages:
     ```
     pacman -Su
     ```
   - Install GTK3 runtime libraries:
     ```
     pacman -S mingw-w64-x86_64-gtk3
     ```

3. Add the GTK3 binaries to your Windows PATH:
   - The GTK3 binaries are located in something like:
     ```
     C:\msys64\mingw64\bin
     ```
   - Add this path to the system Environment Variables under PATH.

4. Verify GTK3 is accessible:
   - Open a new command prompt.
   - Run:
     ```
     weasyprint --version
     ```
   - This should report the version without errors.

## Common Issues

- Error "libgobject-2.0-0.dll" not found:
  - Usually means GTK3 binaries are missing or PATH not set correctly.
- Ensure you install the 64-bit version if your Python is 64-bit.
- Restart your terminal or IDE after changing PATH.

## Alternative PDF Options

If WeasyPrint installation remains problematic, consider:

- ReportLab:
  - Pure Python PDF library.
  - Requires manual PDF layout.
- Headless browsers like Puppeteer or Playwright to print HTML to PDF.
- wkhtmltopdf with subprocess calls.

## References

- Official WeasyPrint install instructions: https://weasyprint.readthedocs.io/en/stable/install.html#windows
- MSYS2 installation: https://www.msys2.org/
- Troubleshooting: https://weasyprint.readthedocs.io/en/stable/first_steps.html#troubleshooting

---
Please let me know if you want step-by-step help with MSYS2 installation or alternative PDF generation approach.
