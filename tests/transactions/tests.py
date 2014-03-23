from __future__ import unicode_literals

import sys
try:
    import threading
except ImportError:
    threading = None
import time
from unittest import skipIf, skipUnless

from django.db import (connection, transaction,
    DatabaseError, IntegrityError, OperationalError)
from django.test import TransactionTestCase, skipIfDBFeature
from django.utils import six

from .models import Reporter


@skipUnless(connection.features.uses_savepoints,
        "'atomic' requires transactions and savepoints.")
class AtomicTests(TransactionTestCase):
    """
    Tests for the atomic decorator and context manager.

    The tests make assertions on internal attributes because there isn't a
    robust way to ask the database for its current transaction state.

    Since the decorator syntax is converted into a context manager (see the
    implementation), there are only a few basic tests with the decorator
    syntax and the bulk of the tests use the context manager syntax.
    """

    available_apps = ['transactions']

    def test_decorator_syntax_commit(self):
        @transaction.atomic
        def make_reporter():
            Reporter.objects.create(first_name="Tintin")
        make_reporter()
        self.assertQuerysetEqual(Reporter.objects.all(), ['<Reporter: Tintin>'])

    def test_decorator_syntax_rollback(self):
        @transaction.atomic
        def make_reporter():
            Reporter.objects.create(first_name="Haddock")
            raise Exception("Oops, that's his last name")
        with six.assertRaisesRegex(self, Exception, "Oops"):
            make_reporter()
        self.assertQuerysetEqual(Reporter.objects.all(), [])

    def test_alternate_decorator_syntax_commit(self):
        @transaction.atomic()
        def make_reporter():
            Reporter.objects.create(first_name="Tintin")
        make_reporter()
        self.assertQuerysetEqual(Reporter.objects.all(), ['<Reporter: Tintin>'])

    def test_alternate_decorator_syntax_rollback(self):
        @transaction.atomic()
        def make_reporter():
            Reporter.objects.create(first_name="Haddock")
            raise Exception("Oops, that's his last name")
        with six.assertRaisesRegex(self, Exception, "Oops"):
            make_reporter()
        self.assertQuerysetEqual(Reporter.objects.all(), [])

    def test_commit(self):
        with transaction.atomic():
            Reporter.objects.create(first_name="Tintin")
        self.assertQuerysetEqual(Reporter.objects.all(), ['<Reporter: Tintin>'])

    def test_rollback(self):
        with six.assertRaisesRegex(self, Exception, "Oops"):
            with transaction.atomic():
                Reporter.objects.create(first_name="Haddock")
                raise Exception("Oops, that's his last name")
        self.assertQuerysetEqual(Reporter.objects.all(), [])

    def test_nested_commit_commit(self):
        with transaction.atomic():
            Reporter.objects.create(first_name="Tintin")
            with transaction.atomic():
                Reporter.objects.create(first_name="Archibald", last_name="Haddock")
        self.assertQuerysetEqual(Reporter.objects.all(),
                ['<Reporter: Archibald Haddock>', '<Reporter: Tintin>'])

    def test_nested_commit_rollback(self):
        with transaction.atomic():
            Reporter.objects.create(first_name="Tintin")
            with six.assertRaisesRegex(self, Exception, "Oops"):
                with transaction.atomic():
                    Reporter.objects.create(first_name="Haddock")
                    raise Exception("Oops, that's his last name")
        self.assertQuerysetEqual(Reporter.objects.all(), ['<Reporter: Tintin>'])

    def test_nested_rollback_commit(self):
        with six.assertRaisesRegex(self, Exception, "Oops"):
            with transaction.atomic():
                Reporter.objects.create(last_name="Tintin")
                with transaction.atomic():
                    Reporter.objects.create(last_name="Haddock")
                raise Exception("Oops, that's his first name")
        self.assertQuerysetEqual(Reporter.objects.all(), [])

    def test_nested_rollback_rollback(self):
        with six.assertRaisesRegex(self, Exception, "Oops"):
            with transaction.atomic():
                Reporter.objects.create(last_name="Tintin")
                with six.assertRaisesRegex(self, Exception, "Oops"):
                    with transaction.atomic():
                        Reporter.objects.create(first_name="Haddock")
                    raise Exception("Oops, that's his last name")
                raise Exception("Oops, that's his first name")
        self.assertQuerysetEqual(Reporter.objects.all(), [])

    def test_merged_commit_commit(self):
        with transaction.atomic():
            Reporter.objects.create(first_name="Tintin")
            with transaction.atomic(savepoint=False):
                Reporter.objects.create(first_name="Archibald", last_name="Haddock")
        self.assertQuerysetEqual(Reporter.objects.all(),
                ['<Reporter: Archibald Haddock>', '<Reporter: Tintin>'])

    def test_merged_commit_rollback(self):
        with transaction.atomic():
            Reporter.objects.create(first_name="Tintin")
            with six.assertRaisesRegex(self, Exception, "Oops"):
                with transaction.atomic(savepoint=False):
                    Reporter.objects.create(first_name="Haddock")
                    raise Exception("Oops, that's his last name")
        # Writes in the outer block are rolled back too.
        self.assertQuerysetEqual(Reporter.objects.all(), [])

    def test_merged_rollback_commit(self):
        with six.assertRaisesRegex(self, Exception, "Oops"):
            with transaction.atomic():
                Reporter.objects.create(last_name="Tintin")
                with transaction.atomic(savepoint=False):
                    Reporter.objects.create(last_name="Haddock")
                raise Exception("Oops, that's his first name")
        self.assertQuerysetEqual(Reporter.objects.all(), [])

    def test_merged_rollback_rollback(self):
        with six.assertRaisesRegex(self, Exception, "Oops"):
            with transaction.atomic():
                Reporter.objects.create(last_name="Tintin")
                with six.assertRaisesRegex(self, Exception, "Oops"):
                    with transaction.atomic(savepoint=False):
                        Reporter.objects.create(first_name="Haddock")
                    raise Exception("Oops, that's his last name")
                raise Exception("Oops, that's his first name")
        self.assertQuerysetEqual(Reporter.objects.all(), [])

    def test_reuse_commit_commit(self):
        atomic = transaction.atomic()
        with atomic:
            Reporter.objects.create(first_name="Tintin")
            with atomic:
                Reporter.objects.create(first_name="Archibald", last_name="Haddock")
        self.assertQuerysetEqual(Reporter.objects.all(),
                ['<Reporter: Archibald Haddock>', '<Reporter: Tintin>'])

    def test_reuse_commit_rollback(self):
        atomic = transaction.atomic()
        with atomic:
            Reporter.objects.create(first_name="Tintin")
            with six.assertRaisesRegex(self, Exception, "Oops"):
                with atomic:
                    Reporter.objects.create(first_name="Haddock")
                    raise Exception("Oops, that's his last name")
        self.assertQuerysetEqual(Reporter.objects.all(), ['<Reporter: Tintin>'])

    def test_reuse_rollback_commit(self):
        atomic = transaction.atomic()
        with six.assertRaisesRegex(self, Exception, "Oops"):
            with atomic:
                Reporter.objects.create(last_name="Tintin")
                with atomic:
                    Reporter.objects.create(last_name="Haddock")
                raise Exception("Oops, that's his first name")
        self.assertQuerysetEqual(Reporter.objects.all(), [])

    def test_reuse_rollback_rollback(self):
        atomic = transaction.atomic()
        with six.assertRaisesRegex(self, Exception, "Oops"):
            with atomic:
                Reporter.objects.create(last_name="Tintin")
                with six.assertRaisesRegex(self, Exception, "Oops"):
                    with atomic:
                        Reporter.objects.create(first_name="Haddock")
                    raise Exception("Oops, that's his last name")
                raise Exception("Oops, that's his first name")
        self.assertQuerysetEqual(Reporter.objects.all(), [])

    def test_force_rollback(self):
        with transaction.atomic():
            Reporter.objects.create(first_name="Tintin")
            # atomic block shouldn't rollback, but force it.
            self.assertFalse(transaction.get_rollback())
            transaction.set_rollback(True)
        self.assertQuerysetEqual(Reporter.objects.all(), [])

    def test_prevent_rollback(self):
        with transaction.atomic():
            Reporter.objects.create(first_name="Tintin")
            sid = transaction.savepoint()
            # trigger a database error inside an inner atomic without savepoint
            with self.assertRaises(DatabaseError):
                with transaction.atomic(savepoint=False):
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT no_such_col FROM transactions_reporter")
            # prevent atomic from rolling back since we're recovering manually
            self.assertTrue(transaction.get_rollback())
            transaction.set_rollback(False)
            transaction.savepoint_rollback(sid)
        self.assertQuerysetEqual(Reporter.objects.all(), ['<Reporter: Tintin>'])


