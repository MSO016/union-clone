// Função para inicializar tooltips do Bootstrap
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Função para abrir modal de reabertura
function openReopenModal(orderId) {
    // Limpa o formulário
    document.getElementById('reopenForm').reset();
    
    // Define o ID da OS
    document.getElementById('order_id').value = orderId;
    
    // Abre o modal usando Bootstrap 5
    var modal = new bootstrap.Modal(document.getElementById('reopenModal'));
    modal.show();
}

// Função para reabrir ordem
function reopenOrder() {
    const form = document.getElementById('reopenForm');
    const orderId = document.getElementById('order_id').value;
    
    if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return;
    }
    
    const formData = new FormData(form);
    
    fetch(`/orders/${orderId}/reopen-not-authorized`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Erro na requisição');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            window.location.href = data.redirect_url;
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Erro',
                text: data.message || 'Erro ao reabrir OS'
            });
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        Swal.fire({
            icon: 'error',
            title: 'Erro',
            text: 'Erro ao reabrir OS'
        });
    });
}
