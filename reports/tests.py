from datetime import date
from types import SimpleNamespace

from django.test import SimpleTestCase
from django.test.utils import override_settings

from .services import parse_date, get_period


class ReportsDateTests(SimpleTestCase):

    def test_valid_date(self):
        self.assertEqual(
            parse_date("2026-11-02"),
            date(2026, 11, 2),
        )

    def test_invalid_date(self):
        self.assertIsNone(
            parse_date("not-a-date")
        )

    def test_all_time_has_no_date_bounds(self):
        request = SimpleNamespace(
            GET={"period": "all"}
        )

        period = get_period(request)

        self.assertIsNone(period["start"])
        self.assertIsNone(period["end"])

    def test_date_range_swaps_reversed_dates(self):
        request = SimpleNamespace(
            GET={
                "period": "range",
                "start_date": "2026-11-02",
                "end_date": "2026-11-01",
            }
        )

        period = get_period(request)

        self.assertEqual(
            period["start"],
            date(2026, 11, 1),
        )

        self.assertEqual(
            period["end"],
            date(2026, 11, 2),
        )