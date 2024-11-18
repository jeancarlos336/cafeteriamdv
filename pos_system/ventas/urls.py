from django.urls import path
from django.contrib.auth import views as auth_views  # Vistas de autenticación de Django
from .views import register_view, dashboard_view, listar_productos, crear_producto, eliminar_producto, \
    listar_ventas, eliminar_venta, ver_detalle_venta, listar_categorias, crear_categoria, \
    crear_venta_completa, obtener_precio_producto, generar_boleta_pdf, actualizar_producto,listar_compras,crear_compra,ver_compra, generar_reporte_compras
from . import views 


urlpatterns = [
    # Redirige la raíz a la vista dashboard
    path('', dashboard_view, name='dashboard'),  # Ruta para el dashboard al inicio
    
    # Rutas de autenticación
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', views.custom_logout, name='logout'),  # Ruta personalizada para logout
    path('register/', views.register_view, name='register'),  
  
    # Rutas de productos
    path('productos/', listar_productos, name='listar_productos'),
    path('productos/crear/', crear_producto, name='crear_producto'),
    path('productos/eliminar/<int:id_producto>/', eliminar_producto, name='eliminar_producto'),
    path('productos/actualizar/<int:id_producto>/', actualizar_producto, name='actualizar_producto'),
    
    # Rutas de ventas
    path('ventas/', listar_ventas, name='listar_ventas'),  
    path('ventas/crear-completa/', crear_venta_completa, name='crear_venta_completa'),
    path('ventas/<int:id_venta>/', ver_detalle_venta, name='ver_detalle_venta'),
    path('eliminar_venta/<int:venta_id>/', eliminar_venta, name='eliminar_venta'),
    
    # Rutas de categorías
    path('categorias/', listar_categorias, name='listar_categorias'),
    path('categorias/crear/', crear_categoria, name='crear_categoria'),
    
    # Otras rutas
    path('obtener_precio_producto/<int:producto_id>/', obtener_precio_producto, name='obtener_precio_producto'),
    path('venta/<int:venta_id>/boleta_pdf/', generar_boleta_pdf, name='generar_boleta_pdf'),
    path('reporte_compras/', generar_reporte_compras, name='reporte_compras'),
    path('reporte_ventas/', views.generar_reporte_ventas, name='reporte_ventas'),

    # rutas compras
    
    path('compras/', views.listar_compras, name='listar_compras'),
    path('compras/crear/', views.crear_compra, name='crear_compra'),
    path('compras/<int:compra_id>/', views.ver_compra, name='ver_compra'),    
    path('compras/<int:compra_id>/editar/', views.editar_compra, name='editar_compra'),
    path('compras/<int:compra_id>/eliminar/', views.eliminar_compra, name='eliminar_compra'),
 
    
]
