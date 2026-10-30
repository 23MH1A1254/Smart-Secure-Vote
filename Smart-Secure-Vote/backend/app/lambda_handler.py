# AWS Lambda adapter. Install mangum in the Lambda build if deploying this template.
from .main import app
try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    handler = app
