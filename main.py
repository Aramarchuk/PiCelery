import os
import redis
from datetime import datetime, timezone
from typing import Dict, Any, Tuple
from flask import Flask, request
from flask_restx import Api, Resource, fields
from celery import Celery
from pi_calculator import calculate_pi

app = Flask(__name__)

celery_broker_url = os.environ.get('CELERY_BROKER_URL', 'pyamqp://guest@localhost//')
celery_result_backend = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

celery = Celery(
    'pi_calculator_tasks',
    broker=celery_broker_url,
    backend=celery_result_backend
)

celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

api = Api(app, doc='/docs/', title='Pi Calculator API', version='1.0',
          description='A high-performance REST API for calculating π (Pi) to arbitrary precision using the Chudnovsky algorithm with Celery for asynchronous task processing.')

pi_model = api.model('PiCalculation', {
    'n': fields.Integer(required=True, description='Number of decimal places for π calculation'),
})

progress_model = api.model('ProgressCheck', {
    'task_id': fields.String(required=True, description='Task ID for status checking')
})

@celery.task(bind=True)
def calculate_pi_task(self, n_decimals: int) -> Dict[str, Any]:
    """
    Celery task for calculating π (Pi) to specified decimal places.

    This task executes the Chudnovsky algorithm asynchronously, providing
    real-time progress updates during the calculation process.

    Args:
        n_decimals (int): Number of decimal places to calculate π to.
                         Must be a positive integer.

    Returns:
        dict: A dictionary containing:
            - state (str): Final task state ('FINISHED')
            - progress (float): Completion percentage (1.0)
            - result (str): Calculated π value as string

    Raises:
        Exception: Propagates any calculation errors to the Celery worker.
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'progress': 0.0, 'task_id': self.request.id}
        )

        result = calculate_pi(
            n_decimals,
            self.request.id,
            self.update_state
        )

        return {
            'state': 'FINISHED',
            'progress': 1.0,
            'result': result
        }
    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={'progress': 0.0, 'error': str(e)}
        )
        raise

@api.route('/calculate_pi')
class CalculatePi(Resource):
    @api.doc('calculate_pi', params={'n': {'description': 'Number of decimal places for π calculation', 'type': 'integer', 'required': True}})
    def get(self) -> Tuple[Dict[str, Any], int]:
        """
        Start asynchronous π (Pi) calculation.

        Initiates a background task to calculate π to the specified number of
        decimal places using the Chudnovsky algorithm.

        Query Parameters:
            n (int): Number of decimal places for π calculation.
                    Must be a positive integer.

        Returns:
            tuple: A tuple containing:
                - dict: Response with task information:
                    - message (str): Confirmation message
                    - task_id (str): Unique identifier for tracking progress
                    - decimals (int): Number of decimal places requested
                - int: HTTP status code (202 Accepted)

        Raises:
            400: If 'n' parameter is missing or invalid (not a positive integer)

        Example:
            GET /calculate_pi?n=1000
        """
        n = request.args.get('n', type=int)

        if not isinstance(n, int) or n < 1:
            api.abort(400, "Parameter 'n' must be a positive integer")

        task = calculate_pi_task.delay(n)

        return {
            'message': 'Pi calculation started',
            'task_id': task.id,
            'decimals': n
        }, 202


@api.route('/check_progress')
class CheckProgress(Resource):
    @api.expect(progress_model)
    @api.doc('check_progress')
    def post(self) -> Dict[str, Any]:
        """
        Check π (Pi) calculation progress and status.

        Retrieves the current status of a previously initiated π calculation
        task, including progress percentage and results if completed.

        Request Body:
            {
                "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
            }

        Returns:
            dict: Response containing task status information:
                - state (str): Current task state ('PROGRESS', 'FINISHED', 'FAILURE')
                - progress (float): Completion percentage (0.0 to 1.0)
                - result (str, optional): Calculated π value if completed
                - error (str, optional): Error message if calculation failed
                - task_id (str, optional): Task identifier
                - iteration (int, optional): Current iteration number
                - total_iterations (int, optional): Total iterations required
                - elapsed_time (float, optional): Time elapsed in seconds

        Raises:
            400: If 'task_id' parameter is missing or invalid

        Example:
            POST /check_progress
            {"task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"}
        """
        data = request.get_json()

        if not data or 'task_id' not in data:
            api.abort(400, "Parameter 'task_id' is required")

        task_id = data['task_id']
        task = calculate_pi_task.AsyncResult(task_id)

        if task.state == 'PENDING':
            response = {
                'state': 'PROGRESS',
                'progress': 0.0,
                'result': None
            }
        elif task.state == 'PROGRESS':
            response = {
                'state': 'PROGRESS',
                'progress': task.info.get('progress', 0.0),
                'result': None
            }
        elif task.state == 'SUCCESS':
            response = {
                'state': 'FINISHED',
                'progress': 1.0,
                'result': task.info.get('result')
            }
        else:
            response = {
                'state': 'FAILURE',
                'progress': 0.0,
                'result': None,
                'error': str(task.info)
            }

        return response

@api.route('/health')
class HealthCheck(Resource):
    @api.doc('health_check')
    def get(self) -> Dict[str, Any]:
        """
        Comprehensive health check endpoint for the API service.

        Checks the health status of the API and its dependencies (Redis, Celery workers)
        to ensure the service is fully operational.

        Returns:
            dict: Detailed health status response:
                - status (str): Overall service health status ('healthy', 'degraded', 'unhealthy')
                - service (str): Service name for identification
                - timestamp (str): ISO timestamp of the health check
                - checks (dict): Detailed status of each component:
                    - redis (str): Redis connection status
                    - celery (str): Celery worker availability status
                    - api (str): API service status

        Example:
            GET /health
        """
        health_status = {
            'status': 'healthy',
            'service': 'Pi Calculator API',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'checks': {
                'api': 'healthy'
            }
        }

        # Check Redis connection
        try:
            redis_client = redis.from_url(celery_result_backend)
            redis_client.ping()
            health_status['checks']['redis'] = 'healthy'
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['checks']['redis'] = f'unhealthy: {str(e)}'

        # Check Celery workers
        try:
            inspect = celery.control.inspect()
            stats = inspect.stats()
            if stats and len(stats) > 0:
                health_status['checks']['celery'] = f'healthy ({len(stats)} workers)'
            else:
                if health_status['status'] == 'healthy':
                    health_status['status'] = 'degraded'
                health_status['checks']['celery'] = 'no workers available'
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['checks']['celery'] = f'unhealthy: {str(e)}'

        return health_status

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)