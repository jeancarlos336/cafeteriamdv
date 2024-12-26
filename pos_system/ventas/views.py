from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps
from io import BytesIO
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum
from django.db.models.functions import TruncWeek, TruncMonth
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.forms import inlineformset_factory

from reportlab.lib.pagesizes import A4, letter, landscape
from reportlab.pdfgen import canvas
from xhtml2pdf import pisa

from .forms import (
    ActVentaForm,
    CategoriaProductoForm,
    CompraForm,
    DetalleVentaFormSet,
    FiltroVentasForm,
    ProductoForm,
    ReporteCompraForm,
    ReporteVentaForm,
    VentaForm,
)
from .models import CategoriaProducto, Compra, DetalleVenta, Producto, Venta


# VISTAS ESPECIALES Y DE LOGIN
# Decorador personalizado para verificar si es administrador
def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesión primero.")
            return redirect(settings.LOGIN_URL + f"?next={request.path}")

        if not request.user.groups.filter(name="Administradores").exists():
            messages.error(
                request, "No tienes acceso a este menú. Debes ser administrador."
            )
            # Puedes cambiar esta URL por la que necesites
            return redirect("dashboard")

        return view_func(request, *args, **kwargs)

    return _wrapped_view


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
            messages.error(
                request, "Hubo un error en el registro. Por favor, verifica los datos."
            )
    else:
        form = UserCreationForm()
    return render(request, "ventas/register.html", {"form": form})


# Vista del Dashboard (solo accesible para usuarios autenticados)
@login_required
def dashboard_view(request):
    # Ventas semanales
    ventas_semanales = (
        Venta.objects.annotate(semana=TruncWeek("fecha"))
        .values("semana")
        .annotate(total_ventas=Sum("total"))
        .order_by("semana")
    )

    # Ventas mensuales
    ventas_mensuales = (
        Venta.objects.annotate(mes=TruncMonth("fecha"))
        .values("mes")
        .annotate(total_ventas=Sum("total"))
        .order_by("mes")
    )

    # Preparar datos para gráficos
    labels_semanales = [v["semana"].strftime("%d-%m-%Y") for v in ventas_semanales]
    datos_semanales = [float(v["total_ventas"]) for v in ventas_semanales]

    labels_mensuales = [v["mes"].strftime("%B %Y") for v in ventas_mensuales]
    datos_mensuales = [float(v["total_ventas"]) for v in ventas_mensuales]

    context = {
        "labels_semanales": labels_semanales,
        "datos_semanales": datos_semanales,
        "labels_mensuales": labels_mensuales,
        "datos_mensuales": datos_mensuales,
    }

    return render(request, "ventas/dashboard.html", context)

# Vista personalizada para el login (verifica si el usuario ya está autenticado)
class CustomLoginView(LoginView):
    template_name = (
        "login.html"  # Asegúrate de tener la plantilla de login correctamente
    )

    def get_redirect_url(self):
        # Redirige al dashboard si el usuario ya está autenticado
        if self.request.user.is_authenticated:
            return redirect("dashboard")
        return super().get_redirect_url()

# Vista personalizada para el logout (cerrar sesión)
def custom_logout(request):
    logout(request)
    messages.success(request, "Has cerrado sesión correctamente.")
    return redirect("login")  # Redirige a la página de login después de cerrar sesión


# ---------------------------------Vistas de Productos--------------------------------------------
# Vista para listar productos

def listar_productos(request):
    # Obtener el término de búsqueda de los parámetros GET
    search_query = request.GET.get("search", "")

    # Obtener todos los productos ordenados
    productos_list = Producto.objects.all()

    # Filtrar productos si hay un término de búsqueda
    if search_query:
        productos_list = productos_list.filter(
            Q(nom_producto__icontains=search_query)
            | Q(valor_venta__icontains=search_query)
        )

    # Dividir en páginas de 10 registros cada una
    paginator = Paginator(productos_list, 10)

    # Obtener el número de página actual desde los parámetros GET
    page_number = request.GET.get("page")
    productos = paginator.get_page(page_number)  # Obtener la página correspondiente

    # Renderizar la plantilla con los datos paginados
    return render(
        request,
        "ventas/listar_productos.html",
        {
            "productos": productos,  # Nombre consistente
            "search_query": search_query,
        },
    )

