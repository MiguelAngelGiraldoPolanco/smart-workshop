# CLAUDE.md

## Project Overview

Smart Workshop is a personal automotive workshop management platform built with Python and Django.

The project is under continuous development, with the long-term goal of integrating AI agents and deploying cloud infrastructure using Docker, Kubernetes and AWS.

## Development Guidelines

### General Principles

- Follow clean code principles and maintain readable, maintainable code.
- Prefer simple solutions over unnecessary complexity.
- Respect the existing project architecture.
- Avoid introducing unnecessary dependencies.
- Explain significant architectural decisions before implementing them.
- Do not modify unrelated functionality.

### Python & Django

- Follow Python best practices and PEP 8 conventions.
- Use Django's built-in functionality whenever appropriate.
- Keep business logic separate from views and models when necessary.
- Use Django ORM for database operations.
- Implement appropriate validation and error handling.
- Follow Django security recommendations.

### Database

- Preserve data integrity.
- Use Django migrations for database schema changes.
- Avoid destructive database operations without explicit approval.
- Never hardcode database credentials.

### Testing

- Write tests for new functionality.
- Run relevant tests after modifying existing code.
- Consider edge cases and error handling.
- Do not assume functionality works without verification.

### Security

- Never commit secrets, passwords, API keys or environment variables.
- Use environment variables for sensitive configuration.
- Validate user input.
- Apply appropriate authentication and authorization.

### AI Development

- AI agents must interact with application functionality through explicitly defined tools.
- Do not allow agents to bypass application business rules or permissions.
- Validate AI-generated outputs before executing sensitive operations.
- Require human confirmation for critical operations.

### Documentation

- Update documentation when functionality or architecture changes.
- Document significant architectural decisions.
- Keep the README consistent with the actual implementation.
- Distinguish implemented features from planned functionality.

## Development Workflow

Before implementing changes:

1. Inspect the existing codebase.
2. Understand the current architecture.
3. Identify the files and components affected.
4. Explain the proposed approach when the change is significant.

After implementing changes:

1. Review the modified code.
2. Run relevant tests.
3. Report what was changed.
4. Identify remaining limitations or potential improvements.

## Important

This is a learning-oriented engineering project.

Prioritize helping the developer understand the implementation, technical decisions and trade-offs rather than simply generating code.