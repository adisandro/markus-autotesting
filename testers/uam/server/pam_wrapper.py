import json
import os
import subprocess
import enum
import sys


class PAMResult:
    """
    A test result from pam.
    """

    class Status(enum.Enum):
        PASS = 1
        FAIL = 2
        ERROR = 3

    def __init__(self, class_name, name, status, description='', message=''):
        self.class_name = class_name
        self.name = name
        self.status = status
        self.description = description
        self.message = message


class PAMWrapper:
    """
    A base wrapper class to run the Python AutoMarker (pam - https://github.com/ProjectAT/uam).
    """

    def __init__(self, path_to_uam, test_files, test_timeout=5, global_timeout=20, path_to_virtualenv=None,
                 result_filename='result.json'):
        """
        Initializes the various parameters to run pam.
        :param path_to_uam: The path to the uam installation.
        :param test_files: A list of test files to be run by pam.
        :param test_timeout: The max time to run a single test on the student submission.
        :param global_timeout: The max time to run all tests on the student submission.
        :param path_to_virtualenv: The path to the virtualenv to be used to run pam, can be None if all necessary.
        :param result_filename: The file name of pam's json output.
        dependencies are installed system-wide.
        """
        self.path_to_uam = path_to_uam
        self.path_to_pam = path_to_uam + '/pam/pam.py'
        self.test_files = test_files
        self.test_timeout = test_timeout
        self.global_timeout = global_timeout
        self.path_to_virtualenv = path_to_virtualenv
        self.result_filename = result_filename

    def collect_results(self):
        """
        Collects pam results.
        :return: A list of results (possibly empty), or None if the tests timed out.
        """
        results = None
        try:
            with open(self.result_filename) as result_file:
                results = []
                result = json.load(result_file)
                for test_class_name, test_class_result in result['results'].items():
                    if 'passes' in test_class_result:
                        for test_name, test_desc in test_class_result['passes'].items():
                            results.append(
                                PAMResult(class_name=test_class_name.partition('.')[2], name=test_name,
                                          status=PAMResult.Status.PASS, description=test_desc))
                    if 'failures' in test_class_result:
                        for test_name, test_stack in test_class_result['failures'].items():
                            results.append(
                                PAMResult(class_name=test_class_name.partition('.')[2], name=test_name,
                                          status=PAMResult.Status.FAIL, description=test_stack['description'],
                                          message=test_stack['message']))
                    if 'errors' in test_class_result:
                        for test_name, test_stack in test_class_result['errors'].items():
                            results.append(
                                PAMResult(class_name=test_class_name.partition('.')[2], name=test_name,
                                          status=PAMResult.Status.ERROR, description=test_stack['description'],
                                          message=test_stack['message']))
        except OSError:
            print('Test framework error: no result generated', file=sys.stderr)
            exit(1)
        return results

    def print_results(self, results):
        """
        Prints pam results: must be overridden.
        :param results: A list of results (possibly empty), or None if the tests timed out.
        """
        pass

    def run(self):
        """
        Runs pam.
        """
        if self.path_to_virtualenv is None:
            shell_command = [self.path_to_pam, '-t', str(self.test_timeout), self.result_filename]
            shell_command.extend(self.test_files)
            shell = False
        else:
            shell_command = '''
                . {cmd.path_to_virtualenv}/bin/activate;
                {cmd.path_to_pam} -t {cmd.test_timeout} {cmd.result_filename} {files}
            '''.format(cmd=self, files=' '.join(self.test_files))
            shell = True
        try:
            env = os.environ.copy()  # need to add path to uam libs
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = "{systempath}:{pampath}".format(systempath=env['PYTHONPATH'],
                                                                    pampath=self.path_to_uam)
            else:
                env['PYTHONPATH'] = self.path_to_uam
            subprocess.run(shell_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, shell=shell,
                           env=env, timeout=self.global_timeout)
            # use the following with Python < 3.5
            # subprocess.check_call(shell_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=shell,
            #                       env=env, timeout=self.global_timeout)
            results = self.collect_results()
            self.print_results(results)
        except subprocess.TimeoutExpired:
            self.print_results(None)
            exit(1)
        except subprocess.CalledProcessError as e:
            print('Test framework error: stdout: {stdout}, stderr: {stderr}'.format(stdout=e.stdout, stderr=e.stderr),
                  file=sys.stderr)
            # use the following with Python < 3.5
            # print('Test framework error', file=sys.stderr)
            exit(1)
        except Exception as e:
            print('Test framework error: {exception}'.format(exception=e), file=sys.stderr)
            exit(1)
