from flask import json
from survey import db
import datetime


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True)
    is_admin = db.Column(db.Boolean)

    def __init__(self, email, password, is_admin=False):
        self.email = email
        self.password = password
        self.is_admin = is_admin

    def __repr__(self):
        return '<User %r>' % self.email

    def get_id(self):
        return unicode(self.id)

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True


class Dataset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime)
    accessed = db.Column(db.DateTime)
    active = db.Column(db.Boolean)
    file_id = db.Column(db.String(256))
    file_name = db.Column(db.String(256))
    progress = db.Column(db.Integer)
    errors = db.Column(db.UnicodeText())
    display_name = db.Column(db.UnicodeText())
    description = db.Column(db.UnicodeText())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('user', lazy='dynamic'))

    @classmethod
    def GetByFileId(cls, file_id):
        return Dataset.query.filter_by(file_id=file_id).first()

    @classmethod
    def GetById(cls, id):
        return Dataset.query.filter_by(id=id).first()

    @classmethod
    def GetAllActiveForUser(cls, user):
        return Dataset.query.filter_by(user=user, active=True).order_by(Dataset.accessed.desc()).all()

    def __init__(self, file_id, file_name, user):
        self.created = datetime.datetime.utcnow()
        self.accessed = self.created
        self.active = False
        self.file_id = file_id
        self.file_name = file_name
        self.progress = 0
        self.user = user

    def update_progress(self, progress, errors=None):
        self.progress = progress
        if errors:
            self.errors = '|'.join('%s' % e for e in errors)
        return self

    def activate(self):
        self.active = True
        return self

    def deactivate(self):
        self.active = False
        return self

    def save(self):
        self.accessed = datetime.datetime.utcnow()
        db.session.add(self)
        db.session.commit()
        return self

    def error_messages(self):
        return self.errors.split('|') if self.errors else []


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column(db.Boolean)
    index = db.Column(db.Integer)
    name = db.Column(db.UnicodeText())
    facet_name = db.Column(db.UnicodeText())
    data_type = db.Column(db.String(256))
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))
    dataset = db.relationship('Dataset', backref=db.backref('dataset', lazy='dynamic'))

    @classmethod
    def GetForDataset(cls, dataset):
        return Question.query.filter_by(dataset=dataset, active=True).order_by(Question.index.asc()).all()

    @classmethod
    def GetAllForDataset(cls, dataset):
        return Question.query.filter_by(dataset=dataset).order_by(Question.index.asc()).all()

    def __init__(self, index, name, facet_name, data_type, dataset):
        self.active = False
        self.index = index
        self.name = name
        self.facet_name = facet_name
        self.data_type = data_type
        self.dataset = dataset

    def activate(self):
        self.active = True
        return self

    def deactivate(self):
        self.active = False
        return self

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime)
    _configuration = db.Column(db.UnicodeText())
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))
    dataset = db.relationship('Dataset', backref=db.backref('activity_dataset', lazy='dynamic'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('activity_user', lazy='dynamic'))

    @classmethod
    def GetById(cls, activity_id):
        activity = Activity.query.filter_by(id=activity_id).first()
        return cls._ExpandConfiguration(activity) if activity else None

    @classmethod
    def GetLastForUser(cls, user, dataset=None):
        activity = Activity.GetForUser(user, dataset=dataset)
        activity = [a for a in activity if a.dataset.active]
        return activity[0] if activity else None

    @classmethod
    def GetForUser(cls, user, count=1, dataset=None):
        query = Activity.query.filter_by(user=user)
        if dataset:
            query = query.filter_by(dataset=dataset)
        activity = query.order_by(Activity.created.desc()).limit(count).all()
        activity = [Activity._ExpandConfiguration(a) for a in activity]
        return activity

    @classmethod
    def _ExpandConfiguration(cls, activity):
        activity.configuration = json.loads(activity._configuration) if activity._configuration else None
        activity.configuration['activity_id'] = activity.id
        activity.configuration['created'] = activity.created.strftime('%c')
        return activity

    def __init__(self, user, dataset, configuration):
        self.created = datetime.datetime.utcnow()
        self._configuration = json.dumps(configuration)
        self.user = user
        self.dataset = dataset

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self