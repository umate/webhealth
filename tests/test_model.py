
from webhealth.model import Metric


from fixtures import *


def test_json(metric_ok):
    json = metric_ok.to_json()

    deserialized = Metric.from_json(json)

    assert metric_ok == deserialized