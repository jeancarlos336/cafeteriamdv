from django.shortcuts import render, get_object_or_404, redirect
from .models import Producto, CategoriaProducto, Venta, DetalleVenta,Compra
from .forms import ProductoForm, VentaForm, CategoriaProductoForm
from .forms import VentaForm, DetalleVentaFormSet,CompraForm, ReporteCompraForm, ReporteVentaForm
from django.http import JsonResponse
from decimal import Decimal
from django.db import transaction
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from .models import Venta, DetalleVenta, Compra, Venta
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.contrib import messages
from django.urls import reverse
from django.core.paginator import Paginator
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib.auth.views import LoginView
from datetime import datetime
from io import BytesIO
from django.db import models
from django.conf import settings
from functools import wraps

# Decorador personalizado para verificar si es administrador
def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Debes iniciar sesión primero.')
            return redirect(settings.LOGIN_URL + f'?next={request.path}')
        
        if not request.user.groups.filter(name='Administradores').exists():
            messages.error(request, 'No tienes acceso a este menú. Debes ser administrador.')
            # Puedes cambiar esta URL por la que necesites
            return redirect('dashboard')  
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# Vista para listar productos
@admin_required  # Usamos nuestro decorador personalizado
def listar_productos(request):
    productos = Producto.objects.all().order_by('id_categoria_id')
    paginator = Paginator(productos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'ventas/listar_productos.html', {'page_obj': page_obj})

# Vista para registrar usuarios
@login_required
def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Inicia sesión automáticamente al registrarse
            messages.success(request, "Te has registrado correctamente.")
            return redirect("dashboard")  # Redirige al dashboard después de registrarse
        else:
            messages.error(request, "Hubo un error en el registro. Por favor, verifica los datos.")
    else:
        form = UserCreationForm()
    return render(request, "ventas/register.html", {"form": form})

# Vista del Dashboard (solo accesible para usuarios autenticados)



@login_required
def dashboard_view(request):
    return render(request, "ventas/dashboard.html")


# Vista para crear un producto

@login_required
@admin_required  # Usamos nuestro decorador personalizado
def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_productos')
    else:
        form = ProductoForm()
    return render(request, 'ventas/crear_producto.html', {'form': form})


# Vista para listar ventas
@login_required
def listar_ventas(request):
    ventas = Venta.objects.all().order_by('-id_venta')  # Ordenar por fecha descendente
    return render(request, 'ventas/listar_ventas.html', {'ventas': ventas})

# Vista para ver detalle de una venta

@login_required
def ver_detalle_venta(request, id_venta):
    venta = get_object_or_404(Venta, id_venta=id_venta)
    detalles = DetalleVenta.objects.filter(id_venta=venta)  # Ajustado para usar el campo correcto
    return render(request, 'ventas/ver_detalle_venta.html', {'venta': venta, 'detalles': detalles})


# Vista para listar categorías
@login_required
@admin_required  # Usamos nuestro decorador personalizado
def listar_categorias(request):
    categorias = CategoriaProducto.objects.all()  # Obtiene todas las categorías
    return render(request, 'ventas/listar_categorias.html', {'categorias': categorias})


# Vista para crear una categoría
@login_required
@admin_required  # Usamos nuestro decorador personalizado
def crear_categoria(request):
    if request.method == 'POST':
        form = CategoriaProductoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_categorias')  # Redirige a la vista de listar categorías
    else:
        form = CategoriaProductoForm()
    return render(request, 'ventas/crear_categoria.html', {'form': form})

@login_required
@transaction.atomic
def crear_venta_completa(request):
    if request.method == 'POST':
        venta_form = VentaForm(request.POST)
        
        if venta_form.is_valid():
            venta = venta_form.save(commit=False)
            # Inicialmente guardamos la venta con total 0
            venta.total = Decimal('0.00')
            venta.save()
            
            formset = DetalleVentaFormSet(request.POST, instance=venta)
            
            if formset.is_valid():
                total_venta = Decimal('0.00')
                detalles = formset.save(commit=False)
                
                for detalle in detalles:
                    producto = detalle.id_producto
                    detalle.precio_unitario = producto.valor_venta
                    detalle.sub_total = detalle.cantidad * detalle.precio_unitario
                    detalle.save()
                    total_venta += detalle.sub_total
                
                # Actualizamos el total de la venta
                venta.total = total_venta
                venta.save()
                
                # Eliminamos los detalles marcados para eliminar
                for obj in formset.deleted_objects:
                    obj.delete()
                
                return redirect('listar_ventas')
    else:
        venta_form = VentaForm()
        formset = DetalleVentaFormSet()
    
    return render(request, 'ventas/crear_venta_completa.html', {
        'venta_form': venta_form,
        'detalle_venta_formset': formset
    })


