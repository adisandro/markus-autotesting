#!/usr/bin/env python3

import config
import os
import shutil

header = """[supervisord]

[supervisorctl]

[inet_http_server]
port = 127.0.0.1:9001

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

"""

content = """[program:rq_worker_type{type_ind}]
command={rq} worker {worker_args} {queues}
process_name=%(program_name)%(process_num)
numprocs={numprocs}
directory={directory}
stopsignal=TERM
autostart=true
autorestart=true

"""

try:
	rkw = config.REDIS_CONNECTION_KWARGS
	redis_url = '--url redis://{}:{}/{}'.format(rkw['host'], rkw['port'], rkw['db'])
except KeyError:
	redis_url = ''

with open('supervisord.conf', 'w') as f:
	f.write(header)
	for i, (numprocs, queues) in enumerate(config.WORKERS):
		queue_str = ' '.join(queues)
		c = content.format(rq=shutil.which('rq'),
						   type_ind=i, 
						   worker_args=redis_url, 
						   queues=queue_str, 
						   numprocs=numprocs, 
						   directory=os.path.abspath('server'))
		f.write(c)

