from slacker.database import db


class VM(db.Model):
    __tablename__ = 'vm'
    id = db.Column(db.String, primary_key=True)
    owners = db.relationship('User', secondary='ownedvm')


class OwnedVM(db.Model):
    """Model that represents a relationship of ownership between a user and a vm."""
    __tablename__ = 'ownedvm'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    user_name = db.Column(db.String)
    vm_id = db.Column(db.Integer, db.ForeignKey('vm.id'), primary_key=True)
    vm_alias = db.Column(db.String)