def obtener_precio_producto(request, producto_id):
    try:
        producto = Producto.objects.get(id_producto=producto_id)
        return JsonResponse({'precio': producto.valor_venta})  # Asegúrate de que 'valor_venta' es el precio correcto
    except Producto.DoesNotExist:
        return JsonResponse({'precio': 0})

@login_required
def generar_boleta_pdf(request, venta_id):
    venta = get_object_or_404(Venta, id_venta=venta_id)
    detalles = DetalleVenta.objects.filter(id_venta=venta)

    # Renderizar la plantilla HTML
    html = render_to_string('ventas/boleta_pdf.html', {
        'venta': venta,
        'detalles': detalles,
    })

    # Crear el objeto HttpResponse con el tipo de contenido adecuado
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="boleta_{venta.id_venta}.pdf"'

    # Convertir el HTML a PDF
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Error al generar PDF', status=400)

    return response

@login_required
def eliminar_venta(request, venta_id):
    venta = get_object_or_404(Venta, id_venta=venta_id)
    venta.delete()
    messages.success(request, 'Venta eliminada correctamente.')
    return redirect('listar_ventas')

@login_required
def eliminar_producto(request, id_producto):
    producto = get_object_or_404(Producto, id_producto=id_producto)  # Cambia aquí a id_producto
    
    # Verificar que la solicitud sea POST para proceder con la eliminación
    if request.method == 'POST':
        producto.delete()
        messages.success(request, 'Producto eliminado exitosamente.')
        return redirect(reverse('listar_productos'))  # Redirigir a la lista de productos

    # Si no es una solicitud POST, redirige a la lista de productos
    return redirect(reverse('listar_productos'))

@login_required
@admin_required  # Usamos nuestro decorador personalizado
def actualizar_producto(request, id_producto):
    producto = get_object_or_404(Producto, id_producto=id_producto)  # Cambia aquí a id_producto
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado exitosamente.')
            return redirect(reverse('listar_productos'))  # Redirige a la lista de productos
    else:
        form = ProductoForm(instance=producto)
    
    return render(request, 'ventas/actualizar_producto.html', {'form': form, 'producto': producto})


# Vista personalizada para el login (verifica si el usuario ya está autenticado)
class CustomLoginView(LoginView):
    template_name = 'login.html'  # Asegúrate de tener la plantilla de login correctamente

    def get_redirect_url(self):
        # Redirige al dashboard si el usuario ya está autenticado
        if self.request.user.is_authenticated:
            return redirect('dashboard')
        return super().get_redirect_url()


# Vista personalizada para el logout (cerrar sesión)
def custom_logout(request):
    logout(request)
    messages.success(request, "Has cerrado sesión correctamente.")
    return redirect('login')  # Redirige a la página de login después de cerrar sesión


@login_required
def listar_compras(request):
    compras = Compra.objects.all().order_by('-fecha')
    return render(request, 'ventas/listar_compras.html', {'compras': compras})
@login_required
def crear_compra(request):
    if request.method == 'POST':
        form = CompraForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Compra registrada con éxito.")
            return redirect('listar_compras')  # Aquí no se necesita 'compras:' en el nombre de la URL
    else:
        form = CompraForm()
    return render(request, 'ventas/crear_compra.html', {'form': form})


@login_required
def ver_compra(request, compra_id):
    compra = get_object_or_404(Compra, id=compra_id)
    return render(request, 'ventas/ver_compra.html', {'compra': compra})

@login_required
def editar_compra(request, compra_id):
    compra = get_object_or_404(Compra, id=compra_id)
    if request.method == 'POST':
        form = CompraForm(request.POST, instance=compra)
        if form.is_valid():
            form.save()
            messages.success(request, "Compra actualizada con éxito.")
            return redirect('listar_compras')
    else:
        form = CompraForm(instance=compra)
    return render(request, 'ventas/editar_compra.html', {'form': form, 'compra': compra})


@login_required
def eliminar_compra(request, compra_id):
    compra = get_object_or_404(Compra, id=compra_id)
    if request.method == 'POST':
        compra.delete()
        messages.success(request, "Compra eliminada con éxito.")
        return redirect('listar_compras')
    return render(request, 'ventas/eliminar_compra.html', {'compra': compra})


