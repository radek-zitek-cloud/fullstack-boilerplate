# Task Completion Checklist

When you finish a task, ensure the following:

## Code Quality Checks

- [ ] Code follows project conventions (see style_and_conventions.md)
- [ ] Type hints are complete (Python) or types are correct (TypeScript)
- [ ] No unnecessary comments/docstrings (only where needed for clarity)
- [ ] Code is formatted properly

## Run Quality Commands

```bash
# Backend
make format         # Format Python code with ruff
make lint           # Check Python with ruff and mypy

# Frontend (if changed)
cd frontend && npm run lint  # Check TypeScript/ESLint
```

## Testing (if applicable)

```bash
make test-backend   # Run backend tests
make test-frontend  # Run frontend tests
```

## Verification

- [ ] Application starts without errors
- [ ] Key functionality works
- [ ] Logs show expected behavior (check `logs/app.log`)
- [ ] No new errors in `logs/error.log`

## Git Commit

```bash
git add .
git commit -m "type: description

Details of what was done.

Ultraworked with Sisyphus"
```

### Commit Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `test`: Tests
- `chore`: Maintenance

## For New Features

- [ ] Update README if needed
- [ ] Add example usage if applicable
- [ ] Document in AGENTS.md if relevant to developers

## For Bug Fixes

- [ ] Describe the bug in commit message
- [ ] Explain the fix briefly
- [ ] Verify fix resolves the issue

## Before Finalizing

- [ ] Review your changes once more
- [ ] Ensure no debug code left (print statements, etc.)
- [ ] Check that no secrets/credentials are committed
