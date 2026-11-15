from fastapi import Request

def get_store(request: Request):
    return request.app.state.store

def get_settings(request: Request):
    return request.app.state.settings