class AtomicInsideTransactionTests(AtomicTests):
    """All basic tests for atomic should also pass within an existing transaction."""

    def setUp(self):
        self.atomic = transaction.atomic()
        self.atomic.__enter__()

    def tearDown(self):
        self.atomic.__exit__(*sys.exc_info())


@skipIf(connection.features.autocommits_when_autocommit_is_off,
        "This test requires a non-autocommit mode that doesn't autocommit.")
class AtomicWithoutAutocommitTests(AtomicTests):
    """All basic tests for atomic should also pass when autocommit is turned off."""

    def setUp(self):
        transaction.set_autocommit(False)

    def tearDown(self):
        # The tests access the database after exercising 'atomic', initiating
        # a transaction ; a rollback is required before restoring autocommit.
        transaction.rollback()
        transaction.set_autocommit(True)


@skipUnless(connection.features.uses_savepoints,
        "'atomic' requires transactions and savepoints.")
class AtomicMergeTests(TransactionTestCase):
    """Test merging transactions with savepoint=False."""

    available_apps = ['transactions']

    def test_merged_outer_rollback(self):
        with transaction.atomic():
            Reporter.objects.create(first_name="Tintin")
            with transaction.atomic(savepoint=False):
                Reporter.objects.create(first_name="Archibald", last_name="Haddock")
                with six.assertRaisesRegex(self, Exception, "Oops"):
                    with transaction.atomic(savepoint=False):
                        Reporter.objects.create(first_name="Calculus")
                        raise Exception("Oops, that's his last name")
                # The third insert couldn't be roll back. Temporarily mark the
                # connection as not needing rollback to check it.
                self.assertTrue(transaction.get_rollback())
                transaction.set_rollback(False)
                self.assertEqual(Reporter.objects.count(), 3)
                transaction.set_rollback(True)
            # The second insert couldn't be roll back. Temporarily mark the
            # connection as not needing rollback to check it.
            self.assertTrue(transaction.get_rollback())
            transaction.set_rollback(False)
            self.assertEqual(Reporter.objects.count(), 3)
            transaction.set_rollback(True)
        # The first block has a savepoint and must roll back.
        self.assertQuerysetEqual(Reporter.objects.all(), [])

    def test_merged_inner_savepoint_rollback(self):
        with transaction.atomic():
            Reporter.objects.create(first_name="Tintin")
            with transaction.atomic():
                Reporter.objects.create(first_name="Archibald", last_name="Haddock")
                with six.assertRaisesRegex(self, Exception, "Oops"):
                    with transaction.atomic(savepoint=False):
                        Reporter.objects.create(first_name="Calculus")
                        raise Exception("Oops, that's his last name")
                # The third insert couldn't be roll back. Temporarily mark the
                # connection as not needing rollback to check it.
                self.assertTrue(transaction.get_rollback())
                transaction.set_rollback(False)
                self.assertEqual(Reporter.objects.count(), 3)
                transaction.set_rollback(True)
            # The second block has a savepoint and must roll back.
            self.assertEqual(Reporter.objects.count(), 1)
        self.assertQuerysetEqual(Reporter.objects.all(), ['<Reporter: Tintin>'])


