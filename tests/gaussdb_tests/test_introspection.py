from io import StringIO

from django.core.management import call_command

from . import GaussDBTestCase


class InspectDBTests(GaussDBTestCase):
    def assertFieldsInModel(self, model, field_outputs):
        out = StringIO()
        call_command(
            "inspectdb",
            table_name_filter=lambda tn: tn.startswith(model),
            stdout=out,
        )
        output = out.getvalue()
        for field_output in field_outputs:
            self.assertIn(field_output, output)

    def test_range_fields(self):
        self.assertFieldsInModel(
            "gaussdb_tests_rangesmodel",
            [
                "ints = django.contrib.gaussdb.fields.IntegerRangeField(blank=True, "
                "null=True)",
                "bigints = django.contrib.gaussdb.fields.BigIntegerRangeField("
                "blank=True, null=True)",
                "decimals = django.contrib.gaussdb.fields.DecimalRangeField("
                "blank=True, null=True)",
                "timestamps = django.contrib.gaussdb.fields.DateTimeRangeField("
                "blank=True, null=True)",
                "dates = django.contrib.gaussdb.fields.DateRangeField(blank=True, "
                "null=True)",
            ],
        )
