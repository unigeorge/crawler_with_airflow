import os
import sys

import pymysql
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

sys.path.append(os.path.join(os.path.dirname(__file__), '.', 'credentials'))
import data_credential as dc

engine = create_engine(dc.MYSQL_JOB_CRAWLER_URI, pool_pre_ping=True, pool_recycle=3600)
DBSession = sessionmaker(bind=engine)
session = DBSession()


def insert_and_update(base_list):
    for base in base_list:
        session.merge(base)
    session.commit()


def query(sql):
    import pandas as pd
    # check data in mysql
    conn = pymysql.connect(dc.MYSQL_JOB_CRAWLER_INFO)
    cursor = conn.cursor()
    cursor.execute(sql)
    res = cursor.fetchall()
    res_df = pd.DataFrame(res)

    cursor.close()
    conn.close()

    return res_df