@skipUnless(connection.features.uses_savepoints,
        "'atomic' requires transactions and savepoints.")
class AtomicErrorsTests(TransactionTestCase):

    available_apps = ['transactions']

    def test_atomic_prevents_setting_autocommit(self):
        autocommit = transaction.get_autocommit()
        with transaction.atomic():
            with self.assertRaises(transaction.TransactionManagementError):
                transaction.set_autocommit(not autocommit)
        # Make sure autocommit wasn't changed.
        self.assertEqual(connection.autocommit, autocommit)

    def test_atomic_prevents_calling_transaction_methods(self):
        with transaction.atomic():
            with self.assertRaises(transaction.TransactionManagementError):
                transaction.commit()
            with self.assertRaises(transaction.TransactionManagementError):
                transaction.rollback()

    def test_atomic_prevents_queries_in_broken_transaction(self):
        r1 = Reporter.objects.create(first_name="Archibald", last_name="Haddock")
        with transaction.atomic():
            r2 = Reporter(first_name="Cuthbert", last_name="Calculus", id=r1.id)
            with self.assertRaises(IntegrityError):
                r2.save(force_insert=True)
            # The transaction is marked as needing rollback.
            with self.assertRaises(transaction.TransactionManagementError):
                r2.save(force_update=True)
        self.assertEqual(Reporter.objects.get(pk=r1.pk).last_name, "Haddock")

    @skipIfDBFeature('atomic_transactions')
    def test_atomic_allows_queries_after_fixing_transaction(self):
        r1 = Reporter.objects.create(first_name="Archibald", last_name="Haddock")
        with transaction.atomic():
            r2 = Reporter(first_name="Cuthbert", last_name="Calculus", id=r1.id)
            with self.assertRaises(IntegrityError):
                r2.save(force_insert=True)
            # Mark the transaction as no longer needing rollback.
            transaction.set_rollback(False)
            r2.save(force_update=True)
        self.assertEqual(Reporter.objects.get(pk=r1.pk).last_name, "Calculus")


