def success_response(data=None, message="요청 성공"):
    return {
        "success": True,
        "message": message,
        "data": data,
        "error": None
    }


def error_response(message="요청 실패", error=None):
    return {
        "success": False,
        "message": message,
        "data": None,
        "error": error
    }