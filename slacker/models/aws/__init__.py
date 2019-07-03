from slacker.database import db


class VM(db.Model):
    __tablename__ = 'vm'
    id = db.Column(db.String, primary_key=True)


class VMOwnership(db.Model):
    """Represents a vm owned by a user and named by an alias"""
    __tablename__ = 'vm_ownership'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="cascade"), primary_key=True)
    vm_id = db.Column(db.String, db.ForeignKey('vm.id', ondelete="cascade"), primary_key=True)
    alias = db.Column(db.String, primary_key=True)
    user = db.relationship("User", backref=db.backref("owned_vms", cascade='all, delete-orphan'))
    vm = db.relationship("VM", backref=db.backref("owners", cascade='all, delete-orphan'))


    def __str__(self):
        return f"VMOwnership(user_id={self.user_id}, vm_id={self.vm_id}, alias={self.alias})"