# Vista para crear un producto
@login_required
@admin_required  # Usamos nuestro decorador personalizado
def crear_producto(request):
    if request.method == "POST":
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("listar_productos")
    else:
        form = ProductoForm()
    return render(request, "ventas/crear_producto.html", {"form": form})


# elimina prodctuo
@login_required
def eliminar_producto(request, id_producto):
    producto = get_object_or_404(
        Producto, id_producto=id_producto
    )  # Cambia aquí a id_producto
    producto.delete()
    messages.success(request, "Producto eliminado exitosamente.")
    return redirect(reverse("listar_productos"))


# actualiza producto
@login_required
@admin_required  # Usamos nuestro decorador personalizado
def actualizar_producto(request, id_producto):
    producto = get_object_or_404(
        Producto, id_producto=id_producto
    )  # Cambia aquí a id_producto

    if request.method == "POST":
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto actualizado exitosamente.")
            return redirect(
                reverse("listar_productos")
            )  # Redirige a la lista de productos
    else:
        form = ProductoForm(instance=producto)

    return render(
        request, "ventas/actualizar_producto.html", {"form": form, "producto": producto}
    )


# ----------------------------Vistas de Ventas---------------------------
# Vista para crear venta completa
login_required
@transaction.atomic
def crear_venta_completa(request):
    if request.method == "POST":
        venta_form = VentaForm(request.POST)
        formset = DetalleVentaFormSet(request.POST)

        if venta_form.is_valid() and formset.is_valid():
            total_venta = Decimal("0.00")

            # Solo guarda la venta si hay detalles
            if any(
                form.cleaned_data and not form.cleaned_data.get("DELETE")
                for form in formset
            ):
                venta = venta_form.save(commit=False)
                venta.total = Decimal("0.00")  # Inicializa con cero
                venta.vendedor = request.user  # Asigna el usuario logeado
                venta.estado = request.POST.get(
                    "estado", "Pagado"
                )  # Obtiene el estado del formulario
                venta.save()

                detalles = formset.save(commit=False)

                for detalle in detalles:
                    producto = detalle.id_producto
                    detalle.id_venta = venta
                    detalle.precio_unitario = producto.valor_venta
                    detalle.sub_total = detalle.cantidad * detalle.precio_unitario
                    detalle.save()
                    total_venta += detalle.sub_total

                # Actualiza el total de la venta
                venta.total = total_venta
                venta.save()

                return redirect("listar_ventas")
            else:
                messages.error(request, "Debe agregar al menos un producto a la venta")
    else:
        venta_form = VentaForm()
        formset = DetalleVentaFormSet()

    return render(
        request,
        "ventas/crear_venta_completa.html",
        {"venta_form": venta_form, "detalle_venta_formset": formset},
    )


# Vista para listar ventas

