__author__ = 'Nik Burmeister'
from __init__ import app, login_manager
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import pandas as pd
from sqlalchemy.engine import reflection
from sqlalchemy import *


db = SQLAlchemy(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class ORM(object):

    @staticmethod
    def records_to_dataframe(records):
        return pd.read_sql(records.statement, records.session.bind)

    def convert_to_dict(record):
        """
        # TODO: COMMENT
        :param record:
        :return:
        """
        d = {}
        for column in record.__table__.columns:
            d[column.name] = str(getattr(record, column.name))
        return d

    @classmethod
    def remove_record_from_table(cls, record):
        cls.query.filter(cls.id == record.id).delete()
        db.session.commit()

    @classmethod
    def add_record(cls, record, **kwargs):
        obj_dict = cls.convert_to_dict(record)
        record_to_add = {}
        for cls_column in cls.__table__.columns:
            for record_col in obj_dict.keys():
                if record_col != 'pid' and cls_column.name == record_col:
                    record_to_add[cls_column.name] = obj_dict[record_col]

        for kwarg in kwargs:
            record_to_add[kwarg] = kwargs[kwarg]
        removed_record = cls(**record_to_add)
        db.session.add(removed_record)
        db.session.commit()

        # try:
        #     db.session.add(removed_record)
        #     db.session.commit()
        # except:
        #     print("error adding single record in models")




class User(db.Model, UserMixin, ORM):

    __tablename__ = "user"

    pid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(120), unique=False, nullable=False)
    last_name = db.Column(db.String(120), unique=False, nullable=False)
    company_name = db.Column(db.Integer, db.ForeignKey('sponsor.pid'))
    company_email = db.Column(db.String(120), unique=True, nullable=False)
    company_phone = db.Column(db.String(11), unique=False, nullable=True)
    password = db.Column(db.String(60), nullable=False)


class State(db.Model, ORM):

    __tablename__ = "state"

    fips = db.Column(db.String, primary_key=True, nullable=False)
    name = db.Column(db.String, nullable=False, unique=True)
    abbreviation = db.Column(db.String, nullable=False, unique=True)
    region = db.Column(db.Integer, nullable=False, unique=False)
    division = db.Column(db.Integer, nullable=False, unique=False)

    properties = db.relationship("Property", backref="property_state")


class Sponsor(db.Model, ORM):

    __tablename__ = "sponsor"

    pid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    alias = db.Column(db.String(120), nullable=True)
    properties = db.relationship("Property", backref="property_sponsor")


class Portfolio(db.Model, ORM):

    __tablename__ = "portfolio"
    pid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, unique=True, nullable=False)
    properties = db.relationship("Property", backref="property_portfolio")


class AssetClass(db.Model, ORM):

    __tablename__ = "asset_class"

    pid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asset_class = db.Column(db.String, unique=True, nullable=False)
    properties = db.relationship("Property", backref="property_asset_class")


class AssetCategories(db.Model, ORM):

    __tablename__ = "asset_category"
    pid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asset_category = db.Column(db.String, unique=True, nullable=False)
    properties = db.relationship("Property", backref="property_asset_category")


class Property(db.Model, ORM):

    __tablename__ = "property"

    pid = db.Column(db.Integer, primary_key=True)
    report_level = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String, nullable=False)
    name = db.Column(db.String, unique=True)
    alias = db.Column(db.String, nullable=True)
    portfolio = db.Column(db.Integer, db.ForeignKey('portfolio.pid'))
    address = db.Column(db.String)
    city = db.Column(db.String)
    state = db.Column(db.String, db.ForeignKey('state.fips'))
    zip = db.Column(db.String)
    # TODO: Foreign Key
    msa = db.Column(db.String)
    asset_category = db.Column(db.Integer, db.ForeignKey('asset_category.pid'))
    asset_class = db.Column(db.Integer, db.ForeignKey('asset_class.pid'))

    units = db.Column(db.Integer)
    # # TODO: MAKE REQUIRED
    square_feet = db.Column(db.Numeric)
    buildings = db.Column(db.Integer)
    year_built = db.Column(db.String)
    yardi_id = db.Column(db.String, nullable=True)
    sponsor = db.Column(db.Integer, db.ForeignKey('sponsor.pid'))
    acquisition_date = db.Column(db.Date)

    # TODO: LONGITUDE AND LATITUDE
    longitude = db.Column(db.Numeric, nullable=True)
    latitude = db.Column(db.Numeric, nullable=True)

    qrm = db.relationship("QuarterlyReportMetrics", cascade="all,delete")

    # off_market = db.Column(db.String)
    # purchase_price = db.Column(db.Integer)
    # price_per_unit = db.Column(db.Numeric)
    # price_per_sf = db.Column(db.Numeric)
    # fund_I_equity = db.Column(db.Numeric)
    # fund_II_equity = db.Column(db.Numeric)
    # fund_III_equity = db.Column(db.Numeric)
    # fund_IV_equity = db.Column(db.Numeric)
    # fund_V_equity = db.Column(db.Numeric)
    # legacy_fund_equity = db.Column(db.Numeric)
    # co_investor_equity = db.Column(db.Numeric)
    # sponsor_equity = db.Column(db.Numeric)
    # total_equity = db.Column(db.Numeric)
    # original_debt = db.Column(db.Numeric)
    # current_debt = db.Column(db.Numeric)
    # lender = db.Column(db.String)
    # interest_rate = db.Column(db.String)
    # spread = db.Column(db.String)
    # io_end = db.Column(db.Date)
    # maturity = db.Column(db.Date)
    # fund_I_B = db.Column(db.Integer, default=False)
    # fund_II_B = db.Column(db.Integer, default=False)
    # fund_III_B = db.Column(db.Integer, default=False)
    # fund_IV_B = db.Column(db.Integer, default=False)

    @staticmethod
    def get_property_by_name(property_name):
        res = Property.query.filter(Property.name.like(property_name)).all()
        if len(res) == 1:
            return res[0]
        else:
            # todo: error
            raise Exception


