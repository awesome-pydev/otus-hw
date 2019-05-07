#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';
import argparse
import json
import logging
import os
import gzip
import sys
from datetime import datetime as dt
from statistics import median
from collections import defaultdict


default_config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOGGING": None,
    "LOG_DIR": "./log",
    "ERROR_LIMIT": 0.2
}


def find_latest_log(name, path):
    latest_log_date = ''
    latest_log_file = ''
    for root, dirs, files in os.walk(path):
        print(files)
        for file in files:
            if name in file:
                date_in_filename = file.split('-')[-1] if not 'gz' in file else file.split('-')[-1].split('.')[0]
                current_log_data = dt.strptime(date_in_filename, "%Y%m%d")
                if not latest_log_date:
                    latest_log_date = current_log_data
                else:
                    if current_log_data > latest_log_date:
                        latest_log_date = current_log_data
                        latest_log_file = file

    if latest_log_date:
        return latest_log_file
    else:
        raise Exception('No logs found')


def parse_log(log_path, error_limit):
    opener = gzip.open(log_path, "r", encoding="UTF-8", ) if log_path.endswith(".gz") \
        else open(log_path, "r", encoding="UTF-8")

    with opener:
        all_lines = broken_lines = 0
        for line in opener:
            all_lines += 1
            try:
                url = line.split('"')[1].split(' ')[1]
                req_time = float(line.split(' ')[-1])
                yield url, req_time
            except:
                broken_lines += 1

        if (broken_lines / all_lines) > error_limit:
            logging.error("Error limit exceed")
            sys.exit(-1)


def statistics_count(parsed_log):
    total_count = total_sum = 0
    urls_statistics = defaultdict(list)
    for url, req_time in parsed_log:
        urls_statistics[url].append(req_time)
        total_count += 1
        total_sum += float(req_time)
    report = []
    for urs, request_times in urls_statistics.items():
        count = len(request_times)
        count_perc = count / total_count
        time_sum = sum(request_times)
        time_perc = time_sum / total_sum
        time_avg = time_sum / count
        time_max = max(request_times)
        time_med = median([float(x) for x in request_times])
        sample = {"count": count,
                  "time_avg": round(time_avg, 3),
                  "time_max": round(time_max, 3),
                  "time_sum": round(time_sum, 3),
                  "url": urs,
                  "time_med": round(time_med, 3),
                  "time_perc": round(time_perc, 3),
                  "count_perc": round(count_perc, 3)
                  }
        report.append(sample)

    return report


def parse_config(config, path):
    with open(path) as f:
        config_from_file = json.load(f)

    for k in config.keys():
        if k in config_from_file:
            config[k] = config_from_file[k]

    return config


def generate_html_report(report, report_dir, last_report_name):
    try:
        # open temporary html file and copy his content
        with open('report.html', 'r', encoding='utf-8') as html_template:
            html_data = html_template.read()
    except:
        logging.error("Report template not found")
        raise
    try:
        # replace '$table_json' placeholder by the data from filtered_report variable
        newdata = html_data.replace('$table_json', str(report))

        # create temporary html file and inject report data
        with open(os.path.join(report_dir, str('temp_') + last_report_name), 'w', encoding='utf-8') as html_report:
            html_report.write(newdata)

        # if all was ok, remove temp_ mask from report's filename
        os.rename(os.path.join(report_dir, str('temp_') + last_report_name),
                  os.path.join(report_dir, last_report_name))

        logging.info("New report has been generated")
    except:
        logging.error("An error occurred while creating the html-report")
        raise


def main(config):
    latest_log_path = find_latest_log('nginx-access-ui', config['LOG_DIR'])
    last_report_name = 'report_' + str(12345) + '.html' # TODO 111

    print(latest_log_path)
    parsed_log = parse_log(config["LOG_DIR"] + '/' + latest_log_path, config['ERROR_LIMIT'])
    report = statistics_count(parsed_log)

    logging.info("Reports' data has been generated")
    generate_html_report(report, config['REPORT_DIR'], last_report_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='Path to config')
    args = parser.parse_args()
    config_path = args.config

    final_config = parse_config(default_config, config_path) if config_path else default_config

    logging.basicConfig(filename=final_config['LOGGING'],
                        level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S')

    try:
        main(final_config)
    except Exception:
        logging.exception("Unexpected error occurred")
        raise
