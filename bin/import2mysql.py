"""
Table schema

create table if not exists metrics (
    node_id varchar(32) not null,
    website varchar(256) not null,
    reason smallint not null,
    start_time datetime not null,
    end_time datetime not null,
    duration double not null,
    http_code smallint not null,

    end_time_1min datetime not null,
    end_time_5min datetime not null,
    failure tinyint not null

) ENGINE=InnoDB DEFAULT CHARSET=utf8;
"""

import argparse
import getpass
import textwrap

import MySQLdb

import webhealth
from webhealth.model import Metric
from webhealth.util import datetime_to_mysql_date


INSERT_BATCH_LIMIT = 100


class MetricDAO(object):
    def __init__(self, db, user, password):
        self._db = MySQLdb.connect(host='localhost',
                                   user=user,
                                   passwd=password,
                                   db=db)
        self._buffer_to_insert = []

    def add(self, metric):
        self._buffer_to_insert.append(metric)

        if len(self._buffer_to_insert) >= INSERT_BATCH_LIMIT:
            self.flush_buffer()

    def _metric_to_mysql_tuple(self, m):
        return (m.node_id,
                m.website,
                m.state,
                datetime_to_mysql_date(m.start),
                datetime_to_mysql_date(m.end),
                (m.end - m.start).total_seconds(),  # duration in seconds
                0 if m.http_code is None else m.http_code,
                # normalized data
                datetime_to_mysql_date(m.end_1min),
                datetime_to_mysql_date(m.end_5min),
                0 if m.state == Metric.STATE_OK else 1
                )

    def flush_buffer(self):
        if self._buffer_to_insert:
            c = self._db.cursor()
            c.executemany(textwrap.dedent('''insert into metrics (node_id, website, reason, start_time, end_time, duration, http_code,
                                             end_time_1min, end_time_5min, failure)
                                             values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''),
                          [self._metric_to_mysql_tuple(m) for m in self._buffer_to_insert])
            self._db.commit()

            self._buffer_to_insert = []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--filename', dest='filename', required=True)
    parser.add_argument('--user', dest='user', required=True)
    parser.add_argument('--db-name', dest='db_name', required=True)
    args = parser.parse_args()

    metric_dao = MetricDAO(args.db_name,
                           args.user,
                           getpass.getpass())

    with open(args.filename) as f:
        for l in f.readlines():
            metric = webhealth.model.Metric.from_json(l)
            metric_dao.add(metric)

    metric_dao.flush_buffer()


if __name__ == '__main__':
    main()