# Developer Guide 👨‍💻

How to contribute to the PPE polling system.

## Setup

**Clone and install:**
```bash
git clone https://github.com/arielbarak/ppe-polling-app.git
cd ppe-polling-app

# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

**Run development servers:**
```bash
# Backend (terminal 1)
cd backend
uvicorn app.main:app --reload

# Frontend (terminal 2)
cd frontend
npm start
```

## Code Style

**Python:**
- Follow PEP 8
- Use type hints
- Docstrings for all functions

**JavaScript:**
- Use ES6+
- Prettier for formatting
- ESLint for linting

**Format code:**
```bash
# Python
black backend/app

# JavaScript
cd frontend
npm run format
```

## Testing

**Run all tests:**
```bash
cd backend
pytest
```

**Run specific test:**
```bash
pytest tests/test_poll_service.py -v
```

**Run simulations:**
```bash
python -m pytest tests/simulation/ -v
```

**Coverage:**
```bash
pytest --cov=app --cov-report=html
```

## Adding a New Feature

### 1. Backend Feature

**Create model:**
```python
# backend/app/models/my_model.py
from pydantic import BaseModel

class MyModel(BaseModel):
    field1: str
    field2: int
```

**Create service:**
```python
# backend/app/services/my_service.py
class MyService:
    def my_method(self):
        return "result"

my_service = MyService()
```

**Create routes:**
```python
# backend/app/routes/my_routes.py
from fastapi import APIRouter

router = APIRouter(prefix="/my-endpoint", tags=["My Feature"])

@router.get("/")
async def my_endpoint():
    return {"message": "Hello"}
```

**Register router:**
```python
# backend/app/main.py
from .routes import my_routes

app.include_router(my_routes.router)
```

**Write tests:**
```python
# backend/tests/test_my_feature.py
def test_my_feature():
    assert True
```

### 2. Frontend Feature

**Create component:**
```jsx
// frontend/src/components/MyComponent.jsx
import React from 'react';

function MyComponent() {
  return <div>Hello</div>;
}

export default MyComponent;
```

**Create API service:**
```javascript
// frontend/src/services/myApi.js
export async function myApiCall() {
  const response = await fetch('http://localhost:8000/my-endpoint');
  return response.json();
}
```

**Use in component:**
```jsx
import { myApiCall } from '../services/myApi';

function MyComponent() {
  const [data, setData] = useState(null);
  
  useEffect(() => {
    myApiCall().then(setData);
  }, []);
  
  return <div>{data?.message}</div>;
}
```

## Adding a New PPE Type

See `backend/app/ppe/README.md` for complete guide.

**Quick example:**

```python
# backend/app/ppe/my_ppe.py
from .base import BasePPE, PPEType, PPEDifficulty

class MyPPE(BasePPE):
    def get_type(self):
        return PPEType.MY_TYPE
    
    def generate_challenge_with_secret(self, secret, session_id):
        challenge = f"Challenge {secret}"
        solution = f"Solution {secret}"
        return challenge, solution
    
    def verify_solution(self, challenge, solution):
        return True  # Your logic here
```

Register it:
```python
# backend/app/ppe/factory.py
from .my_ppe import MyPPE

self.register(MyPPE, PPEMetadata(...))
```

## Debugging

**Backend logs:**
```bash
# Add to code
import logging
logging.info("Debug message")

# Run with debug
uvicorn app.main:app --reload --log-level debug
```

**Frontend debugging:**
```javascript
// Use React DevTools
console.log('Debug:', data);

// Or add breakpoints in browser DevTools
debugger;
```

**WebSocket debugging:**
```javascript
ws.addEventListener('message', (event) => {
  console.log('WS received:', event.data);
});
```

## Common Tasks

**Add a database migration:**
```bash
# Using Alembic (if implemented)
alembic revision -m "Add new field"
alembic upgrade head
```

**Update dependencies:**
```bash
# Backend
cd backend
pip install new-package
pip freeze > requirements.txt

# Frontend
cd frontend
npm install new-package
```

**Generate API client:**
```bash
# OpenAPI spec available at /docs
curl http://localhost:8000/openapi.json > openapi.json
```

## Project Structure Rules

- **Models** define data structures (Pydantic)
- **Services** contain business logic
- **Routes** handle HTTP/WebSocket
- **Utils** are pure functions
- **PPE** implementations are modular

## Git Workflow

**Create feature branch:**
```bash
git checkout -b feature/my-feature
```

**Commit with good messages:**
```bash
git commit -m "Add my feature

- Implements X
- Fixes Y
- Updates Z"
```

**Push and create PR:**
```bash
git push origin feature/my-feature
# Then create PR on GitHub
```

## CI/CD

Tests run automatically on every PR:
- Linting checks
- Unit tests
- Integration tests
- Simulation tests

## Release Process

1. Update version in `package.json` and `pyproject.toml`
2. Update `CHANGELOG.md`
3. Tag release: `git tag v1.0.0`
4. Push tags: `git push --tags`
5. Build Docker images
6. Deploy to production

## Resources

- [FastAPI docs](https://fastapi.tiangolo.com/)
- [React docs](https://react.dev/)
- [Ant Design](https://ant.design/)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

## Getting Help

- Open an issue on GitHub
- Check existing issues first
- Include error messages and logs
- Minimal reproducible example helps

## Code Review Guidelines

- Keep PRs focused and small
- Write descriptive commit messages
- Add tests for new features
- Update docs if needed
- Respond to feedback promptly

Happy coding! 🚀