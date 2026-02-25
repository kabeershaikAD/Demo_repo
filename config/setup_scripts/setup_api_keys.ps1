# Setup API Keys for Legal RAG System
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "API Key Setup for Legal RAG System" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get API keys from user
Write-Host "Enter your API keys (press Enter to skip):" -ForegroundColor Yellow
Write-Host ""

$openai_key = Read-Host "OpenAI API Key (REQUIRED for embeddings/search)"
$groq_key = Read-Host "Groq API Key (REQUIRED for answer generation)"

# Set environment variables for current session
if ($openai_key) {
    $env:OPENAI_API_KEY = $openai_key
    Write-Host "[SUCCESS] OpenAI API Key set for current session" -ForegroundColor Green
} else {
    Write-Host "[WARNING] OpenAI API Key not set - embeddings will fail!" -ForegroundColor Red
}

if ($groq_key) {
    $env:GROQ_API_KEY = $groq_key
    Write-Host "[SUCCESS] Groq API Key set for current session" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Groq API Key not set - answer generation will fail!" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "IMPORTANT NOTES:" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. These keys are set for THIS PowerShell session only" -ForegroundColor Yellow
Write-Host "2. They will be lost when you close PowerShell" -ForegroundColor Yellow
Write-Host "3. To make permanent, add them to Windows Environment Variables" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Activate virtual environment: .\legal_rag_env\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "2. Run diagnostic: python diagnose_retriever_issue.py" -ForegroundColor White
Write-Host "3. Start Streamlit: streamlit run legal_ui.py" -ForegroundColor White
Write-Host ""