@login_required
def listar_ventas(request):
    # Obtener el término de búsqueda de los parámetros GET
    search_query = request.GET.get("search", "").strip()
    # Filtrar las ventas si hay un término de búsqueda
    ventas_list = Venta.objects.all().order_by("-id_venta")  # Ordenar por ID descendente
    
    if search_query:
        try:
            # Intenta convertir el término de búsqueda al formato 'YYYY-MM-DD'
            search_date = datetime.strptime(search_query, "%d-%m-%Y").date()
            ventas_list = ventas_list.filter(
                Q(fecha=search_date)  # filtra por fecha exacta
            )
        except ValueError:
            # Si no es una fecha, busca en otros campos
            ventas_list = ventas_list.filter(
                Q(cliente__icontains=search_query)
                | Q(id_venta__icontains=search_query)
                | Q(estado__icontains=search_query)
                | Q(total__icontains=search_query)
            )

    # Configuración de la paginación
    paginator = Paginator(ventas_list, 15)
    page_number = request.GET.get("page")
    ventas = paginator.get_page(page_number)

    # Calcular el rango de páginas a mostrar
    PAGES_TO_SHOW = 5  # Número de páginas a mostrar a cada lado de la página actual
    current_page = ventas.number
    total_pages = paginator.num_pages

    # Calcular el rango de páginas
    start_index = max(0, current_page - PAGES_TO_SHOW - 1)
    end_index = min(total_pages, current_page + PAGES_TO_SHOW)
    page_range = list(paginator.page_range)[start_index:end_index]

    # Agregar primera página y puntos suspensivos si es necesario
    if start_index > 0:
        page_range = ['1', '...'] + page_range

    # Agregar última página y puntos suspensivos si es necesario
    if end_index < total_pages:
        page_range = page_range + ['...', str(total_pages)]

    return render(
        request,
        "ventas/listar_ventas.html",
        {
            "ventas": ventas,
            "search_query": search_query,
            "page_range": page_range,
        },
    )

# Vista para ver detalle de una venta
@login_required
def ver_detalle_venta(request, id_venta):
    venta = get_object_or_404(Venta, id_venta=id_venta)
    detalles = DetalleVenta.objects.filter(
        id_venta=venta
    )  # Ajustado para usar el campo correcto
    return render(
        request, "ventas/ver_detalle_venta.html", {"venta": venta, "detalles": detalles}
    )


# Vista elimina venta
@admin_required  # Usamos nuestro decorador personalizado
@login_required
def eliminar_venta(request, venta_id):
    venta = get_object_or_404(Venta, id_venta=venta_id)
    venta.delete()
    messages.success(request, "Venta eliminada correctamente.")
    return redirect("listar_ventas")


# ventas pendientes
def informe_ventas(request):
    ventas = []
    ventas_total = 0

    if request.method == "POST":
        fecha_inicio = request.POST.get("fecha_inicio")
        fecha_termino = request.POST.get("fecha_termino")
        cliente = request.POST.get("cliente")

        ventas = Venta.objects.filter(estado="Pendiente").order_by('cliente')

        if fecha_inicio:
            ventas = ventas.filter(fecha__gte=fecha_inicio)
        if fecha_termino:
            ventas = ventas.filter(fecha__lte=fecha_termino)
        if cliente:
            ventas = ventas.filter(cliente__icontains=cliente)

        ventas_total = ventas.aggregate(total=Sum("total"))["total"] or 0

    context = {
        "ventas": ventas,
        "ventas_total": ventas_total,
    }
    return render(request, "ventas/informe_ventas.html", context)