class QuarterlyReportMetrics(db.Model, ORM):

    __tablename__ = "quarterlyreportmetrics"

    property_id = db.Column(
        db.Integer,
        db.ForeignKey('property.pid'),
        primary_key=True
    )

    date = db.Column(
        db.Date,
        primary_key=True
    )

    occupancy = db.Column(db.Numeric, nullable=True)
    quarterly_distribution_per = db.Column(db.Numeric, nullable=True)
    quarterly_distribution_abs = db.Column(db.Numeric, nullable=True)
    ytd_distribution_per = db.Column(db.Numeric, nullable=True)
    ytd_distribution_abs = db.Column(db.Numeric, nullable=True)


# class FinancialStatementMappings(db.Model, ORM):
#
#     __tablename__ = 'financial_statement_mappings'
#
#
# class FinancialStatementCategories(db.model, ORM):
#
#     __tablename__ = 'financial_statement_categories'
#
#     category_pid = db.Column(db.String, primary_key=True, unique=True)
#     category_name = db.Column(db.String, primary_key=True, unique=True)




db.session.commit()
#db.drop_all()
db.create_all()
db.session.commit()



# class ScrapedComments(db.Model, ORM):
#
#     __tablename__ = 'scraped_comments'
#
#     comment_id = db.Column('comment_id', db.String, primary_key=True)
#     date_found = db.Column('date_found', db.Date, primary_key=False)
#     username = db.Column('username', db.String, primary_key=False)
#     user_comment = db.Column('user_comment', db.String, primary_key=False)
#     comment_date = db.Column('comment_date', db.DateTime, primary_key=False)
#     reddit_link = db.Column('reddit_link', db.String, primary_key=False)
#     subreddit = db.Column('subreddit', db.String, primary_key=False)
#     submission_title = db.Column('submission_title', db.String, primary_key=False)


# class FlaggedComments(db.Model, ORM):
#
#     __tablename__ = 'flagged_comments'
#
#     df_cols = ['ID', 'Comment ID', 'Date Found', 'Username', 'Comment', "Polarity",
#                'Subjectivity', 'Comment Date', 'Language', 'Link', 'r/', 'Submission Title', 'See Details']
#
#     id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
#     comment_id = db.Column('comment_id', db.String, primary_key=False, unique=True)
#     date_found = db.Column('date_found', db.Date, primary_key=False)
#     username = db.Column('username', db.String, primary_key=False)
#     user_comment = db.Column('user_comment', db.String, primary_key=False)
#     polarity = db.Column('polarity', db.Float, primary_key=False)
#     subjectivity = db.Column('subjectivity', db.Float, primary_key=False)
#     comment_date = db.Column('comment_date', db.Date, primary_key=False)
#     detected_language = db.Column('detected_language', db.String, primary_key=False)
#     reddit_link = db.Column('reddit_link', db.String, primary_key=False)
#     subreddit = db.Column('subreddit', db.String, primary_key=False)
#     submission_title = db.Column('submission_title', db.String, primary_key=False)
#     was_user_contacted = db.Column('was_user_contacted', db.Boolean, primary_key=False, default=0)
#     was_comment_deleted = db.Column('was_comment_deleted', db.Boolean, primary_key=False, default=0)
#
#     primary_keywords = db.relationship('PrimaryKeywords', secondary=flagged_comments_primary_key_mapping,
#                                        backref=db.backref('fc_pk_mapping', lazy='dynamic'), cascade="all,delete")
#     secondary_keywords = db.relationship('SecondaryKeywords', secondary=flagged_comments_secondary_key_mapping,
#                                        backref=db.backref('fc_sk_mapping', lazy='dynamic'), cascade="all,delete")
#
#     @classmethod
#     def was_comment_removed(cls, username):
#         return len(db.session.query(FlaggedComments).filter(FlaggedComments.username.like(username)).filter(
#             FlaggedComments.was_comment_deleted.is_(True)).all()) > 0
#
#     @classmethod
#     def was_user_messaged(cls, username):
#         return len(db.session.query(FlaggedComments).filter(FlaggedComments.username.like(username)).filter(
#             FlaggedComments.was_user_contacted.is_(True)).all()) > 0
#
#
#     @staticmethod
#     def format_df_columns(df, *args):
#         cols = copy.deepcopy(FlaggedComments.df_cols)
#         for arg in args:
#             if arg in cols:
#                 cols.remove(arg)
#         df.columns = cols
#         return df
#
#     def remove_record_from_flagged_and_add_to_processed(self,
#                                                         message=""):
#
#         sent_message = Messages(sender=self.username,
#                                 recipient=self.username,
#                                 message=message,
#                                 date_sent=datetime.today())
#         db.session.add(sent_message)
#
#         # REMINDER: ALWAYS DELETE AFTER TRANSFER
#         del self
#         db.session.commit()


