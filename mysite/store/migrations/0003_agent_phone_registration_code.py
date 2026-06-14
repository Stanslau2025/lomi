# Generated for agent phone and registration codes.

from django.db import migrations, models


def fill_registration_codes(apps, schema_editor):
    Agent = apps.get_model("store", "Agent")
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    used = set()
    count = 0
    for agent in Agent.objects.order_by("created_at", "id"):
        normalized = (agent.registration_code or "").strip().upper()
        if normalized and normalized not in used:
            agent.registration_code = normalized
            agent.save(update_fields=["registration_code"])
            used.add(normalized)
            continue

        while True:
            code = f"{alphabet[count % len(alphabet)]}{20 + (count * 10)}"
            count += 1
            if code not in used:
                break
        agent.registration_code = code
        agent.save(update_fields=["registration_code"])
        used.add(code)


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0002_alter_product_category"),
    ]

    operations = [
        migrations.AddField(
            model_name="agent",
            name="phone",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="agent",
            name="registration_code",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.RunPython(fill_registration_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="agent",
            name="registration_code",
            field=models.CharField(blank=True, max_length=20, unique=True),
        ),
    ]
