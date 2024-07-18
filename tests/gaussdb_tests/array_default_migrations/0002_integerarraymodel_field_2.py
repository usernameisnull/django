import django.contrib.gaussdb.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("gaussdb_tests", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="integerarraydefaultmodel",
            name="field_2",
            field=django.contrib.gaussdb.fields.ArrayField(
                models.IntegerField(), default=[], size=None
            ),
            preserve_default=False,
        ),
    ]
