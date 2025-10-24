from flask import jsonify
import time

def success_response(data, message="Success", meta=None):
    response = {
        "status": "success",
        "message": message,
        "data": data,
        "timestamp": int(time.time())
    }
    if meta:
        response["meta"] = meta
    return jsonify(response)

def error_response(message, error_code=400, details=None):
    response = {
        "status": "error",
        "message": message,
        "error_code": error_code,
        "timestamp": int(time.time())
    }
    if details:
        response["details"] = details
    return jsonify(response), error_code

def pagination_meta(page, limit, total):
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "has_next": (page * limit) < total,
        "has_prev": page > 1
    }
