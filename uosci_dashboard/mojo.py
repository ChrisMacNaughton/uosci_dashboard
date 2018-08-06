from uosci_dashboard.uosci_jenkins import (
    fetch_matrix_results
)


def execute(config, env):
    print("# Gathering results from the last Mojo runs")
    results = fetch_matrix_results(
        host=config['host'],
        username=config['username'],
        password=config['password'],
        matrix='MojoMatrix',
        filter=None)
    template = env.get_template('mojo.html')

    rates = {}
    debug = False
    for name, jobs in results.items():
        if debug:
            import code; code.interact(local=dict(globals(), **locals()))
            debug = False
        for uos in env.globals['uos_combos']:
            job = jobs.get(uos)
            if job is None:
                continue
            if rates.get(uos) is None:
                rates[uos] = {'success': 0, 'total': 0}
            if job['successful']:
                rates[uos]['success'] += 1
            rates[uos]['total'] += 1
    success_runs = {}
    for uos in env.globals['uos_combos']:
        success_runs[uos] = round(rates[uos]['success'] / rates[uos]['total'] * 100, 2)


    return [(template, {'jobs': results, 'uos_rates': success_runs })]
