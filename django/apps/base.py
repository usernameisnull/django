from importlib import import_module

from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import module_has_submodule
from django.utils._os import upath


MODELS_MODULE_NAME = 'models'


class AppConfig(object):
    """
    Class representing a Django application and its configuration.
    """

    def __init__(self, app_name, app_module):
        # Full Python path to the application eg. 'django.contrib.admin'.
        self.name = app_name

        # Root module for the application eg. <module 'django.contrib.admin'
        # from 'django/contrib/admin/__init__.pyc'>.
        self.module = app_module

        # The following attributes could be defined at the class level in a
        # subclass, hence the test-and-set pattern.

        # Last component of the Python path to the application eg. 'admin'.
        # This value must be unique across a Django project.
        if not hasattr(self, 'label'):
            self.label = app_name.rpartition(".")[2]

        # Human-readable name for the application eg. "Admin".
        if not hasattr(self, 'verbose_name'):
            self.verbose_name = self.label.title()

        # Filesystem path to the application directory eg.
        # u'/usr/lib/python2.7/dist-packages/django/contrib/admin'. May be
        # None if the application isn't a bona fide package eg. if it's an
        # egg. Otherwise it's a unicode on Python 2 and a str on Python 3.
        if not hasattr(self, 'path'):
            try:
                self.path = upath(app_module.__path__[0])
            except AttributeError:
                self.path = None

        # Module containing models eg. <module 'django.contrib.admin.models'
        # from 'django/contrib/admin/models.pyc'>. Set by import_models().
        # None if the application doesn't have a models module.
        self.models_module = None

        # Mapping of lower case model names to model classes. Initally set to
        # None to prevent accidental access before import_models() runs.
        self.models = None

    def __repr__(self):
        return '<AppConfig: %s>' % self.label

    @classmethod
    def create(cls, entry):
        """
        Factory that creates an app config from an entry in INSTALLED_APPS.
        """
        try:
            # If import_module succeeds, entry is a path to an app module.
            # Otherwise, entry is a path to an app config class or an error.
            module = import_module(entry)

        except ImportError:
            # Avoid django.utils.module_loading.import_by_path because it
            # masks errors -- it reraises ImportError as ImproperlyConfigured.
            mod_path, _, cls_name = entry.rpartition('.')

            # Raise the original exception when entry cannot be a path to an
            # app config class.
            if not mod_path:
                raise

            mod = import_module(mod_path)
            try:
                cls = getattr(mod, cls_name)
            except AttributeError:
                # Emulate the error that "from <mod_path> import <cls_name>"
                # would raise when <mod_path> exists but not <cls_name>, with
                # more context (Python just says "cannot import name ...").
                raise ImportError(
                    "cannot import name '%s' from '%s'" % (cls_name, mod_path))

            # Check for obvious errors. (This check prevents duck typing, but
            # it could be removed if it became a problem in practice.)
            if not issubclass(cls, AppConfig):
                raise ImproperlyConfigured(
                    "'%s' isn't a subclass of AppConfig." % entry)

            # Obtain app name here rather than in AppClass.__init__ to keep
            # all error checking for entries in INSTALLED_APPS in one place.
            try:
                app_name = cls.name
            except AttributeError:
                raise ImproperlyConfigured(
                    "'%s' must supply a name attribute." % entry)

            # Ensure app_names points to a valid module.
            app_module = import_module(app_name)

            # Entry is a path to an app config class.
            return cls(app_name, app_module)

        else:
            # Entry is a path to an app module.
            return cls(entry, module)

    def import_models(self, all_models):
        # Dictionary of models for this app, primarily maintained in the
        # 'all_models' attribute of the Apps this AppConfig is attached to.
        # Injected as a parameter because it gets populated when models are
        # imported, which may happen before populate_models() runs.
        self.models = all_models

        if module_has_submodule(self.module, MODELS_MODULE_NAME):
            models_module_name = '%s.%s' % (self.name, MODELS_MODULE_NAME)
            self.models_module = import_module(models_module_name)
