from __future__ import annotations

import uuid

from dotenv import load_dotenv
from flask import Flask, g, request

from .config import Config
from .db import init_db
from .errors import register_error_handlers
from .models import Base
from .routes import api, health, web


def create_app(test_config: dict | None = None) -> Flask:
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    if not test_config:
        Config.validate()

    init_db(app)
    register_error_handlers(app)
    app.register_blueprint(web)
    app.register_blueprint(api)
    app.register_blueprint(health)

    @app.before_request
    def attach_request_id() -> None:
        incoming = request.headers.get("X-Request-ID", "").strip()
        g.request_id = incoming[:80] if incoming else str(uuid.uuid4())

    @app.after_request
    def expose_request_id(response):
        response.headers["X-Request-ID"] = getattr(g, "request_id", "unknown")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; base-uri 'self'; form-action 'self'; "
            "frame-ancestors 'none'; object-src 'none'",
        )
        return response

    engine = app.extensions.get("db_engine")
    if app.config.get("CREATE_SCHEMA") and engine is not None:
        Base.metadata.create_all(engine)

    return app
