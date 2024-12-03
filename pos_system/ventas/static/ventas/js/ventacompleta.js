$(document).ready(function() {
    // Función para imprimir
    $('#btnImprimir').click(function() {
        window.print();  // Abre el cuadro de impresión del navegador
    });
    //formatea cantidades
    function formatNumber(number) {
        return number.toLocaleString('es-CL', { style: 'currency', currency: 'CLP' });
      }

    // Función para actualizar subtotal de una fila
    function updateSubtotal(row) {
        const cantidad = parseFloat($(row).find('[name$="cantidad"]').val()) || 0;
        const precio = Math.round(parseFloat($(row).find('[name$="precio_unitario"]').val()) || 0);
        const subtotal = Math.round(cantidad * precio);
        $(row).find('[name$="sub_total"]').val(subtotal);
        updateTotal();
    }
    

    // Función para actualizar el total general
    function updateTotal() {
        let total = 0;
        $('.detalle').each(function() {
            if (!$(this).find('[name$="DELETE"]').is(':checked')) {
                const subtotal = parseFloat($(this).find('[name$="sub_total"]').val()) || 0;
                total += subtotal;
            }
        });
        $('#total').val(total);
    }
    
    
    // Función para obtener el precio del producto
    function getProductPrice(select) {
        const productoId = $(select).val();
        if (productoId) {
            $.get(`/obtener_precio_producto/${productoId}/`, function(data) {
                const row = $(select).closest('.detalle');
                row.find('[name$="precio_unitario"]').val(Math.round(data.precio)); // Añade Math.round()
                updateSubtotal(row);
            });
        }
    }

    // Event listeners para cambios en productos
    $(document).on('change', '[name$="id_producto"]', function() {
        getProductPrice(this);
    });

    // Event listeners para cambios en cantidad o precio
    $(document).on('change keyup', '[name$="cantidad"], [name$="precio_unitario"]', function() {
        updateSubtotal($(this).closest('.detalle'));
    });

    // Event listener para checkbox de eliminar
    $(document).on('change', '[name$="DELETE"]', function() {
        const row = $(this).closest('.detalle');
        if (this.checked) {
            row.addClass('deleted-row');
        } else {
            row.removeClass('deleted-row');
        }
        updateTotal();
    });

    // Botón para agregar nuevo producto
    $('#agregar-producto').click(function() {
        const totalForms = $('#id_detalleventa_set-TOTAL_FORMS');
        const currentForms = parseInt(totalForms.val());
        const row = $('.detalle:first').clone(true);
        
        // Actualizar índices
        row.find(':input').each(function() {
            let name = $(this).attr('name');
            if (name) {
                name = name.replace('-0-', `-${currentForms}-`);
                $(this).attr('name', name);
                $(this).attr('id', `id_${name}`);
            }
        });
        
        // Limpiar valores
        row.find('input').val('');
        row.find('select').prop('selectedIndex', 0);
        row.removeClass('deleted-row');
        
        // Agregar nueva fila
        $('.detalle:last').after(row);
        totalForms.val(currentForms + 1);
    });

    // Validación del formulario antes de enviar
    $('#ventaForm').on('submit', function(e) {
        let hasProducts = false;
        $('.detalle').each(function() {
            if (!$(this).find('[name$="DELETE"]').is(':checked') && 
                $(this).find('[name$="id_producto"]').val()) {
                hasProducts = true;
                return false;
            }
        });

        if (!hasProducts) {
            e.preventDefault();
            alert('Debe agregar al menos un producto a la venta.');
            return false;
        }

        if (parseFloat($('#total').val()) <= 0) {
            e.preventDefault();
            alert('El total de la venta debe ser mayor que 0.');
            return false;
        }
    });

    // Inicializar cálculos al cargar la página
    $('.detalle').each(function() {
        updateSubtotal(this);
    });
});

    // Función para calcular y mostrar el vuelto
    function updateVuelto() {
        const total = parseFloat($('#total').val().replace(/[^0-9.-]+/g, "")) || 0; // Extrae el número del formato CLP
        const efectivo = parseFloat($('#efectivo').val()) || 0;
        const vuelto = efectivo - total;

        // Actualiza el campo del vuelto
        $('#vuelto').val(vuelto >= 0 ? vuelto.toLocaleString('es-CL', { style: 'currency', currency: 'CLP' }) : 'Insuficiente');
    }

    // Evento para recalcular el vuelto al cambiar el efectivo
    $('#efectivo').on('input', function() {
        updateVuelto();
    });

    // Recalcula el vuelto cada vez que se actualiza el total
    $('#total').on('change', function() {
        updateVuelto();
    });

    // Llama a la función al cargar la página para inicializar valores
    updateVuelto();
