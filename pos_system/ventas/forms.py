from django import forms
from .models import Producto, Venta, CategoriaProducto, DetalleVenta, Compra
from django.forms import inlineformset_factory
from django.forms import DateInput
from .models import Compra  # Modelo de Compra, asegúrate de que esté definido
from django.contrib.auth.models import User


class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ["cliente"]


class ActVentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ["cliente", "estado"]


# Reemplaza tu DetalleVentaFormSet actual por este:
DetalleVentaFormSet = inlineformset_factory(
    Venta,
    DetalleVenta,
    fields=["id_producto", "cantidad", "precio_unitario", "sub_total"],
    extra=2,
    can_delete=True,
)


class CategoriaProductoForm(forms.ModelForm):
    class Meta:
        model = CategoriaProducto
        fields = ["nomb_categoria"]  # Campo del modelo que se incluirá en el formulario


class FiltroVentasForm(forms.Form):
    fecha_inicio = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        required=True,
        label="Fecha Inicio",
    )
    fecha_fin = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), required=True, label="Fecha Fin"
    )
    cliente = forms.CharField(max_length=255, required=False, label="Cliente")


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            "nom_producto",
            "costo_producto",
            "valor_venta",
            "id_categoria",
        ]  # Asegúrate de usar los nombres de campos correctos
        labels = {
            "nom_producto": "Nombre del Producto",
            "costo_producto": "Costo",
            "valor_venta": "Precio de Venta",
        }
        widgets = {
            "nom_producto": forms.TextInput(attrs={"class": "form-control"}),
            "costo_producto": forms.NumberInput(attrs={"class": "form-control"}),
            "valor_venta": forms.NumberInput(attrs={"class": "form-control"}),
        }


class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ["fecha", "numero_boleta", "destino", "detalle", "total"]

    # Añadir el widget de tipo 'date' para el campo de fecha
    fecha = forms.DateField(widget=DateInput(attrs={"type": "date"}))


class ReporteCompraForm(forms.Form):
    fecha_inicio = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), label="Fecha de inicio"
    )
    fecha_fin = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), label="Fecha de fin"
    )
    destino = forms.CharField(label="Destino", required=False)


# reporte de ventas
class ReporteVentaForm(forms.Form):
    fecha_inicio = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), label="Fecha de inicio"
    )
    fecha_fin = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), label="Fecha de fin"
    )
    vendedor = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        empty_label="Todos los vendedores",
        label="Vendedor (opcional)",
    )