@login_required
@admin_required  # Usamos nuestro decorador personalizado
def generar_reporte_compras(request):
    if request.method == "POST":
        form = ReporteCompraForm(request.POST)
        if form.is_valid():
            fecha_inicio = form.cleaned_data['fecha_inicio']
            fecha_fin = form.cleaned_data['fecha_fin']
            destino = form.cleaned_data['destino']

            # Filtrar las compras según las fechas y el destino solo si este está definido
            if destino:
                compras = Compra.objects.filter(
                    fecha__range=(fecha_inicio, fecha_fin),
                    destino=destino
                )
            else:
                compras = Compra.objects.filter(
                    fecha__range=(fecha_inicio, fecha_fin)
                )

            # Sumar todos los valores de las compras
            total_compras = sum(compra.total for compra in compras)

            # Generar el PDF
            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=A4)            
            
            # Título dividido en dos líneas
            encabezado_linea1 = "Informe de Compras Cafetería MDV"
            encabezado_linea2 = f"Desde {fecha_inicio} hasta {fecha_fin}"
            if destino:
                encabezado_linea2 += f" Items: {destino}"

            # Establecer el estilo de fuente
            p.setFont("Helvetica-Bold", 16)

            # Dibujar la primera línea del encabezado
            p.drawString(100, 800, encabezado_linea1)

            # Dibujar la segunda línea del encabezado
            p.setFont("Helvetica", 12)  # Fuente normal para la segunda línea
            p.drawString(100, 780, encabezado_linea2)

            y = 750  # Coordenada y inicial para los encabezados de columnas
            p.setFont("Helvetica", 10)
            # Encabezados de las columnas con borde
            p.drawString(80, y, "Fecha")
            p.drawString(180, y, "N° Boleta")
            p.drawString(280, y, "Destino")
            p.drawString(380, y, "Detalle")
            p.drawString(480, y, "Total")
            y -= 30

            # Dibujar líneas horizontales para el encabezado
            p.line(70, y + 10, 530, y + 10)  # Línea horizontal en el encabezado

            # Agregar los detalles de cada compra
            for compra in compras:
                p.drawString(80, y, compra.fecha.strftime('%d-%m-%Y'))
                p.drawString(180, y, compra.numero_boleta)
                p.drawString(280, y, compra.destino)
                p.drawString(380, y, compra.detalle)        
                p.drawString(480, y, "{:,.0f}".format(compra.total).replace(',', '.'))
                y -= 20

                # Dibujar líneas horizontales para separar filas
                p.line(70, y + 10, 530, y + 10)  # Línea horizontal después de cada fila

            # Agregar el total de las compras al final del informe
            y -= 20  # Espacio antes del total
            p.setFont("Helvetica-Bold", 12)  # Negrita para el total
            p.drawString(380, y, "Total Compras:")
            p.drawString(480, y, "{:,.0f}".format(total_compras).replace(',', '.'))

            # Agregar línea para el total
            y -= 20
            p.line(70, y + 10, 530, y + 10)  # Línea horizontal debajo del total

            p.showPage()
            p.save()

            # Configurar el HttpResponse para devolver el PDF
            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="reporte_compras_{datetime.now().strftime("%Y%m%d")}.pdf"'
            return response      

    else:
        form = ReporteCompraForm()

    return render(request, 'ventas/reporte_compras.html', {'form': form})



# Vista para generar reporte de ventas
@login_required
@admin_required  # Usamos nuestro decorador personalizado
def generar_reporte_ventas(request):
    if request.method == "POST":
        form = ReporteVentaForm(request.POST)
        if form.is_valid():
            fecha_inicio = form.cleaned_data['fecha_inicio']
            fecha_fin = form.cleaned_data['fecha_fin']

            # Filtrar las ventas según las fechas
            ventas = Venta.objects.filter(fecha__range=(fecha_inicio, fecha_fin))

            # Calcular el total de ventas
            total_ventas = ventas.aggregate(total=models.Sum('total'))['total'] or 0

            # Generar el PDF
            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=A4)
            
            # Título del reporte
            encabezado = f"Informe de Ventas desde {fecha_inicio} hasta {fecha_fin}"
            p.setFont("Helvetica-Bold", 16)
            p.drawString(100, 800, encabezado)
            y = 750  # Coordenada y inicial

            # Encabezados de las columnas
            p.setFont("Helvetica-Bold", 12)
            p.drawString(80, y, "Fecha")
            p.drawString(180, y, "Cliente")
            p.drawString(280, y, "Total")
            y -= 30

            # Datos de las ventas
            p.setFont("Helvetica", 10)
            for venta in ventas:
                p.drawString(80, y, venta.fecha.strftime('%d-%m-%Y'))
                p.drawString(180, y, venta.cliente)
                p.drawString(280, y, "{:,.0f}".format(venta.total).replace(',', '.'))               
                y -= 20

            # Total de ventas
            y -= 20  # Espacio antes del total
            p.setFont("Helvetica-Bold", 12)
            p.drawString(180, y, "Total Ventas:")
            p.drawString(280, y, "{:,.0f}".format(total_ventas).replace(',', '.'))
            
            p.showPage()
            p.save()

            # Configurar el HttpResponse para devolver el PDF
            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="reporte_ventas_{datetime.now().strftime("%Y%m%d")}.pdf"'
            return response

    else:
        form = ReporteVentaForm()

    return render(request, 'ventas/reporte_ventas.html', {'form': form})