# class Messages(db.Model, ORM):
#     id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
#     sender = db.Column('sender', db.String, primary_key=False)
#     recipient = db.Column('recipient', db.String, primary_key=False)
#     subject = db.Column('subject', db.String, primary_key=False)
#     body = db.Column('body', db.Text, primary_key=False)
#     date_sent = db.Column('date_sent', db.DateTime, primary_key=False)
#     has_been_sent_for_processing = db.Column('has_been_sent_for_processing', db.Integer, primary_key=False, default=0)
#     ca_user_id_assoc = db.Column('ca_user_id_assoc', db.String, primary_key=False) # do we even need?
#
#     def __repr__(self):
#         return "{un} {em} {imf} {wb} {wto}".format(un=self.sender,
#                                                    em=self.recipient,
#                                                    imf=self.subject,
#                                                    wb=self.message,
#                                                    wto=self.date_sent)


# primary_key_subscribers = db.Table('primary_key_subscribers',
#                              db.Column('company', db.Integer, db.ForeignKey('company.id')),
#                              db.Column('primary_keywords', db.Integer, db.ForeignKey('primary_keywords.id', ondelete='cascade')))
#
# secondary_key_subscribers = db.Table('secondary_key_subscribers',
#                              db.Column('company', db.Integer, db.ForeignKey('company.id')),
#                              db.Column('secondary_keywords', db.Integer, db.ForeignKey('secondary_keywords.id', ondelete='cascade')))
#
# flagged_comments_primary_key_mapping = db.Table('flagged_comments_primary_key_mapping',
#                                                 db.Column('flagged_comments', db.Integer,
#                                                           db.ForeignKey('flagged_comments.id', ondelete='cascade')),
#                                                 db.Column('primary_key', db.Integer,
#                                                           db.ForeignKey('primary_keywords.id', ondelete='cascade')))
#
# flagged_comments_secondary_key_mapping = db.Table('flagged_comments_secondary_key_mapping',
#                                                 db.Column('flagged_comments', db.Integer,
#                                                           db.ForeignKey('flagged_comments.id', ondelete='cascade')),
#                                                 db.Column('secondary_key', db.Integer,
#                                                           db.ForeignKey('secondary_keywords.id', ondelete='cascade')))


# class Company(db.Model, ORM):
#
#     __tablename__ = 'company'
#
#     id = db.Column(db.Integer, primary_key=True)
#     company_name = db.Column(db.String(120), unique=True, nullable=False)
#     users = db.relationship('Users', backref='companyname')
#     primary_keywords = db.relationship('PrimaryKeywords', secondary=primary_key_subscribers, backref=db.backref(
#         'primary_key_subs', lazy='dynamic'))
#     secondary_keywords = db.relationship('SecondaryKeywords', secondary=secondary_key_subscribers, backref=db.backref(
#         'secondary_key_subs', lazy='dynamic'))
#
#
# class PrimaryKeywords(db.Model, ORM):
#
#     __tablename__ = 'primary_keywords'
#
#     id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
#     primary_keyword = db.Column('primary_keyword', db.String, unique=True)
#
#
# class SecondaryKeywords(db.Model, ORM):
#
#     __tablename__ = 'secondary_keywords'
#
#     id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
#     secondary_keyword = db.Column('secondary_keyword', db.String, unique=True)
