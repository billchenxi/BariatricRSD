# Contributing to BariatricRSD

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Issues

If you find a bug or have a feature request, please open an issue on GitHub with a clear description and, if applicable, steps to reproduce the problem.

### Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Run linting: `ruff check bariatric_rsd/`
5. Run tests: `pytest tests/`
6. Commit with a descriptive message
7. Push to your fork and submit a Pull Request

### Code Style

- Follow PEP 8 conventions
- Use type hints for function signatures
- Add docstrings to all public classes and functions
- Maximum line length: 100 characters

### Adding New Features

If you want to add a new feature (e.g., a new temporal model, a new task head, or support for a new dataset), please open an issue first to discuss the approach.

### Testing

- Add tests for any new functionality in the `tests/` directory
- Ensure all existing tests pass before submitting a PR

## Development Setup

```bash
git clone https://github.com/billchenxi/BariatricRSD.git
cd BariatricRSD
pip install -e ".[dev]"
pre-commit install
```

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
