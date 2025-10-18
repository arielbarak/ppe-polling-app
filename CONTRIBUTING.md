# Contributing

Thanks for your interest! Here's how to contribute.

## Quick Start

```bash
# Fork and clone
git clone https://github.com/arielbarak/ppe-polling-app.git
cd ppe-polling-app

# Create branch
git checkout -b feature/my-feature

# Make changes, test, commit
git commit -m "Add my feature"

# Push and create PR
git push origin feature/my-feature
```

## What to Contribute

### Good First Issues
- Fix typos in docs
- Add tests
- Improve error messages
- Add code comments

### Feature Ideas
- New PPE types (audio CAPTCHA, image recognition)
- Database integration
- Vote privacy (zero-knowledge proofs)
- Mobile app
- Better UI/UX

### Bug Reports
Open an issue with:
- What happened
- What you expected
- Steps to reproduce
- Error messages/logs

## Code Standards

**Python:**
```python
def my_function(param: str) -> bool:
    """
    Brief description.
    
    Args:
        param: What it is
        
    Returns:
        What it returns
    """
    return True
```

**JavaScript:**
```javascript
/**
 * Brief description.
 * 
 * @param {string} param - What it is
 * @returns {boolean} What it returns
 */
function myFunction(param) {
  return true;
}
```

## Testing

Add tests for new features:

```python
# backend/tests/test_my_feature.py
def test_my_feature():
    assert my_function() == expected
```

Run tests:
```bash
pytest
```

## Pull Request Process

1. **Update docs** if needed
2. **Add tests** for new code
3. **Run linter**: `black backend/app`
4. **Pass all tests**: `pytest`
5. **Write clear commit messages**
6. **One feature per PR**

## Commit Messages

Good:
```
Add audio CAPTCHA PPE type

- Implements BasePPE interface
- Adds audio generation
- Includes client handler
```

Bad:
```
updated stuff
```

## Questions?

Open an issue or ask in discussions.

Thanks for contributing! 🙏