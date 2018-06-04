#!/usr/bin/env python3

import sys
import argparse
import rq
import json
import inspect
import autotest_server as ats
import config

### HELPER FUNCTIONS ###

def job_id(markus_address, run_id, **kw):
    """
    Return a unique job id for each enqueued job
    based on the markus_address and the run_id
    """
    return '{}_{}'.format(markus_address, run_id)

def check_args(func, *args, **kwargs):
    """
    Raises an error if calling the function func with args and
    kwargs would raise an error.
    """
    try:
        inspect.signature(func).bind(*args, **kwargs)
    except TypeError as e:
        raise type(e)('{}\nWith args: {}\nWith kwargs:{}'.format(e, args, tuple(kwargs))).with_traceback(sys.exc_info()[2])

def queue_name(queue, i):
    """
    Return a formatted queue name from a queue object and an integer
    or some other unique identifier.
    """
    return '{}{}'.format(queue.type, i)

def get_queue(**kw):
    """
    Return a queue. The returned queue is one whose condition function
    returns True when called with the arguments in **kw. 
    """
    for queue_type in config.WORKER_QUEUES:
        if queue_type['filter'](**kw):
            return rq.Queue(queue_type['name'], connection=ats.redis_connection())
    raise RuntimeError('cannot enqueue job: unable to determine correct queue type') 

def print_queue_info(queue):
    """
    Print json to stdout indicating the number of jobs in the queue and the 
    average pop interval during the current burst of jobs.
    """
    print(json.dumps({'count' : queue.count, 'pop_rate': ats.get_avg_pop_interval(queue.name)}))

def check_test_script_files_exist(markus_address, assignment_id, **kw):
    if ats.test_script_directory(markus_address, assignment_id) is None:
        raise RuntimeError('cannot find test script files: please upload some before running tests')


### COMMAND FUNCTIONS ###

def run_test(user_type, batch_id, **kw):
    """
    Enqueue a test run job with keyword arguments specified in **kw
    """
    queue = get_queue(user_type=user_type, batch_id=batch_id, **kw)
    check_args(ats.run_test, **kw)
    check_test_script_files_exist(**kw)
    print_queue_info(queue)
    queue.enqueue_call(ats.run_test, kwargs=kw, job_id=job_id(**kw))

def update_scripts(**kw):
    """
    Enqueue a test script update job with keyword arguments specified in **kw
    """
    queue = rq.Queue(config.SERVICE_QUEUE, connection=ats.redis_connection())
    check_args(ats.update_test_scripts, **kw)
    queue.enqueue_call(ats.update_test_scripts, kwargs=kw)

def cancel_test(markus_address, run_ids, **kw):
    """
    Cancel a test run job with the job_id defined using 
    markus_address and run_id. 
    """
    with rq.Connection(ats.redis_connection()):
        for run_id in run_ids:
            job_id = job_id(markus_address, run_id)
            rq.cancel_job(job_id)

COMMANDS = {'run'       : run_test,
            'scripts'   : update_scripts,
            'cancel'    : cancel_test}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('command', choices=COMMANDS)
    parser.add_argument('json', type=json.loads)

    args = parser.parse_args()

    COMMANDS[args.command](**args.json)