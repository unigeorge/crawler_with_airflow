# base MYSQL_INFO
MYSQL_INFO = {
    'user': 'user',
    'password': 'password',
    'host': 'host',
    'port': 3306
}

# base MYSQL_URI
MYSQL_URI = 'mysql+pymysql://user:password@host:3306/%s?charset=utf8'


# MYSQL_INFO
MYSQL_JOB_CRAWLER_INFO = MYSQL_INFO.copy()
MYSQL_JOB_CRAWLER_INFO.update(database='job_crawler')

# MYSQL_URI
MYSQL_JOB_CRAWLER_URI = MYSQL_URI % 'job_crawler'

# proxy address
PROXY_ADD = 'http://127.0.0.1:5010'
