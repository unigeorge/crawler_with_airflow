# Crawler with Airflow

## Information

Use docker-compose commands to control the docker images and containers.

## Notes

- Put the cookies file into `dags/job_crawler/common_package/credentials` or use `dags/job_crawler/common_package/utils/base_util.py` to generate a file.
- Put `airflow.cfg ` into `./` as airflow's config file.
- If bash_command in the dag file `job_crawler.py` uses `--proxied` arg, [proxy_pool](https://github.com/jhao104/proxy_pool) needs to be enabled at the beginning. You can replace it with your paid proxy account.
- Get `COPY ./airflow.cfg airflow.cfg` commented out in the Dockerfile if you don't have your own airflow.cfg for copying. Check [Airflow Document](https://airflow.apache.org/docs/apache-airflow/stable/start/docker.html) for more information about Airflow and Docker.