# actualizar venta
def actualizar_venta(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == "POST":
        form = ActVentaForm(request.POST, instance=venta)
        if form.is_valid():
            form.save()
            return redirect(
                "listar_ventas"
            )  # Reemplaza 'lista_ventas' con la URL de tu lista de ventas
    else:
        form = ActVentaForm(instance=venta)
    return render(request, "ventas/actualizar_venta.html", {"form": form})


# --------------------VISTAS DE CATEGORIAS---------------------------------------------------
# Vista para listar categorías
@login_required
@admin_required  # Usamos nuestro decorador personalizado
def listar_categorias(request):
    # Obtener el término de búsqueda de los parámetros GET
    search_query = request.GET.get("search", "")

    # Obtener todos las categorias ordenados
    categorias_list = CategoriaProducto.objects.all().order_by(
        "id_categoria"
    )  # Obtiene todas las categorías

    # Filtrar productos si hay un término de búsqueda
    if search_query:
        categorias_list = categorias_list.filter(
            Q(id_categoria__icontains=search_query)
            | Q(nomb_categoria__icontains=search_query)
        )
    # Dividir en páginas de 10 registros cada una
    paginator = Paginator(categorias_list, 10)

    # Obtener el número de página actual desde los parámetros GET
    page_number = request.GET.get("page")
    categoria = paginator.get_page(page_number)  # Obtener la página correspondiente

    # Renderizar la plantilla con los datos paginados
    return render(
        request,
        "ventas/listar_categorias.html",
        {
            "categoria": categoria,  # Nombre consistente
            "search_query": search_query,
        },
    )


# Vista para crear una categoría
@login_required
@admin_required  # Usamos nuestro decorador personalizado
def crear_categoria(request):
    if request.method == "POST":
        form = CategoriaProductoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(
                "listar_categorias"
            )  # Redirige a la vista de listar categorías
    else:
        form = CategoriaProductoForm()
    return render(request, "ventas/crear_categoria.html", {"form": form})


# elimina Categoria
@login_required
def eliminar_categoria(request, id_categoria):
    categoria = get_object_or_404(CategoriaProducto, id_categoria=id_categoria)
    categoria.delete()
    messages.success(request, "categoria eliminada exitosamente.")
    return redirect(reverse("listar_categorias"))


# actualiza Categoria
@login_required
@admin_required  # Usamos nuestro decorador personalizado
def actualizar_categoria(request, id_categoria):
    try:
        # Intenta obtener la categoría por su ID
        categoria = CategoriaProducto.objects.get(id_categoria=id_categoria)
    except CategoriaProducto.DoesNotExist:
        messages.error(request, "La categoría no existe.")
        return redirect("listar_categorias")

    if request.method == "POST":
        form = CategoriaProductoForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoría actualizada exitosamente.")
            return redirect("listar_categorias")
    else:
        form = CategoriaProductoForm(instance=categoria)

    return render(
        request,
        "ventas/actualizarcategoria.html",
        {"form": form, "categoria": categoria},
    )


# ------------VISTAS ESPECIALEAS OBTIENE PRECIO
# Vista obtine precio
def obtener_precio_producto(request, producto_id):
    try:
        producto = Producto.objects.get(id_producto=producto_id)
        return JsonResponse(
            {"precio": producto.valor_venta}
        )  # Asegúrate de que 'valor_venta' es el precio correcto
    except Producto.DoesNotExist:
        return JsonResponse({"precio": 0})


# ----------------VISTAS DE COMPRAS---------------------


@login_required
def listar_compras(request):
    # Obtener el término de búsqueda de los parámetros GET
    search_query = request.GET.get("search", "").strip()

    # Filtrar las compras si hay un término de búsqueda

    compras_list = Compra.objects.all().order_by("-id")

    if search_query:
        try:
            # Intenta convertir el término de búsqueda al formato 'YYYY-MM-DD'
            search_date = datetime.strptime(search_query, "%d-%m-%Y").date()
            compras_list = compras_list.filter(
                Q(fecha=search_date)  # Filtra por fecha exacta
            )
        except ValueError:
            compras_list = compras_list.filter(
                Q(numero_boleta__icontains=search_query)
                | Q(  # Reemplaza 'campo1' con el nombre de tu campo a buscar
                    destino__icontains=search_query
                )
                | Q(detalle__icontains=search_query)
                | Q(total__icontains=search_query)
                # Agrega más campos según sea necesario
            )

    # Dividir en páginas de 10 registros cada una
    paginator = Paginator(compras_list, 10)

    # Obtener el número de página actual desde los parámetros GET
    page_number = request.GET.get("page")
    compras = paginator.get_page(page_number)  # Obtener la página correspondiente

    # Renderizar la plantilla con los datos paginados
    return render(
        request,
        "ventas/listar_compras.html",
        {
            "compras": compras,  # Página actual de ventas
            "search_query": search_query,  # Pasar el término de búsqueda para reutilizarlo en la plantilla
        },
    )


@login_required
def crear_compra(request):
    if request.method == "POST":
        form = CompraForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Compra registrada con éxito.")
            return redirect(
                "listar_compras"
            )  # Aquí no se necesita 'compras:' en el nombre de la URL
    else:
        form = CompraForm()
    return render(request, "ventas/crear_compra.html", {"form": form})


@login_required
def ver_compra(request, compra_id):
    compra = get_object_or_404(Compra, id=compra_id)
    return render(request, "ventas/ver_compra.html", {"compra": compra})


@login_required
def editar_compra(request, compra_id):
    compra = get_object_or_404(Compra, id=compra_id)
    if request.method == "POST":
        form = CompraForm(request.POST, instance=compra)
        if form.is_valid():
            form.save()
            messages.success(request, "Compra actualizada con éxito.")
            return redirect("listar_compras")
    else:
        form = CompraForm(instance=compra)
    return render(
        request, "ventas/editar_compra.html", {"form": form, "compra": compra}
    )


@login_required
def eliminar_compra(request, compra_id):
    compra = get_object_or_404(Compra, id=compra_id)
    if request.method == "POST":
        compra.delete()
        messages.success(request, "Compra eliminada con éxito.")
        return redirect("listar_compras")
    return render(request, "ventas/eliminar_compra.html", {"compra": compra})


# ---------INFORMES Y BOLETAS----------------------
# Vista generar boleta de venta
def generar_boleta_impresion(request, id_venta):
    venta = Venta.objects.get(id_venta=id_venta)
    detalles = DetalleVenta.objects.filter(id_venta=venta)

    # Renderiza la plantilla HTML
    html_content = render_to_string(
        "ventas/boleta_pdf.html", {"venta": venta, "detalles": detalles}
    )

    return HttpResponse(html_content)


# ------------------------------------------------------------


@login_required
@admin_required  # Usamos nuestro decorador personalizado
def generar_reporte_compras(request):
    if request.method == "POST":
        form = ReporteCompraForm(request.POST)
        if form.is_valid():
            fecha_inicio = form.cleaned_data["fecha_inicio"]
            fecha_fin = form.cleaned_data["fecha_fin"]
            destino = form.cleaned_data["destino"]

            # Filtrar las compras según las fechas y el destino
            if destino:
                compras = Compra.objects.filter(
                    fecha__range=(fecha_inicio, fecha_fin), destino=destino
                ).order_by("-id")
            else:
                compras = Compra.objects.filter(
                    fecha__range=(fecha_inicio, fecha_fin)
                ).order_by("-id")

            # Calcular el total
            total_compras = sum(compra.total for compra in compras)

            # Generar el PDF en formato horizontal
            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=landscape(A4))

            # Encabezado
            p.setFont("Helvetica-Bold", 16)
            p.drawString(60, 550, "Informe de Compras - Cafetería MDV")
            p.setFont("Helvetica", 12)
            p.drawString(60, 530, f"Desde {fecha_inicio} hasta {fecha_fin}")
            if destino:
                p.drawString(60, 510, f"Destino: {destino}")

            # Tabla
            y = 480
            p.setFont("Helvetica-Bold", 10)
            p.drawString(60, y, "Fecha")
            p.drawString(130, y, "N° Boleta")
            p.drawString(220, y, "Destino")
            p.drawString(360, y, "Detalle")
            p.drawString(600, y, "Total")
            y -= 20

            # Contenido de la tabla
            p.setFont("Helvetica", 10)
            for compra in compras:
                p.drawString(60, y, compra.fecha.strftime("%d-%m-%Y"))
                p.drawString(130, y, compra.numero_boleta)
                p.drawString(220, y, compra.destino if compra.destino else "N/A")
                p.drawString(360, y, compra.detalle)
                p.drawString(600, y, "{:,.0f}".format(compra.total).replace(",", "."))
                y -= 15

                if y < 50:  # Saltar a una nueva página si no hay más espacio
                    p.showPage()
                    p.setFont("Helvetica", 10)
                    y = 550

            # Total al final
            p.setFont("Helvetica-Bold", 12)
            p.drawString(400, y - 30, "Total Compras:")
            p.drawString(500, y - 30, "{:,.0f}".format(total_compras).replace(",", "."))

            p.showPage()
            p.save()

            # Respuesta HTTP
            buffer.seek(0)
            response = HttpResponse(buffer, content_type="application/pdf")
            response[
                "Content-Disposition"
            ] = f'attachment; filename="reporte_compras_horizontal_{datetime.now().strftime("%Y%m%d")}.pdf"'
            return response
    else:
        form = ReporteCompraForm()

    return render(request, "ventas/reporte_compras.html", {"form": form})


