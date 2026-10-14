"""Application factory and package initialization for TECH5.

This module initializes the Flask application, establishes database tables,
and registers the Component A (Visualization & Recommendation) blueprint.
"""

import os
from typing import Any

import flask

from app import config
from app.persistence import database
from app.visualization import routes as visualization_routes


def create_app(test_config: dict[str, Any] | None = None) -> flask.Flask:
    """Creates and configures an instance of the Flask application.

    Args:
        test_config: Optional configuration overrides for test execution.

    Returns:
        The configured Flask application object.
    """
    app = flask.Flask(
        __name__,
        template_folder=os.path.join(
            os.path.dirname(__file__), "visualization", "templates"
        ),
        static_folder=os.path.join(
            os.path.dirname(__file__), "visualization", "static"
        ),
    )

    app.config.from_object(config.Config)
    if test_config is not None:
        app.config.from_mapping(test_config)

    app.secret_key = app.config.get(
        "SECRET_KEY", "tech5-decision-support-secret-key-2026"
    )

    # Initialize relational database tables
    db_path = app.config.get("DATABASE_PATH")
    if db_path:
        db_mgr = database.DatabaseManager(db_path)
        database.db_manager = db_mgr
        db_mgr.initialize_schema()

    # Register Component A (Visualization & Recommendation) blueprint
    app.register_blueprint(visualization_routes.web_bp)

    return app
