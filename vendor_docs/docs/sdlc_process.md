# SDLC Process for VendorGuard

## 1. Feature Planning
- Create markdown file in `docs/features/`
- Describe goals, stakeholders, dependencies
- Include model fields, view flow, UI behavior

## 2. Development
- Use Git branches per feature (e.g. `feat/assessments`)
- Unit test every service logic
- Templates and views scaffolded with comments

## 3. Code Review
- Every PR checked for:
  - Working logic
  - Security
  - Comments + test coverage
  - Style (black, flake8)

## 4. Testing
- Pytest for unit tests
- Manual functional QA via test checklist
- (CI/CD to be added post-MVP)

## 5. Deployment
- Dev env: local Docker or runserver
- Staging/prod: via Railway or Fly.io (planned)
