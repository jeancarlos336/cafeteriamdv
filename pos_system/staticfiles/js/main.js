// Función para confirmar eliminación
function confirmarEliminacion(ventaId) {
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    const confirmButton = document.getElementById('confirmDelete');
    
    confirmButton.onclick = function() {
        // Redirige para eliminar la venta
        window.location.href = `/eliminar_venta/${ventaId}/`;
    };
    
    modal.show();
}

// Función para la búsqueda en tiempo real
document.querySelector('.search-input').addEventListener('input', function(e) {
    const searchTerm = e.target.value.toLowerCase();
    const rows = document.querySelectorAll('tbody tr');
        
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
   });
// Función para que imprima directo en la impresora 
function imprimirBoleta(ventaId) {
    // Abre una nueva ventana con la boleta
    const boletaWindow = window.open(`/generar_boleta_impresion/${ventaId}/`, '_blank');
    
    // Espera a que la ventana se cargue completamente
    boletaWindow.onload = function() {
        // Imprime directamente
        boletaWindow.print();
        // Cierra la ventana después de imprimir
        boletaWindow.close();
    };
}