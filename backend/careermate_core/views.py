import logging
import time
from django.conf import settings
from django.db import connection
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """
    Health check endpoint for CareerMate AI.
    Verifies API responsiveness and database connectivity.
    Dynamically detects the database engine (PostgreSQL / MySQL) and suppresses internal error leakage.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        start_time = time.time()
        db_status = "unhealthy"
        db_response_time_ms = None

        # Dynamically determine the active database engine / vendor
        db_vendor = connection.vendor  # 'postgresql', 'mysql', 'sqlite', etc.
        engine_name = connection.settings_dict.get('ENGINE', '').split('.')[-1]
        active_engine = db_vendor or engine_name

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                row = cursor.fetchone()
                if row and row[0] == 1:
                    db_status = "healthy"
            db_response_time_ms = round((time.time() - start_time) * 1000, 2)
        except Exception as exc:
            logger.error("Health check database probe failed: %s", exc, exc_info=True)
            db_status = "unhealthy"

        is_healthy = db_status == "healthy"
        status_code = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

        payload = {
            "status": "healthy" if is_healthy else "degraded",
            "timestamp": timezone.now().isoformat(),
            "environment": "production" if not settings.DEBUG else "development",
            "version": "1.0.0",
            "checks": {
                "database": {
                    "engine": active_engine,
                    "status": db_status,
                    "latency_ms": db_response_time_ms,
                },
                "api": {
                    "status": "healthy",
                }
            }
        }
        return Response(payload, status=status_code)
        return Response(payload, status=status_code)
