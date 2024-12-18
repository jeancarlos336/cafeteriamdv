# Generated by Django 5.1.2 on 2024-10-21 15:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CategoriaProducto",
            fields=[
                ("id_categoria", models.AutoField(primary_key=True, serialize=False)),
                ("nomb_categoria", models.CharField(max_length=100)),
            ],
            options={
                "verbose_name": "Categoría de Producto",
                "verbose_name_plural": "Categorías de Productos",
            },
        ),
        migrations.CreateModel(
            name="Venta",
            fields=[
                ("id_venta", models.AutoField(primary_key=True, serialize=False)),
                ("fecha", models.DateField(auto_now_add=True)),
                ("cliente", models.CharField(max_length=150)),
                ("total", models.DecimalField(decimal_places=2, max_digits=10)),
            ],
            options={
                "verbose_name": "Venta",
                "verbose_name_plural": "Ventas",
            },
        ),
        migrations.CreateModel(
            name="Producto",
            fields=[
                ("id_producto", models.AutoField(primary_key=True, serialize=False)),
                ("nom_producto", models.CharField(max_length=150)),
                (
                    "costo_producto",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                ("valor_venta", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "id_categoria",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="ventas.categoriaproducto",
                    ),
                ),
            ],
            options={
                "verbose_name": "Producto",
                "verbose_name_plural": "Productos",
            },
        ),
        migrations.CreateModel(
            name="DetalleVenta",
            fields=[
                (
                    "id_detalleventa",
                    models.AutoField(primary_key=True, serialize=False),
                ),
                ("cantidad", models.IntegerField()),
                (
                    "precio_unitario",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                ("sub_total", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "id_producto",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="ventas.producto",
                    ),
                ),
                (
                    "id_venta",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="ventas.venta"
                    ),
                ),
            ],
            options={
                "verbose_name": "Detalle de Venta",
                "verbose_name_plural": "Detalles de Ventas",
            },
        ),
    ]
