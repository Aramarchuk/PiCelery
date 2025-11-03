import os
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
          description='API')

pi_model = api.model('PiCalculation', {
    'n': fields.Integer(required=True, description='Number of decimal places'),
    'algorithm': fields.String(required=False, default='chudnovsky',
                               description='chudnovsky')
})

progress_model = api.model('ProgressCheck', {
    'task_id': fields.String(required=True, description='Task ID for status checking')
})

@celery.task(bind=True)
def calculate_pi_task(self, n_decimals):
    """Task for calculating Pi in background using Chudnovsky algorithm"""
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
    @api.expect(pi_model)
    @api.doc('calculate_pi')
    def post(self):
        """Start asynchronous Pi calculation"""
        data = request.get_json()

        if not data or 'n' not in data:
            api.abort(400, "Parameter 'n' is required")

        n = data['n']

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
    def post(self):
        """Check Pi calculation status"""
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
            print(task.info)
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
    def get(self):
        """Check API health"""
        return {'status': 'healthy', 'service': 'Pi Calculator API'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)