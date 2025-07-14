# Feature: Assessments

## Objective
Allow users to assess a specific vendor offering using a questionnaire, capture evidence, and optionally export results.

## Models
- Assessment
- Answer
- Questionnaire
- Question
- FileEvidence (if attached)

## View Flow
1. Offering Detail → "Start Assessment"
2. User answers questions (conditional UI)
3. Upload optional documents
4. Submit
5. Results available under Offering → Assessments tab

## Logic
- Question types: Yes/No, Text, Evidence upload
- Conditional field visibility
- Score calculation removed as per ADR 001

## Edge Cases
- No questionnaire attached
- Already assessed
- Incomplete submissions
