from django.db import models

# Modelo para la categoría de productos
class CategoriaProducto(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nomb_categoria = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Categoría de Producto"
        verbose_name_plural = "Categorías de Productos"

    def __str__(self):
        return self.nomb_categoria


# Modelo para los productos
class Producto(models.Model):
    id_producto = models.AutoField(primary_key=True)
    nom_producto = models.CharField(max_length=150)
    costo_producto = models.DecimalField(max_digits=10, decimal_places=2)
    valor_venta = models.DecimalField(max_digits=10, decimal_places=2)
    id_categoria = models.ForeignKey(CategoriaProducto, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def __str__(self):
        return self.nom_producto


# Modelo para las ventas
class Venta(models.Model):
    id_venta = models.AutoField(primary_key=True)
    fecha = models.DateField(auto_now_add=True)
    cliente = models.CharField(max_length=150)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"

    def __str__(self):
        return f"Venta {self.id_venta} - {self.cliente}"


# Modelo para el detalle de la venta
class DetalleVenta(models.Model):
    id_detalleventa = models.AutoField(primary_key=True)
    id_venta = models.ForeignKey(Venta, on_delete=models.CASCADE)
    id_producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Detalle de Venta"
        verbose_name_plural = "Detalles de Ventas"

    def __str__(self):
        return f"{self.cantidad} de {self.id_producto} en Venta {self.id_venta}"
    
    #def save(self, *args, **kwargs):
     #   self.sub_total = self.cantidad * self.precio_unitario
      #  super().save(*args, **kwargs)
    
    
from django.forms import inlineformset_factory

def crear_venta(request):
    DetalleVentaFormSet = inlineformset_factory(
        Venta, DetalleVenta, fields=['id_producto', 'cantidad'], extra=1
    )
    
    if request.method == 'POST':
        form_venta = VentaForm(request.POST)
        formset_detalles = DetalleVentaFormSet(request.POST)

        if form_venta.is_valid() and formset_detalles.is_valid():
            venta = form_venta.save()
            detalles = formset_detalles.save(commit=False)
            
            for detalle in detalles:
                detalle.id_venta = venta
                detalle.precio_unitario = detalle.id_producto.precio  # Tomamos el precio del producto
                detalle.sub_total = detalle.precio_unitario * detalle.cantidad
                detalle.save()
                
            return redirect('listar_ventas')

    else:
        form_venta = VentaForm()
        formset_detalles = DetalleVentaFormSet()

    return render(request, 'ventas/crear_venta.html', {
        'form_venta': form_venta,
        'formset_detalles': formset_detalles
    })

class Compra(models.Model):
    fecha = models.DateField()
    numero_boleta = models.CharField(max_length=20)
    destino = models.CharField(max_length=100)
    detalle = models.TextField()
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Compra {self.numero_boleta} - {self.destino}"
    