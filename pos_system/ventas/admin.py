from django.contrib import admin
from .models import Producto, CategoriaProducto, Venta, DetalleVenta


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 1  # Número de formularios adicionales para añadir en el mismo formulario


class VentaAdmin(admin.ModelAdmin):
    list_display = (
        "id_venta",
        "fecha",
        "cliente",
        "total",
    )  # Campos a mostrar en la lista de ventas
    search_fields = ("cliente",)  # Permite buscar por cliente
    inlines = [DetalleVentaInline]  # Añade detalles de la venta en la misma página


class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        "id_producto",
        "nom_producto",
        "costo_producto",
        "valor_venta",
        "id_categoria",
    )  # Campos a mostrar en la lista de productos
    search_fields = ("nom_producto",)  # Permite buscar por nombre de producto


class CategoriaProductoAdmin(admin.ModelAdmin):
    list_display = (
        "id_categoria",
        "nomb_categoria",
    )  # Campos a mostrar en la lista de categorías
    search_fields = ("nomb_categoria",)  # Permite buscar por nombre de categoría


# Registro de modelos en el admin
admin.site.register(Producto, ProductoAdmin)
admin.site.register(CategoriaProducto, CategoriaProductoAdmin)
admin.site.register(Venta, VentaAdmin)
