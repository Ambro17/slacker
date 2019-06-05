from slacker.database import db


class VM(db.Model):
    __tablename__ = 'vm'
    id = db.Column(db.String, primary_key=True)


class VMOwnership(db.Model):
    __tablename__ = 'vm_ownership'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    vm_id = db.Column(db.String, db.ForeignKey('vm.id'), primary_key=True)
    alias = db.Column(db.String)
    user = db.relationship("User", backref=db.backref("owned_vms"))
    vm = db.relationship("VM", backref=db.backref("owners"))
