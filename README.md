# Pi Calculator API

A high-performance REST API for calculating π (Pi) to arbitrary precision using the Chudnovsky algorithm with Celery for asynchronous task processing.

## Features

- **Asynchronous Processing**: Uses Celery with Redis/RabbitMQ for background Pi calculations
- **Progress Tracking**: Real-time progress updates during long calculations
- **RESTful API**: Clean REST API with Swagger documentation
- **Performance Prediction**: Built-in time estimation using power-law approximation
- **High Precision**: Supports calculation of π to thousands of decimal places
- **Visualization**: Generates performance plots and approximation curves

## Architecture

The system consists of:

- **Flask REST API**: Handles HTTP requests and provides API endpoints
- **Celery Workers**: Perform heavy Pi calculations in the background
- **Redis/RabbitMQ**: Message broker for task queuing
- **Redis**: Result backend for storing calculation results

## API Endpoints

### 1. Calculate Pi
```
GET /calculate_pi?n=123
```

**Response (202):**
```json
{
  "message": "Pi calculation started",
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "decimals": 1000
}
```

### 2. Check Progress
```
POST /check_progress
```

**Request Body:**
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Response:**
```json
{
  "state": "PROGRESS",
  "progress": 0.75,
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "iteration": 750,
  "total_iterations": 1000,
  "elapsed_time": 15.2,
  "result": null
}
```

### 3. Health Check
```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "Pi Calculator API"
}
```

## Installation

### Prerequisites
- Python 3.8+
- Redis server
- RabbitMQ (optional, defaults to pyamqp)

### Setup

1. **Clone the repository:**
```bash
git clone <repository-url>
cd PiSelery
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Start Redis:**
```bash
redis-server
```

4. **Start the Celery worker:**
```bash
celery -A main.celery worker --loglevel=info
```

5. **Start the Flask API:**
```bash
python main.py
```

The API will be available at `http://localhost:5000`

## Environment Variables

- `CELERY_BROKER_URL`: Message broker URL (default: `pyamqp://guest@localhost//`)
- `CELERY_RESULT_BACKEND`: Result backend URL (default: `redis://localhost:6379/0`)
- `BASE_URL`: API base URL for testing (default: `http://localhost:5000`)

## Testing

Run the test script to verify API functionality:

```bash
python test_api.py
```

This will test:
- Health check endpoint
- Pi calculation with different precision levels (10, 50, 10000 decimals)
- Progress tracking during calculations

## Algorithm Details

### Chudnovsky Algorithm
The implementation uses the Chudnovsky algorithm, one of the fastest methods for calculating π:

```
π = (426880 * √10005) / Σ
where Σ = Σ_{k=0}^∞ ((-1)^k * (6k)! * (13591409 + 545140134k)) / ((3k)! * (k!)^3 * 640320^{3k + 3/2})
```

### Performance Approximation
The system uses power-law approximation to estimate calculation time:

```
T(n) = exp(a) * n^b
```

Where parameters `a` and `b` are learned from previous calculations and stored in `approximation_params.json`.

## Project Structure

```
PiSelery/
├── main.py                    # Flask API and Celery configuration
├── pi_calculator.py          # Pi calculation algorithms
├── logariphmic_aproximation.py # Performance approximation functions
├── test_api.py              # API testing script
├── requirements.txt         # Python dependencies
├── approximation_params.json # Pre-trained approximation parameters
└── README.md               # This file
```

## API Documentation

Once the server is running, visit `http://localhost:5000/docs/` to access interactive Swagger documentation.

## Usage Examples

### Calculate π to 1000 decimal places:

```python
import requests

# Start calculation
response = requests.post('http://localhost:5000/calculate_pi',
                        json={'n': 1000, 'algorithm': 'chudnovsky'})
task_id = response.json()['task_id']

# Check progress
while True:
    progress = requests.post('http://localhost:5000/check_progress',
                            json={'task_id': task_id}).json()

    if progress['state'] == 'FINISHED':
        print(f"π = {progress['result']}")
        break
    elif progress['state'] == 'FAILURE':
        print(f"Error: {progress['error']}")
        break
    else:
        print(f"Progress: {progress['progress']:.1%}")
```

## Performance Notes

- Calculation time grows approximately as O(n^1.9) where n is the number of decimal places
- Memory usage scales with the precision required
- The system can handle calculations up to at least 10,000 decimal places efficiently

## License

This project is licensed under the MIT License.