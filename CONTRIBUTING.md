# Contributing to CCXT CTA Strategy

Thank you for your interest in contributing to the CCXT CTA Strategy project! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Poetry or uv for dependency management

### Development Setup

1. **Fork the repository**
   ```bash
   git clone https://github.com/your-username/ccxt_cta.git
   cd ccxt_cta
   ```

2. **Set up development environment**
   ```bash
   # Using uv (recommended)
   uv sync --dev

   # Or using poetry
   poetry install --with dev
   ```

3. **Create a virtual environment**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

4. **Install pre-commit hooks**
   ```bash
   uv run pre-commit install
   ```

## 📏 Code Style

This project follows strict code style guidelines:

- **PEP 8** compliance
- **Black** code formatting
- **isort** import sorting
- **mypy** type checking
- **flake8** linting

### Running Code Quality Checks

```bash
# Format code
uv run black src/ tests/

# Sort imports
uv run isort src/ tests/

# Type checking
uv run mypy src/

# Linting
uv run flake8 src/ tests/

# Run all checks
uv run pre-commit run --all-files
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_strategy.py

# Run with verbose output
uv run pytest -v
```

### Writing Tests

- Use `pytest` for all tests
- Write unit tests for new features
- Include integration tests for complex functionality
- Use descriptive test names
- Add docstrings to test functions

### Test Structure

```
tests/
├── test_strategy.py          # Core strategy tests
├── test_utils.py            # Utility function tests
├── test_demos.py            # Demo tests
└── integration/             # Integration tests
    ├── test_exchange.py
    └── test_data_flow.py
```

## 📝 Documentation

### Code Documentation

- Use docstrings for all public functions and classes
- Follow Google-style docstrings
- Include type hints for all functions
- Add inline comments for complex logic

### README Updates

- Update README.md for major features
- Update CHANGELOG.md for version changes
- Keep documentation up-to-date with code changes

## 🌟 Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, documented code
   - Add tests for new functionality
   - Update documentation

3. **Run quality checks**
   ```bash
   uv run pre-commit run --all-files
   uv run pytest
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a Pull Request on GitHub.

### Commit Message Format

Use conventional commit format:
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Test changes
- `chore:` - Maintenance changes

## 🏷️ Labeling Pull Requests

Use these labels for PRs:
- `bug` - Bug fixes
- `enhancement` - New features
- `documentation` - Documentation changes
- `tests` - Test changes
- `dependencies` - Dependency updates
- `breaking-change` - Breaking changes

## 🐛 Reporting Bugs

When reporting bugs:

1. **Use the issue template**
2. **Provide detailed information**
   - Python version
   - Operating system
   - Error messages
   - Steps to reproduce
3. **Include minimal reproduction example**

## 💡 Feature Requests

When requesting features:

1. **Check existing issues** first
2. **Provide clear description** of the feature
3. **Explain the use case** and benefits
4. **Consider implementation** suggestions

## 🔍 Code Review Process

### Reviewer Guidelines

- Check code quality and style
- Verify tests are comprehensive
- Ensure documentation is updated
- Test functionality if possible
- Provide constructive feedback

### Contributor Guidelines

- Address all review comments
- Update tests and documentation
- Respond to feedback promptly
- Be open to suggestions

## 📦 Release Process

Releases follow [Semantic Versioning](https://semver.org/):

- `MAJOR.MINOR.PATCH`
- `MAJOR`: Breaking changes
- `MINOR`: New features (backward compatible)
- `PATCH`: Bug fixes

### Release Checklist

- [ ] All tests pass
- [ ] Documentation is updated
- [ ] CHANGELOG is updated
- [ ] Version is bumped
- [ ] Tag is created
- [ ] Release notes are written

## 🤝 Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Provide helpful feedback
- Focus on constructive discussions

### Getting Help

- Check documentation first
- Search existing issues
- Ask questions in discussions
- Be patient with responses

## 🏆 Recognition

Contributors are recognized in:

- README.md contributors section
- Release notes
- Special mentions in communications

## 📋 Project Structure

```
ccxt_cta/
├── src/                     # Source code
│   ├── strategy/           # Core strategy modules
│   ├── demos/              # Demonstration modules
│   ├── utils/              # Utility modules
│   └── __init__.py
├── tests/                  # Test files
├── config/                 # Configuration files
├── docs/                   # Documentation
├── scripts/                # Utility scripts
├── pyproject.toml          # Project configuration
├── README.md              # Project README
├── CONTRIBUTING.md         # Contributing guide
├── CHANGELOG.md           # Change log
└── LICENSE               # License file
```

## 📞 Contact

- Create an issue for bugs or features
- Start a discussion for questions
- Email: powerair@example.com

## 🙏 Thank You

Thank you for contributing to the CCXT CTA Strategy project! Your contributions help make this project better for everyone.

---

Remember: The goal is to create a high-quality, well-tested, and well-documented trading strategy that benefits the entire community.