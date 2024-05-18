import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://case113201:@Ntub_113201@140.131.114.242/113-NTUB'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'recordings')