# Vista para generar reporte de ventas


@login_required
@admin_required
def generar_reporte_ventas(request):
    if request.method == "POST":
        form = ReporteVentaForm(request.POST)
        if form.is_valid():
            fecha_inicio = form.cleaned_data["fecha_inicio"]
            fecha_fin = form.cleaned_data["fecha_fin"]
            vendedor = form.cleaned_data.get("vendedor")

            # Filtrar las ventas según las fechas
            ventas = Venta.objects.filter(fecha__range=(fecha_inicio, fecha_fin))

            # Filtrar por vendedor si se seleccionó
            if vendedor:
                ventas = ventas.filter(vendedor=vendedor)

            # Calcular el total de ventas
            total_ventas = ventas.aggregate(total=Sum("total"))["total"] or Decimal(
                "0.00"
            )

            # Preparar contexto para el template
            context = {
                "form": form,
                "ventas": ventas,
                "total_ventas": total_ventas,
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "vendedor_seleccionado": vendedor,
            }

            return render(request, "ventas/resultado_reporte.html", context)

    else:
        form = ReporteVentaForm()
    return render(request, "ventas/reporte_ventas.html", {"form": form})


# balance anual

from datetime import datetime
from django.shortcuts import render
from django.db.models import Sum


def balance_anual(request):
    if request.method == "POST":
        # Validar el año recibido
        try:
            year = int(request.POST.get("year"))
        except (TypeError, ValueError):
            year = None

        if year is None or year < 2000 or year > datetime.now().year:
            return render(
                request,
                "balance_form.html",
                {
                    "years": list(range(datetime.now().year, 2000, -1)),
                    "error": "Año inválido. Por favor, selecciona un año válido.",
                },
            )

        # Obtener ventas y compras agrupadas por mes
        ventas_mensuales = (
            Venta.objects.filter(fecha__year=year)
            .values_list("fecha__month")
            .annotate(total_ventas=Sum("total"))
        )

        compras_mensuales = (
            Compra.objects.filter(fecha__year=year)
            .values_list("fecha__month")
            .annotate(total_compras=Sum("total"))
        )

        # Crear un diccionario con las ventas y compras por mes
        meses = {i: {"ventas": 0, "compras": 0, "saldo": 0} for i in range(1, 13)}

        for venta in ventas_mensuales:
            mes, total_ventas = venta
            meses[mes]["ventas"] = total_ventas

        for compra in compras_mensuales:
            mes, total_compras = compra
            meses[mes]["compras"] = total_compras

        # Calcular el saldo mensual y los totales anuales
        for valores in meses.values():
            valores["saldo"] = valores["ventas"] - valores["compras"]

        total_ventas_anuales = sum(valores["ventas"] for valores in meses.values())
        total_compras_anuales = sum(valores["compras"] for valores in meses.values())
        saldo_anual = total_ventas_anuales - total_compras_anuales

        context = {
            "year": year,
            "meses": meses,
            "total_ventas_anuales": total_ventas_anuales,
            "total_compras_anuales": total_compras_anuales,
            "saldo_anual": saldo_anual,
        }

        return render(request, "ventas/balance_anual.html", context)

    else:
        # Preparar el formulario para seleccionar el año
        current_year = datetime.now().year
        years = list(range(current_year, 2000, -1))
        return render(request, "ventas/balance_form.html", {"years": years})
