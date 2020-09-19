# -*- coding: utf-8 -*-

from sqlalchemy import Column, desc
from sqlalchemy.orm import backref

from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import UserMixin

from amp.extensions import db
from amp.utils import get_current_time
from amp.constants import USER, USER_ROLE, ADMIN, INACTIVE, USER_STATUS, \
    SEX_TYPES, STRING_LEN

import pandas as pd

class User(db.Model, UserMixin):

    __tablename__ = 'users'

    id = Column(db.Integer, primary_key=True)
    name = Column(db.String(STRING_LEN), nullable=False, unique=True)
    email = Column(db.String(STRING_LEN), nullable=False, unique=True)
    phone = Column(db.String(STRING_LEN), nullable=False, default="")
    url = Column(db.String(STRING_LEN), nullable=False, default="")
    deposit = Column(db.Numeric, nullable=False, default=0.0)
    location = Column(db.String(STRING_LEN), nullable=False, default="")
    bio = Column(db.Text, default="")
    activation_key = Column(db.String(STRING_LEN))
    create_at = Column(db.DateTime, nullable=False, default=get_current_time)
    update_at = Column(db.DateTime)

    avatar = Column(db.String(STRING_LEN))

    _password = Column('password', db.String(200), nullable=False)

    def _get_password(self):
        return self._password

    def _set_password(self, password):
        self._password = generate_password_hash(password)

    # Hide password encryption by exposing password field only.
    password = db.synonym('_password',
                          descriptor=property(_get_password,
                                              _set_password))

    def check_password(self, password):
        if self.password is None:
            return False
        return check_password_hash(self.password, password)

    _sex = Column('sex', db.Integer, nullable=False, default=1)

    def _get_sex(self):
        return SEX_TYPES.get(self.sex)

    def _set_sex(self, sex):
        self._sex = sex

    sex = db.synonym('_sex', descriptor=property(_get_sex, _set_sex))

    # ================================================================
    role_code = Column(db.SmallInteger, default=USER, nullable=False)

    @property
    def role(self):
        return USER_ROLE[self.role_code]

    def is_admin(self):
        return self.role_code == ADMIN

    # ================================================================
    # One-to-many relationship between users and user_statuses.
    status_code = Column(db.SmallInteger, nullable=False, default=INACTIVE)

    @property
    def status(self):
        return USER_STATUS[self.status_code]

    # ================================================================
    # Class methods

    @classmethod
    def authenticate(cls, login, password):
        user = cls.query.filter(db.or_(
            User.name == login, User.email == login)).first()

        if user:
            authenticated = user.check_password(password)
        else:
            authenticated = False

        return user, authenticated

    @classmethod
    def search(cls, keywords):
        criteria = []
        for keyword in keywords.split():
            keyword = '%' + keyword + '%'
            criteria.append(db.or_(
                User.name.ilike(keyword),
                User.email.ilike(keyword),
            ))
        q = reduce(db.and_, criteria)
        return cls.query.filter(q)

    @classmethod
    def get_by_id(cls, user_id):
        return cls.query.filter_by(id=user_id).first_or_404()

    def check_name(self, name):
        return User.query.filter(db.and_(
            User.name == name, User.email != self.id)).count() == 0

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




# db.session.commit()
# #db.drop_all()
# db.create_all()
# db.session.commit()