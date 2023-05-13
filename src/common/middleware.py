from corsheaders.middleware import CorsMiddleware


class CustomCorsMiddleware(CorsMiddleware):
    def process_response(self, request, response):
        response = super().process_response(request, response)
        response["Cross-Origin-Opener-Policy"] = "same-origin"
        response["Access-Control-Allow-Credentials"] = "true"
        return response
