from schemas.response import ApiResponse


def success(data=None, msg="success"):
    return ApiResponse(
        code=200,
        msg=msg,
        data=data
    )