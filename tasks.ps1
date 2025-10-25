param(
    [Parameter(Position = 0)]
    [ValidateSet("install", "run-backend", "lint", "format", "test", "download-model")]
    [string]$Task = "run-backend"
)

switch ($Task) {
    "install" {
        pip install -r requirements.txt
    }
    "download-model" {
        python -m spacy download en_core_web_lg
        if ($LASTEXITCODE -ne 0) {
            python -m spacy download en_core_web_sm
        }
    }
    "run-backend" {
        Set-Location backend
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    }
    "lint" {
        ruff check backend
        isort backend --check-only
        black backend --check
    }
    "format" {
        isort backend
        black backend
    }
    "test" {
        pytest
    }
}
