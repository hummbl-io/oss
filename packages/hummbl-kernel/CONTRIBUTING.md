# Contributing to HUMMBL/kernel

Thank you for your interest in contributing to HUMMBL/kernel! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contribution Guidelines](#contribution-guidelines)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to [security@hummbl.io](mailto:security@hummbl.io).

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Basic understanding of Python and agent orchestration concepts

### Development Setup

1. Fork the repository
2. Clone your fork locally
3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install dependencies (stdlib-only, but for development):
   ```bash
   pip install pytest pytest-cov
   ```
5. Run tests to verify setup:
   ```bash
   python -m pytest tests/
   ```

## Contribution Guidelines

### What to Contribute

We welcome contributions in the following areas:

- **Bug fixes**: Fix reported issues
- **New adapters**: Add support for new agent frameworks or tools
- **Documentation**: Improve documentation and examples
- **Tests**: Add test coverage for existing functionality
- **Performance**: Optimize existing code
- **Security**: Report and fix security vulnerabilities

### What NOT to Contribute

- Breaking changes without discussion
- Third-party dependencies (stdlib-only policy)
- Features outside the project scope
- Code that doesn't follow stdlib-only policy

## Pull Request Process

1. **Branch Naming**: Use `type/description` format (e.g., `feat/add-langchain-adapter`, `fix/security-leak`)
2. **Make Changes**: Implement your changes following coding standards
3. **Test**: Ensure all tests pass and add new tests for new functionality
4. **Document**: Update relevant documentation
5. **Commit**: Use conventional commit format
6. **Push**: Push to your fork
7. **PR**: Create pull request with clear description

### PR Description Template

```markdown
## Description
Brief description of changes

## Type
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] All tests pass

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new dependencies added
```

## Coding Standards

### Python Style

- Follow PEP 8 style guidelines
- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Use type hints where appropriate
- Write docstrings for all public functions and classes

### Stdlib-Only Policy

HUMMBL/kernel maintains a stdlib-only policy for runtime dependencies:
- No third-party imports in production code
- Use only Python standard library
- Third-party tools allowed only for development (pytest, etc.)
- Any exception requires ADR approval

### Security Standards

- Never commit secrets, tokens, or credentials
- Validate all inputs and grants
- Follow security best practices
- Report security vulnerabilities privately

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=kernel --cov-report=html

# Run specific test file
python -m pytest tests/test_kernel.py
```

### Writing Tests

- Write tests for all new functionality
- Aim for >80% code coverage
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies where appropriate

## Documentation

### Code Documentation

- Add docstrings to all public functions and classes
- Use Google docstring format
- Include examples in docstrings
- Document security considerations

### Project Documentation

- Update README.md for user-facing changes
- Update relevant .md files for architectural changes
- Add examples to EXAMPLES.md for new features
- Update CHANGELOG.md for version changes

## Questions?

- Open an issue for questions
- Contact maintainers at [kernel@hummbl.io](mailto:kernel@hummbl.io)
- Check existing issues and discussions

## License

By contributing to HUMMBL/kernel, you agree that your contributions will be licensed under the project's license.

---

Thank you for contributing to HUMMBL/kernel!