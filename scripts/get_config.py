import os

# parse enviroment variables and write to .odoorc
# enviroment variable must prefix with ODOO_
supported_configs = [
    'admin_passwd',
    'dbfilter',
    'data_dir',
    'db_host',
    'db_maxconn',
    'db_password',
    'db_port',
    'db_sslmode',
    'db_template',
    'db_user',
    'db_name',
    'http_interface',
    'http_port',
    'limit_request',
    'limit_memory_hard',
    'limit_memory_soft',
    'limit_time_cpu',
    'limit_time_real',
    'limit_time_real_cron',
    'list_db',
    'log_db',
    'log_db_level',
    'logfile',
    'log_handler',
    'log_level',
    'max_cron_threads',
    'proxy_mode',
    'server_wide_modules',
    'smtp_password',
    'smtp_port',
    'smtp_server',
    'smtp_ssl',
    'smtp_user',
    'test_enable',
    'unaccent',
    'without_demo',
    'workers',
    'running_env',
]


PREFIX = "ODOO_"

with open("odoo.conf","r") as config_file:
    config = config_file.read()

    with open(".odoorc","w") as run_config_file:
        for k, v in os.environ.items():
            if not k.startswith(PREFIX):
                continue
            key = k[len(PREFIX):].lower()
            if key in supported_configs:
                config += f"{key}={v}\n"

        run_config_file.write(config)