@skipUnless(connection.vendor == 'mysql', "MySQL-specific behaviors")
class AtomicMySQLTests(TransactionTestCase):

    available_apps = ['transactions']

    @skipIf(threading is None, "Test requires threading")
    def test_implicit_savepoint_rollback(self):
        """MySQL implicitly rolls back savepoints when it deadlocks (#22291)."""

        other_thread_ready = threading.Event()

        def other_thread():
            try:
                with transaction.atomic():
                    Reporter.objects.create(id=1, first_name="Tintin")
                    other_thread_ready.set()
                    # We cannot synchronize the two threads with an event here
                    # because the main thread locks. Sleep for a little while.
                    time.sleep(1)
                    # 2) ... and this line deadlocks. (see below for 1)
                    Reporter.objects.exclude(id=1).update(id=2)
            finally:
                # This is the thread-local connection, not the main connection.
                connection.close()

        other_thread = threading.Thread(target=other_thread)
        other_thread.start()
        other_thread_ready.wait()

        with six.assertRaisesRegex(self, OperationalError, 'Deadlock found'):
            # Double atomic to enter a transaction and create a savepoint.
            with transaction.atomic():
                with transaction.atomic():
                    # 1) This line locks... (see above for 2)
                    Reporter.objects.create(id=1, first_name="Tintin")

        other_thread.join()


class AtomicMiscTests(TransactionTestCase):

    available_apps = []

    def test_wrap_callable_instance(self):
        # Regression test for #20028
        class Callable(object):
            def __call__(self):
                pass
        # Must not raise an exception
        transaction.atomic(Callable())
