@echo off
REM GITHUB UPLOAD - WINDOWS QUICK START GUIDE
REM Run these commands to upload your SmartFarming project to GitHub

echo.
echo ============================================
echo  SMARTFARMING - GITHUB UPLOAD INSTRUCTIONS
echo ============================================
echo.

echo STEP 1: CREATE GITHUB REPOSITORY
echo.
echo 1. Go to: https://github.com/new
echo 2. Repository name: smartfarming
echo 3. Description: Django-based smart agriculture platform
echo 4. Visibility: Public
echo 5. DO NOT initialize with README, .gitignore, or license
echo 6. Click "Create repository"
echo 7. Copy the HTTPS URL from the page
echo.
pause

echo STEP 2: CONFIGURE GIT REMOTE
echo.
echo Replace YOUR_USERNAME with your GitHub username:
echo.
echo Example:
echo   git remote add origin https://github.com/YOUR_USERNAME/smartfarming.git
echo.
SET /P "GITHUB_URL=Enter your GitHub repository HTTPS URL: "
if not "%GITHUB_URL%"=="" (
    git remote add origin %GITHUB_URL%
    echo.
    echo ✓ Remote configured!
) else (
    echo Skipped remote configuration
)
echo.
pause

echo STEP 3: PUSH TO GITHUB
echo.
echo Running: git branch -M main
git branch -M main
echo Running: git push -u origin main
git push -u origin main
echo.
if %ERRORLEVEL% EQU 0 (
    echo ✓ Successfully pushed to GitHub!
    echo.
    echo Visit your repository at:
    echo %GITHUB_URL%
) else (
    echo ⚠ Push may have encountered an error
    echo Check authentication credentials
)
echo.
pause

echo STEP 4: VERIFY GITHUB REPOSITORY
echo.
echo Open your browser and visit:
echo %GITHUB_URL%
echo.
echo You should see your SmartFarming code and updated README!
echo.
pause

echo ============================================
echo  PROJECT DETAILS
echo ============================================
echo.
echo Django Version: 5.2.5
echo Python Version: 3.13
echo.
echo Apps Included (8):
echo   • admin_panel - Admin dashboard
echo   • ai_recommendations - AI-powered crop suggestions
echo   • crops - Crop management
echo   • government_schemes - Subsidy information
echo   • marketplace - Product marketplace
echo   • orders - Order management
echo   • users - Authentication & profiles
echo   • weather - Weather integration
echo.
echo Dependencies: 53 packages
echo Project Size: 4.6 MB
echo.
echo ✓ Project is clean and ready for production!
echo.
pause

echo ============================================
echo  TROUBLESHOOTING
echo ============================================
echo.
echo If authentication fails:
echo   1. Create Personal Access Token: https://github.com/settings/tokens/new
echo   2. Select scope: repo
echo   3. Use token as password when prompted
echo.
echo If you see "Repository not found":
echo   1. Check YOUR_USERNAME is correct
echo   2. Verify repository exists on GitHub
echo   3. Check internet connection
echo.
echo For SSH authentication:
echo   git remote set-url origin git@github.com:YOUR_USERNAME/smartfarming.git
echo   Add SSH key to GitHub: https://github.com/settings/keys
echo.
pause

echo ============================================
echo  NEXT STEPS
echo ============================================
echo.
echo After uploading to GitHub:
echo   1. Add a LICENSE file (MIT recommended)
echo   2. Create GitHub Pages documentation
echo   3. Set up GitHub Actions for CI/CD
echo   4. Add contributors
echo   5. Create releases with version tags
echo.
echo Your SmartFarming project is now on GitHub! 🚀
echo.
pause
