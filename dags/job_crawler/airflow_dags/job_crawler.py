from datetime import datetime, timedelta

from airflow import DAG
from airflow.models import Variable
from airflow.operators.bash import BashOperator
from airflow.operators.email import EmailOperator
from airflow.operators.python import PythonOperator
from airflow.providers.dingding.operators.dingding import DingdingOperator
from airflow.providers.mysql.hooks.mysql import MySqlHook

with DAG(
        dag_id='job_crawler',
        default_args={
            'depends_on_past': False,
            'email': Variable.get('admin_email'),
            'email_on_failure': False,
            'email_on_success': False,
            'email_on_retry': False,
            'retries': 2,
            'retry_delay': timedelta(minutes=1)
        },
        description='A simple DAG for job_crawler',
        schedule_interval='@daily',
        start_date=datetime(2021, 1, 1),
        catchup=False,
        tags=['job'],
) as dag:
    print_date = BashOperator(
        task_id='print_date',
        bash_command='date',
    )

    def build_email_of_new_arrival(dt, target_job, **context):
        sql_hook = MySqlHook().get_hook(conn_id='job_crawler')
        sql = 'select * from job_info where to_days(create_time)=to_days("%s") and target_job="%s"' % (dt, target_job)
        res_df = sql_hook.get_pandas_df(sql)

        if res_df.empty:
            html_content = '<h2>今日无新增 %s 相关岗位<h2>' % target_job
            dingding_markdown = '### 今日无新增 %s 岗位' % target_job
        else:
            file_name = 'new_arrival_job_for_%s_%s.csv' % (target_job, dt)
            res_df.to_csv(file_name, encoding='utf_8_sig')
            html_content = '<h2>今日新增 %s 相关岗位如下（详细信息请查看附件）：<h2>' % target_job + res_df.iloc[:, [0, 1, 4]].to_html()
            dingding_markdown = '### 今日新增 %s 相关岗位如下（详细信息请查看邮件）：\n' % target_job \
                                + res_df.iloc[:, [0, 1, 4]].to_markdown().replace('\n', '\n\n---\n')

        email_op = EmailOperator(
            task_id='send_email',
            to=Variable.get('target_job_email', deserialize_json=True).get(target_job),
            subject='New_Job_Info_of_%s_%s' % (target_job, dt),
            html_content=html_content,
            files=[] if res_df.empty else [file_name]
        )
        email_op.execute(context)

        dingding_op = DingdingOperator(
            task_id='send_dingding',
            dingding_conn_id='dingding',
            message_type='markdown',
            message={
                'title': '今日 %s 相关岗位信息' % target_job,
                'text': dingding_markdown
            },
            at_all=True
        )
        dingding_op.execute(context)

    for target_job in Variable.get('target_job_email', deserialize_json=True).keys():

        crawl_boss_zhipin = BashOperator(
            task_id='crawl_boss_zhipin_for_%s' % target_job,
            depends_on_past=False,
            bash_command='cd /opt/airflow/dags/job_crawler/common_package/crawler '
                         '&& python boss_zhipin.py --headless --target_job %s --cookies' % target_job,
            retries=0,
        )

        send_new_arrival = PythonOperator(
            task_id="send_new_arrival_for_%s" % target_job,
            python_callable=build_email_of_new_arrival,
            op_kwargs={'dt': '{{ macros.ds_add(ds, 1) }}', 'target_job': target_job},
            provide_context=True
        )

        print_date >> crawl_boss_zhipin >> send_new_arrival

    dag.doc_md = """
    This DAG downloads job information
    """
