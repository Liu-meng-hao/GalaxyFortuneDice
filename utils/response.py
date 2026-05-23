from schemas.response import ApiResponse


def success(data=None, msg="success"):
    return ApiResponse(
        code=0,
        msg=msg,
        data=data
    )