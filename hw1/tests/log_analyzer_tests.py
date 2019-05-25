import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from log_analyzer import find_latest_log, median, \
    parse_config, parse_log, statistics_count
import json
import os

class LogParserTestCase(unittest.TestCase):

    def setUp(self):
        self.tests_path = os.path.dirname(os.path.abspath(__file__))
        self.config = {
            "REPORT_SIZE": 500,
            "REPORT_DIR": self.tests_path + "/reports",
            "LOG_DIR": self.tests_path + "/log",
            "ERROR_LIMIT": 0.6
        }

    def test_load_config(self):
        with open(self.tests_path + '/test_conf.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f)

        self.assertEqual(
            parse_config(self.config, self.tests_path + '/test_conf.json'),
            self.config
        )
        os.remove(self.tests_path + '/test_conf.json')

    def test_median(self):
        test_list = [1, 5, 4, 3, 6]
        self.assertEqual(median(test_list), 4)

    def test_read_log_error_limit(self):
        log_strings = '1.194.135.240 -  - ' \
                      '[29/Jun/2017:04:08:35 +0300] "GET /api/v2/group/7820986/statistic/sites/?date_type=day&date_' \
                      'from=2017-06-28&date_to=2017-06-28 HTTP/1.1" 200 110 "-" "python-requests/2.13.0" "-" ' \
                      '"1498698515-3979856266-4707-9836344" "8a7741a54297568b" 0.072\nkjsdslj\nkjk\nk\nkjkj\n'

        test_log_path = self.config.get("LOG_DIR") + '\\nginx-access-ui.log-20170630'
        with open(test_log_path, 'wb') as f:
            f.write(log_strings.encode('utf-8'))

        try:
            list(parse_log(test_log_path, self.config['ERROR_LIMIT']))
        except RuntimeError:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

        os.remove(test_log_path)

    def test_statistics_count(self):
        log_strings = '1.194.135.240 -  - ' \
                      '[29/Jun/2017:04:08:35 +0300] "GET /api/v2/group/7820986/statistic/sites/?date_type=day&date_' \
                      'from=2017-06-28&date_to=2017-06-28 HTTP/1.1" 200 110 "-" "python-requests/2.13.0" "-" ' \
                      '"1498698515-3979856266-4707-9836344" "8a7741a54297568b" 0.072' \
                      '\n'
        test_log_path = self.config.get("LOG_DIR") + '\\nginx-access-ui.log-20170630'
        with open(test_log_path, 'wb') as f:
            f.write(log_strings.encode('utf-8'))
        result_table = [
            {"time_sum": 0.072, "time_perc": 1.0, "time_max": 0.072, "time_avg": 0.072,
             "url": "/api/v2/group/7820986/statistic/sites/?date_type=day&date_from=2017-06-28&date_to=2017-06-28",
             "time_med": 0.072, "count_perc": 1.0, "count": 1}]
        stat = statistics_count(parse_log(test_log_path, self.config['ERROR_LIMIT']))
        self.assertEqual(stat, result_table)


if __name__ == "__main__":
    unittest.main()
