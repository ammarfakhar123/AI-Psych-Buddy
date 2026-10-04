from django.db import migrations

from apps.exercises.seed_data import GROUNDING_EXERCISES


def seed(apps, schema_editor):
    WellnessExercise = apps.get_model("exercises", "WellnessExercise")
    for data in GROUNDING_EXERCISES:
        WellnessExercise.objects.update_or_create(slug=data["slug"], defaults=data)


def unseed(apps, schema_editor):
    apps.get_model("exercises", "WellnessExercise").objects.filter(
        slug__in=[d["slug"] for d in GROUNDING_EXERCISES]).delete()


class Migration(migrations.Migration):
    dependencies = [("exercises", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
