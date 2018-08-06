from datetime import datetime, timedelta, timezone

import jenkins as jenkins
from uosci_dashboard import dashboard


class Jenkins(jenkins.Jenkins):
    def matrix(self, view_name):
        views = self.get_jobs(view_name=view_name)
        return views

    def job_result(self, job):
        """
        Fetches the latest job results from Jenkins for the
        configured job
        """
        job_info = self.get_job_info(job['name'])  #, depth=1)
        if job_info is None or job_info['lastBuild'] is None:
            return {}

        build_info = self.get_build_info(
            job['name'],
            job_info['lastBuild']['number'],
            depth=1)
        # build_info = job_info['lastBuild']
        # runtimes =
        try:
            prev_run = self.get_build_info(
                job['name'],
                job_info['builds'][1]['number'],
                depth=0)
            duration = prev_run['duration']
        except IndexError:
            duration = 0
        # debug = True
        debug = False
        if debug:
            import code; code.interact(local=dict(globals(), **locals()))
            debug = False
        results = {}
        results['pass'] = True
        # results['duration'] = {'last': duration, 'this': build_info['duration']}
        last_duration = timedelta(milliseconds=duration)
        this_duration = timedelta(milliseconds=build_info['duration'])
        results['duration'] = str(this_duration).split('.', 2)[0]
        results['duration_diff'] = str(this_duration - last_duration).split('.', 2)[0]
        # print("[{}] - About to subtract last_duration ({} / {}) from this_duration ({} / {}) -> {}".format(job['name'], duration, last_duration, build_info['duration'], this_duration, results['duration']))


        successful, total = 0.0, 0
        for run in build_info['runs']:
            if run['number'] != job_info['lastBuild']['number']:
                continue
            series = get_series_from_url(run['url'])
            if series not in dashboard.UOS_COMBOS:
                continue
            details = result_from_run(run)
            if details is not None:
                total += 1
                results[series] = details
                if details['successful']:
                    successful += 1
                else:
                    if results['pass']:
                        results['pass'] = False
        if total != 0:
            results['rate'] = round(successful / total * 100, 2)
        else:
            results['rate'] = 0.0
        return results


def result_from_run(run):
    """
    Summarizes a run from Jenkins API

    :param run: Details of the run from Jenkins
    :type dict
    :returns Summary of the run
    :rtype dict
    """
    date = datetime.fromtimestamp(run['timestamp'] / 1000, tz=timezone.utc)
    thirty_days_ago = datetime.now(tz=timezone.utc) - timedelta(days=30)
    if date < thirty_days_ago:
        return
    name_split = run['fullDisplayName'].split(' ')
    success = run['result'] == "SUCCESS"
    if success:
        state = 'Pass'
    else:
        state = 'Fail'
    return {
        'successful': success,
        'state': state,
        'url': run['url'],
        'date': date,
        'name': name_split[0],
        'spec': name_split[-2].split(',')[0],
        'duration': str(timedelta(milliseconds=run['duration'])).split('.', 2)[0],
        'builtOn': run['builtOn'],
        'run': run,
    }


def get_series_from_url(url):
    """
    Breaks a Jenkins job URL out to retrieve U_OS combination


    :param url: Jenkins job URL
    :type str
    :returns: Ubuntu/OpenStack combination
    :rtype: Option(str)
    """
    if 'U_OS' in url:
        return url.split('U_OS=')[-1].split('/')[0]


def get_job_from_specs(name, specs={}):
    if name is '' or name is 'Spec/Bundle/Test':
        return None
    return specs.get(name)


def get_spec_summary(results):
    specs = {}
    for name, spec_list in results.items():
        for uos, job in spec_list.items():
            specs[job['spec']] = name
    return specs


def fetch_matrix_results(host,
                  username,
                  password,
                  matrix,
                  filter=None):
    client = Jenkins(
        host, username=username, password=password)
    jobs = client.matrix(matrix)
    results = {}
    for job in jobs:
        if job['color'] == 'disabled':
            continue
        if filter_job(job['name'], filter):
            continue
        runs = client.job_result(job)
        if len(runs.keys() - ['pass', 'duration', 'duration_diff', 'rate']) > 0:
            results[job['name'].replace('test_mojo_', '')] = runs
    return results


def filter_job(job_name, filter=None):
    if 'test'not in job_name:
        return True
    if filter is not None and filter not in job_name:
        return True
    return False