DEBUG = True
SECRET_KEY = 'A0Zr98j/3yX R~QBH!667]LWX/,?RT'
SQLALCHEMY_DATABASE_URI = 'sqlite:////usr/local/metaLayer-survey/survey.db'
