import unittest

from django.core.management.color import no_style
from django.db import connection
from django.test import SimpleTestCase

from ..models import Person, Tag


@unittest.skipUnless(connection.vendor == "gaussdb", "GaussDB tests.")
class GaussDBOperationsTests(SimpleTestCase):
    # django.test.testcases.DatabaseOperationForbidden: Database queries to 'default'
    # are not allowed in SimpleTestCase subclasses. Either subclass TestCase or
    # TransactionTestCase to ensure proper test isolation or add 'default' to
    # backends.gaussdb.test_operations.GaussDBOperationsTests.databases to
    # silence this failure.
    databases = {'default'}
    def test_sql_flush(self):
        self.assertEqual(
            connection.ops.sql_flush(
                no_style(),
                [Person._meta.db_table, Tag._meta.db_table],
            ),
            ['TRUNCATE "backends_person", "backends_tag";'],
        )

    def test_sql_flush_allow_cascade(self):
        self.assertEqual(
            connection.ops.sql_flush(
                no_style(),
                [Person._meta.db_table, Tag._meta.db_table],
                allow_cascade=True,
            ),
            ['TRUNCATE "backends_person", "backends_tag" CASCADE;'],
        )

    def test_sql_flush_sequences(self):
        self.assertEqual(
            connection.ops.sql_flush(
                no_style(),
                [Person._meta.db_table, Tag._meta.db_table],
                reset_sequences=True,
            ),
            ['TRUNCATE "backends_person", "backends_tag";',
             'SELECT setval(pg_get_serial_sequence(\'"backends_person"\',\'id\'), '
             '1, false);',
             'SELECT setval(pg_get_serial_sequence(\'"backends_tag"\',\'id\'), '
             '1, false);'],
        )

    def test_sql_flush_sequences_allow_cascade(self):
        self.assertEqual(
            connection.ops.sql_flush(
                no_style(),
                [Person._meta.db_table, Tag._meta.db_table],
                reset_sequences=True,
                allow_cascade=True,
            ),
            ['TRUNCATE "backends_person", "backends_tag" CASCADE;',
             'SELECT setval(pg_get_serial_sequence(\'"backends_person"\',\'id\'), '
             '1, false);',
             'SELECT setval(pg_get_serial_sequence(\'"backends_tag"\',\'id\'), '
             '1, false);'],
        )
