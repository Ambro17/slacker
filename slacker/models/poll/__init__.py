"""
Models to support polls


,---------.           ,------------.
|  Poll   |           |   Option   |
|---------|           |------------|
|+id      | 1 ----- * |+ id        |
|+question|           |+ text      |
|+options |           |+ start_date|
`---------`           `------------`
    1                       1
    |                       |
    |                       |
    `-----------+-----------`
                |
                *
           .----------.
           |   Vote   |
           |----------|
           |+id       |
           |+question |
           |+options  |
           `----------`

"""
from operator import itemgetter

from slacker.database import db
from slacker.models.model_utils import CRUDMixin


class Poll(db.Model, CRUDMixin):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String, nullable=False)
    options = db.relationship("Option", backref='poll')
    votes = db.relationship("Vote", backref='poll')
    created_at = db.Column(db.DateTime)
    author = db.Column(db.String)
    ended = db.Column(db.Boolean, default=False)

    @classmethod
    def from_string(cls, poll_string):
        """Creates a poll from a well-defined string.

        Format: <question>? <option>+
        Examples:
            - colors? blue   # Not much of a poll, but still valid.
            - best colors? red blue green yellow

        Returns:
            (Poll, None) - If poll_string is well-formed
            (None, error_msg) - If there was a problem on the poll_string
        """
        try:
            question, rest = poll_string.split('?')
        except ValueError:
            msg = 'Mal formato. Uso: `/poll pregunta? opcion1 opcion2`'
            return None, msg

        if not rest:
            msg = 'Te faltaron las opciones. `/poll pregunta? op1 op2 op3`'
            return None, msg

        options = rest.strip().split()
        if len(options) > 10:
            msg = 'Sólo puede haber 10 opciones como máximo'
            return None, msg

        poll_options = [
            Option(number=i+1, text=op)
            for i, op in enumerate(options)
        ]
        poll = Poll.create(question=question, options=poll_options)
        return poll, None


    def to_dict(self):
        return {
            'question': self.question,
            'options': self.ordered_options()
        }


    def ordered_options(self):
        """Return poll options sorted by number"""
        return sorted(
            [
                (op.number, op.text, len(op.votes))
                for op in self.options
            ], key=itemgetter(0)
        )


    @classmethod
    def format_option(cls, option):
        """Format poll option with or without votes.
        i.e:
            1. option_with_votes `5`
            2. option_with_no_votes
            ...
        """
        msg = f'{option.number}. {option.text}'
        if option.votes:
            msg += f' `{len(option.votes)}`'
        return msg


    def options_to_string(self, sep='\n'):
        return f'{sep}'.join(self.format_option(op) for op in self.options)


    def __str__(self):
        return f'*{self.question}?*\n{self.options_to_string()}'


class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'))
    number = db.Column(db.Integer, nullable=False)
    text = db.Column(db.String, nullable=False)

    votes = db.relationship("Vote", backref='option')



class Vote(db.Model):
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'), primary_key=True)
    option_id = db.Column(db.Integer, db.ForeignKey('option.id'), primary_key=True)
    user_id = db.Column(db.String, primary_key=True)
    user_name = db.Column(db.String, nullable=True)
