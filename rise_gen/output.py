from prettytable import PrettyTable

def format_results(results):
    """Pretty print a set of test results

    Args:
    results (dict[]): An array of results. Most results have a 'level' key.

    Yields:
        str: String representation of the results
    """
    headers = sorted(results[0].keys())

    if 'level' in headers:
        # move 'level' to the front
        headers.pop(headers.index('level'))
        headers.insert(0, 'level')
    if 'avg rounds' in headers:
        # move 'avg rounds' to the back
        headers.pop(headers.index('avg rounds'))
        headers.append('avg rounds')
    table = PrettyTable(headers)
    for result in results:
        row = []
        for header in headers:
            row.append(result[header])
        table.add_row(row)
    return str(table)
