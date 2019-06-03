from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db():
    import slacker.models
    from slacker import create_app
    app = create_app()
    with app.app_context():
        db.create_all()
