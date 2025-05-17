# Generate coverage reports with module-specific details
pytest --cov-report=term-missing:skip-covered `
      --cov-report=html `
      --cov-report=xml `
      --cov-branch `
      --cov=bot.admin `
      --cov=bot.utils `
      --cov=bot

# Generate module-specific reports
$modules = @("admin", "utils", "core")
foreach ($module in $modules) {
    Write-Host "`nCoverage report for $module module:"
    Write-Host "================================="
    
    if ($module -eq "core") {
        $path = "bot"
    } else {
        $path = "bot/$module"
    }
    
    coverage report --include="$path/*" --show-missing
}

# Print overall statistics
Write-Host "`nOverall Coverage Summary:"
Write-Host "======================="
coverage report

# Create coverage badge if coverage-badge is installed
if (Get-Command coverage-badge -ErrorAction SilentlyContinue) {
    coverage-badge -o coverage_html/badge.svg
    Write-Host "`nCoverage badge generated at coverage_html/badge.svg"
}

Write-Host "`nDetailed HTML report available at coverage_html/index.html" 