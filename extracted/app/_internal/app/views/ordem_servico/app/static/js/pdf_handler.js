// Função para lidar com PDFs no PyWebview
window.pdfHandler = {
    // Função para salvar PDF
    savePDF: async function(saleId, type) {
        try {
            // Mostra indicador de carregamento
            this.showLoading();
            
            // Faz a requisição para gerar o PDF
            fetch(`/sales/${saleId}/pdf?type=${type}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Erro ao gerar PDF');
                    }
                    return response.blob();
                })
                .then(blob => {
                    // Cria um objeto URL para o blob
                    const url = window.URL.createObjectURL(blob);
                    
                    // Cria um link temporário e clica nele para fazer o download
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `venda_${saleId}.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    
                    // Limpa o objeto URL e remove o link
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    
                    // Mostra mensagem de sucesso
                    this.showAlert('success', type === 'thermal' ? 'PDF enviado para impressão' : 'PDF gerado com sucesso');
                })
                .catch(error => {
                    console.error('Erro:', error);
                    this.showAlert('error', 'Erro ao processar PDF');
                })
                .finally(() => {
                    this.hideLoading();
                });
            
        } catch (error) {
            console.error('Erro:', error);
            this.showAlert('error', 'Erro ao processar PDF');
        }
    },

    // Função para mostrar alerta
    showAlert: function(type, message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
        alertDiv.role = 'alert';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        document.body.appendChild(alertDiv);
        
        // Remove o alerta após 5 segundos
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    },
    
    // Função para mostrar indicador de carregamento
    showLoading: function() {
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'loading-indicator';
        loadingDiv.className = 'position-fixed top-50 start-50 translate-middle';
        loadingDiv.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Carregando...</span>
            </div>
        `;
        document.body.appendChild(loadingDiv);
    },
    
    // Função para esconder indicador de carregamento
    hideLoading: function() {
        const loadingDiv = document.getElementById('loading-indicator');
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }
};
