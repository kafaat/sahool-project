from fastapi import Request

def abac_guard(request: Request, action: str, resource: str): return True
