# Contributing to DataVideoCodec

Thank you for your interest in contributing to DataVideoCodec! We welcome contributions from the community. This document provides guidelines and instructions for contributing.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- **Title**: Clear, descriptive summary of the bug
- **Description**: Detailed explanation of the issue
- **Steps to Reproduce**: Exact steps to reproduce the problem
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: Python version, OS, FFmpeg version, etc.

### Suggesting Enhancements

Enhancement suggestions are also welcome! Please create an issue with:
- **Title**: Clear summary of the enhancement
- **Description**: Detailed explanation of the proposed feature
- **Motivation**: Why this enhancement would be useful
- **Example Usage**: How users would interact with this feature

### Submitting Pull Requests

1. **Fork the repository** and create your feature branch from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** with clear, focused commits
   ```bash
   git commit -m "Add descriptive commit message"
   ```

3. **Follow the coding style** — maintain consistency with existing code
   - Use meaningful variable names
   - Add docstrings to functions and classes
   - Keep lines reasonably short and readable

4. **Test your changes** before submitting
   ```bash
   python -m pytest tests/ -v
   ```

5. **Update documentation** if your changes affect user-facing features
   - Update README.md if needed
   - Add docstrings to new functions
   - Update architecture diagrams if applicable

6. **Push to your fork** and create a Pull Request
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Provide a clear PR description**:
   - What problem does this solve?
   - What changes were made?
   - Are there any breaking changes?
   - Any testing instructions?

## Code Style Guidelines

- **Python**: Follow PEP 8 conventions
- **Naming**: Use descriptive names for variables, functions, and classes
- **Comments**: Use comments to explain *why*, not *what*
- **Type Hints**: Use type hints in function signatures where possible
- **Docstrings**: Use docstrings for modules, classes, and public functions

## Development Setup

1. Clone your fork:
   ```bash
   git clone https://github.com/your-username/DataVideoCodec.git
   cd DataVideoCodec
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   # .venv\Scripts\activate   # Windows
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run tests to verify setup:
   ```bash
   python -m pytest tests/ -v
   ```

## Testing

- Write unit tests for new functions
- Test both success and error cases
- Run the full test suite before submitting a PR:
  ```bash
  python -m pytest tests/ -v
  ```
- Add integration tests for end-to-end workflows

## Areas for Contribution

We're particularly interested in:
- Bug fixes and stability improvements
- Performance optimizations
- Additional test coverage
- Documentation improvements
- GUI enhancements
- Cross-platform compatibility fixes
- New error correction algorithms

## Review Process

1. A maintainer will review your PR
2. Feedback and suggestions may be provided
3. Make requested changes and push updates
4. Once approved, your PR will be merged

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

## Questions?

If you have any questions, feel free to create an issue or reach out to the maintainers.

Thank you for contributing! 🎉
