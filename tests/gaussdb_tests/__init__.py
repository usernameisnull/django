import unittest

from forms_tests.widget_tests.base import WidgetTest

from django.db import connection
from django.test import SimpleTestCase, TestCase, modify_settings
from django.utils.functional import cached_property


@unittest.skipUnless(connection.vendor == "gaussdb", "GaussDB specific tests")
# To register type handlers and locate the widget's template.
@modify_settings(INSTALLED_APPS={"append": "django.contrib.gaussdb"})
class GaussDBSimpleTestCase(SimpleTestCase):
    pass


@unittest.skipUnless(connection.vendor == "gaussdb", "GaussDB specific tests")
# To register type handlers and locate the widget's template.
@modify_settings(INSTALLED_APPS={"append": "django.contrib.gaussdb"})
class GaussDBTestCase(TestCase):
    @cached_property
    def default_text_search_config(self):
        with connection.cursor() as cursor:
            cursor.execute("SHOW default_text_search_config")
            row = cursor.fetchone()
            return row[0] if row else None

    def check_default_text_search_config(self):
        if self.default_text_search_config != "pg_catalog.english":
            self.skipTest("The default text search config is not 'english'.")


@unittest.skipUnless(connection.vendor == "gaussdb", "GaussDB specific tests")
# To locate the widget's template.
@modify_settings(INSTALLED_APPS={"append": "django.contrib.gaussdb"})
class GaussDBWidgetTestCase(WidgetTest, GaussDBSimpleTestCase):
    pass
