from slacker.database import db
from slacker.models.model_utils import CRUDMixin


class Sticker(db.Model, CRUDMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    image_url = db.Column(db.String, nullable=False)
