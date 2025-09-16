import os
import sys
sys.path.append('./')

import pendulum as pdl

# from fabric.api import *
from fabric import task
from invoke.config import Config
from fabric import Connection

import logging
from utils.logger import setup_logger, logging
logger = setup_logger("fabric", logging.DEBUG)

remote_user = 'tzhu'
remote_host = 'maru'
app_name = 'read-ai'

deploy_directory = f"/var/www/{app_name}"
app_directory = os.path.join(deploy_directory, "apps")
shared_directory = os.path.join(deploy_directory, "shared")
logs_directory = os.path.join(shared_directory, "logs")
audios_directory = os.path.join(shared_directory, "audios")
subtitles_directory = os.path.join(shared_directory, "subtitles")
migrations_directory = os.path.join(shared_directory, "migrations")

worker_num = 2
address = '127.0.0.1'
port = 5000
log_level = 'debug'
# 🔧 AI批改功能需要更长的超时时间
timeout = 180  # 增加到180秒以支持增强的流式AI请求
keepalive = 10
max_requests = 1000
max_requests_jitter = 50

# proxy_server = '172.20.1.247' # 0.0.0.0

### Before deploy to a new server:
'''
sudo apt apt-get update && sudo apt-get upgrade -y
sudo apt install python3-virtualenv libpq-dev python3-certbot-apache python3-certbot-nginx postgresql postgresql-contrib
'''


@task
def setup_connection(ctx):
    ctx.c = Connection(remote_host, user=remote_user)


@task(pre=[setup_connection])
def setup(ctx):
    logger.info('Setting development env')
    ctx.c.run(f"sudo mkdir -p {deploy_directory}")
    ctx.c.run(f"sudo mkdir -p {app_directory}")
    ctx.c.run(f"sudo mkdir -p {shared_directory}")
    ctx.c.run(f"sudo mkdir -p {logs_directory}")
    ctx.c.run(f"sudo chown -R {remote_user}:{remote_user} {deploy_directory}")


@task(pre=[setup_connection])
def start_app(ctx):
    """
    启动应用服务器
    修复：使用setsid、disown和完全IO重定向来彻底分离gunicorn进程，
    防止SSH会话一直等待后台进程完成而导致的超时问题
    """
    if remote_host == 'maru':
        logger.info('Kill existing apps...')
        ctx.c.run(f"cd {os.path.join(deploy_directory, 'current')} && export PATH=/home/`whoami`/.local/bin:$PATH && kill $(pgrep -a gunicorn | awk '{{print $1}}') || true")
        logger.info('Spawning new apps...')
        # 🔧 修复：使用专用脚本启动gunicorn，解决SSH会话挂起问题
        ctx.c.run(f"cd {os.path.join(deploy_directory, 'current')} && bash start_gunicorn.sh {worker_num} {address} {port} {timeout} {keepalive} {max_requests} {max_requests_jitter} {log_level} {app_name}", pty=False)
        logger.info("Server started.")
    else:
        activate_cmd = f'source ~/.virtualenvs/{app_name}/bin/activate'
        with ctx.c.prefix(activate_cmd):
            logger.info('Kill existing apps...')
            ctx.c.run(f"cd {os.path.join(deploy_directory, 'current')} && export PATH=/home/`whoami`/.local/bin:$PATH && kill $(pgrep -a gunicorn | awk '{{print $1}}') || true")
            logger.info('Spawning new apps...')
            # 🔧 修复：使用专用脚本启动gunicorn，解决SSH会话挂起问题
            ctx.c.run(f"cd {os.path.join(deploy_directory, 'current')} && bash start_gunicorn.sh {worker_num} {address} {port} {timeout} {keepalive} {max_requests} {max_requests_jitter} {log_level} {app_name}", pty=False)

            logger.info("Server started.")


@task(pre=[setup_connection])
def update_env(ctx):
    # pip install
    logger.info('Update pip packages...')
    if remote_host == 'maru':
        logger.info('Update pip packages...')
        ctx.c.run(f"pip install -r {os.path.join(deploy_directory, 'current', 'requirements.txt')}")
        # logger.info('DB migrating...')
        # ctx.c.run(f"cd {os.path.join(deploy_directory, 'current')} && export PATH=/home/`whoami`/.local/bin:$PATH && python3 db_manage.py migrate")
    else:
        with ctx.c.prefix(f'source ~/.virtualenvs/{app_name}/bin/activate'):
            logger.info('Update pip packages...')
            ctx.c.run(f"pip install -r {os.path.join(deploy_directory, 'current', 'requirements.txt')}")
            # logger.info('DB migrating...')
            # ctx.c.run(f"cd {os.path.join(deploy_directory, 'current')} && export PATH=/home/`whoami`/.local/bin:$PATH && python3 db_manage.py migrate")


@task(pre=[setup_connection], post=[update_env, start_app])
def deploy(ctx):
    app_version = pdl.now().strftime('%Y%m%d-%H%M%S')
    version_directory = os.path.join(app_directory, app_version)

    tar_file = f'{app_version}.tar.gz'

    # ctx.c.local(f"pip freeze > requirements.txt.lock")
    ctx.c.local(f"tar czf ./tmp/{tar_file} --exclude=./log --exclude=./.git --exclude=./tmp --exclude=./app/static/audios --exclude=./app/static/subtitles . ")
    ctx.c.put(f"./tmp/{tar_file}", app_directory)
    ctx.c.run(f"mkdir -p {version_directory}")
    ctx.c.run(f"tar xzf {os.path.join(app_directory, tar_file)} -C {version_directory}")
    ctx.c.run(f"rm -f {os.path.join(app_directory, tar_file)}")

    ctx.c.run(f"rm -f {os.path.join(deploy_directory, 'current')}")
    ctx.c.run(f"ln -s {version_directory} {os.path.join(deploy_directory, 'current')}")
    ctx.c.run(f"ln -s {logs_directory} {os.path.join(deploy_directory, 'current', 'log')}")
    ctx.c.run(f"ln -s {audios_directory} {os.path.join(deploy_directory, 'current', 'app', 'static', 'audios')}")
    ctx.c.run(f"ln -s {subtitles_directory} {os.path.join(deploy_directory, 'current', 'app', 'static', 'subtitles')}")

@task(pre=[setup_connection])
def seed(ctx):
    ctx.c.run(f"cd {os.path.join(deploy_directory, 'current')} && export PATH=/home/`whoami`/.local/bin:$PATH && python3 db_manage.py seed")


@task(pre=[setup_connection])
def migrate(ctx):
    ctx.c.run(f"cd {os.path.join(deploy_directory, 'current')} && export PATH=/home/`whoami`/.local/bin:$PATH && python3 db_manage.py migrate")
