from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict, deque
import uuid
import time
from fastapi import Response

EMAIL = "25f1002209@ds.study.iitm.ac.in"

ALLOWED_ORIGIN = "https://app-11215s.example.com"
EXAM_ORIGIN = "https://exam.sanand.workers.dev"

RATE_LIMIT = 15
WINDOW = 10

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        ALLOWED_ORIGIN,
        "https://exam.sanand.workers.dev",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        request.state.request_id = request_id

        response = await call_next(request)

        # Echo the request ID in the response header
        response.headers["X-Request-ID"] = request_id

        return response

app.add_middleware(RequestIDMiddleware)

buckets = defaultdict(deque)

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client = request.headers.get("X-Client-Id", "anonymous")
        now = time.time()
        q = buckets[client]
        while q and now - q[0] > WINDOW:
            q.popleft()
        if len(q) >= RATE_LIMIT:
            return JSONResponse(status_code=429, content={"detail":"Rate limit exceeded"})
        q.append(now)
        return await call_next(request)

app.add_middleware(RateLimitMiddleware)

@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }

@app.options("/ping")
async def ping_options():
    return Response(status_code=204)