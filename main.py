import os
import time
import uuid

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware


# Replace this with the exact email used to log in to the assignment.
EMAIL = os.environ.get('EMAIL')

# Your individually assigned CORS origin.
ALLOWED_ORIGIN = "https://dash-ztttsr.example.com"


# Create the FastAPI application.
api = FastAPI()


# Allow requests only from the assigned origin.
api.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@api.get("/stats")
def get_stats(values: str = Query(...)):
    """
    Calculate descriptive statistics for comma-separated integers.
    """

    try:
        # Split the input and convert each value into an integer.
        numbers = [int(item.strip()) for item in values.split(",")]

        # Reject an empty list.
        if not numbers:
            raise ValueError("At least one integer is required")

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="values must contain comma-separated integers",
        )

    # Calculate statistics from the actual input.
    total = sum(numbers)
    count = len(numbers)

    return {
        "email": EMAIL,
        "count": count,
        "sum": total,
        "min": min(numbers),
        "max": max(numbers),
        "mean": total / count,
    }


class RequestMetricsMiddleware:
    """
    Add a unique request ID and processing time to every response.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Only process HTTP requests.
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                elapsed = time.perf_counter() - start_time

                headers = list(message.get("headers", []))

                headers.append(
                    (b"x-request-id", request_id.encode("ascii"))
                )

                headers.append(
                    (
                        b"x-process-time",
                        f"{max(0.0, elapsed):.6f}".encode("ascii"),
                    )
                )

                message["headers"] = headers

            await send(message)

        await self.app(scope, receive, send_with_headers)


# Wrap the entire FastAPI application so the required headers
# are added even to CORS preflight responses and error responses.
app = RequestMetricsMiddleware(api)
