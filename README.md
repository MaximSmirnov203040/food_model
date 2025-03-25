# Food Recommendation System

[![Tests](https://github.com/MaximSmirnov203040/food_model/actions/workflows/test.yml/badge.svg)](https://github.com/MaximSmirnov203040/food_model/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/MaximSmirnov203040/food_model/branch/main/graph/badge.svg)](https://codecov.io/gh/MaximSmirnov203040/food_model)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive food recommendation system that provides personalized recipe suggestions based on user preferences, dietary restrictions, and nutritional goals.

## Features

- **Personalized Recommendations**: Tailored recipe suggestions based on user preferences and dietary restrictions
- **Dietary Restrictions**: Support for various dietary preferences (vegetarian, vegan, keto, etc.)
- **Allergy Tracking**: Comprehensive allergen detection and filtering
- **Nutritional Analysis**: Detailed nutritional information and food flag warnings
- **Cuisine Preferences**: User-specific cuisine preferences and recommendations
- **Comprehensive test coverage**: Thorough testing of all major components
- **CI/CD Pipeline**: Automated testing and code quality checks

## Project Structure

```
food_model/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       └── router.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── data/
│   │   └── ingredient_loader.py
│   ├── models/
│   │   └── models.py
│   ├── schemas/
│   │   └── schemas.py
│   └── services/
│       └── recommendation.py
├── tests/
│   ├── api/
│   ├── data/
│   ├── integration/
│   └── training/
├── scripts/
│   └── training/
├── alembic/
├── alembic.ini
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── .github/
│   └── workflows/
│       └── test.yml
└── .codecov.yml
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/food_model.git
cd food_model
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database:
```bash
alembic upgrade head
```

## Testing

The project includes comprehensive test coverage for all major components:

### Unit Tests
Located in the `tests/` directory, covering:
- Ingredient loading functionality
- Data preprocessing
- Model training
- API endpoints
- Utility functions

### Running Tests

1. Install test dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Run all tests:
```bash
pytest
```

3. Run specific test categories:
```bash
# Run unit tests only
pytest tests/unit

# Run integration tests only
pytest tests/integration

# Run with coverage report
pytest --cov=app --cov-report=term-missing
```

### Test Categories

1. **Ingredient Loading Tests** (`tests/data/test_ingredient_loader.py`)
   - API integration tests
   - Data parsing tests
   - Error handling tests
   - Rate limiting tests
   - Duplicate detection tests

2. **Model Training Tests** (`tests/training/`)
   - Data preparation tests
   - Model architecture tests
   - Training process tests
   - Validation tests

3. **API Tests** (`tests/api/`)
   - Endpoint tests
   - Authentication tests
   - Request validation tests
   - Response format tests

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration and Codecov for code coverage tracking.

### Automated Testing

Tests are automatically run on:
- Every push to the main branch
- Every pull request

The CI pipeline includes:
- Python environment setup
- PostgreSQL service container
- Dependency installation
- Test execution with coverage
- Code coverage reporting

### Code Coverage

- Minimum coverage requirement: 80%
- Coverage reports are generated for:
  - Project overall coverage
  - Patch coverage (changes in PR)
- Coverage is tracked and reported via Codecov

### CI/CD Configuration

1. **GitHub Actions** (`.github/workflows/test.yml`):
   - Runs on Ubuntu latest
   - Sets up Python 3.9
   - Configures PostgreSQL service
   - Installs dependencies
   - Runs tests with coverage
   - Uploads coverage reports

2. **Codecov** (`.codecov.yml`):
   - Configures coverage thresholds
   - Sets up coverage reporting rules
   - Defines ignored files and directories

### Setting up CI/CD

1. Create a GitHub repository
2. Connect to Codecov:
   - Sign up at codecov.io
   - Add your repository
   - Get your Codecov token
3. Add Codecov token to GitHub repository secrets:
   - Go to repository settings
   - Add secret: `CODECOV_TOKEN`

## API Usage

### User Preferences

Update user preferences:
```bash
curl -X PUT "http://localhost:8000/api/v1/users/me/preferences" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "dietary_restrictions": ["vegetarian"],
       "favorite_cuisines": ["italian", "japanese"],
       "allergies": ["nuts"],
       "food_flags": ["high_sodium"]
     }'
```

### Recipe Recommendations

Get personalized recommendations:
```bash
curl "http://localhost:8000/api/v1/recommendations" \
     -H "Authorization: Bearer YOUR_TOKEN"
```

### Recipe Details

Get recipe with food flag information:
```bash
curl "http://localhost:8000/api/v1/recipes/1" \
     -H "Authorization: Bearer YOUR_TOKEN"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 