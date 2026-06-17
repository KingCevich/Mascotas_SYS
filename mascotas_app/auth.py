import httpx
from django.conf import settings


def get_token_from_request(request):
    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()
    try:
        return request.data.get("token") or request.query_params.get("token")
    except AttributeError:
        return None

#validacion de token a traves de auth_serv, retorna payload del token si es valido, o error si no lo es
def validate_token(token: str):
    if not token:
        return False, {"error": "Token no proporcionado"}

    url = settings.AUTH_SERVICE_URL.rstrip("/") + "/api/auth/validate-token/"
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.post(url, json={"token": token})
    except httpx.RequestError:
        return False, {"error": "No se pudo conectar con auth_serv"}

    try:
        payload = response.json()
    except ValueError:
        return False, {"error": "Respuesta inválida de auth_serv"}

    if response.status_code != 200 or not payload.get("valid"):
        return False, payload

    return True, payload
