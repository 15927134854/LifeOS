# Generated by Django 5.2 on 2025-05-19 04:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("goal", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="cumulativelifemeaning",
            name="accumulated_meaning",
            field=models.FloatField(blank=True, null=True, verbose_name="累积的意义"),
        ),
        migrations.AddField(
            model_name="cumulativelifemeaning",
            name="last_updated",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="最后更新时间"
            ),
        ),
        migrations.AddField(
            model_name="cumulativelifemeaning",
            name="total_meaning",
            field=models.FloatField(blank=True, null=True, verbose_name="总意义值"),
        ),
    ]
