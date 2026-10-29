// Funções de utilidade
function formatarMoeda(valor) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(valor);
}

function formatarData(data) {
    return new Date(data).toLocaleDateString('pt-BR');
}

// Funções de validação
function validarFormulario(form) {
    let campos = form.querySelectorAll('[required]');
    let valido = true;
    
    campos.forEach(campo => {
        if (!campo.value) {
            campo.classList.add('is-invalid');
            valido = false;
        } else {
            campo.classList.remove('is-invalid');
        }
    });
    
    return valido;
}

// Funções de manipulação de DOM
function mostrarAlerta(mensagem, tipo = 'success') {
    const alertaDiv = document.createElement('div');
    alertaDiv.className = `alert alert-${tipo} alert-dismissible fade show`;
    alertaDiv.role = 'alert';
    alertaDiv.innerHTML = `
        ${mensagem}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>
    `;
    
    document.querySelector('.container').insertAdjacentElement('afterbegin', alertaDiv);
    
    setTimeout(() => {
        alertaDiv.remove();
    }, 5000);
}

// Funções de interação com API
async function fazerRequisicao(url, opcoes = {}) {
    try {
        const response = await fetch(url, {
            ...opcoes,
            headers: {
                'Content-Type': 'application/json',
                ...opcoes.headers
            }
        });
        
        if (!response.ok) {
            throw new Error(`Erro HTTP: ${response.status}`);
        }
        
        return await response.json();
    } catch (erro) {
        console.error('Erro na requisição:', erro);
        mostrarAlerta('Erro ao processar a requisição', 'danger');
        throw erro;
    }
}

// Funções específicas do sistema
function confirmarExclusao(id, tipo) {
    if (confirm(`Tem certeza que deseja excluir este(a) ${tipo}?`)) {
        return fazerRequisicao(`/api/${tipo}/${id}`, {
            method: 'DELETE'
        });
    }
}

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    // Inicializa tooltips do Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Inicializa máscaras de input
    const mascaras = {
        'telefone': '(00) 00000-0000',
        'cpf': '000.000.000-00',
        'cnpj': '00.000.000/0000-00',
        'cep': '00000-000'
    };
    
    document.querySelectorAll('[data-mascara]').forEach(input => {
        const tipo = input.dataset.mascara;
        if (mascaras[tipo]) {
            IMask(input, {
                mask: mascaras[tipo]
            });
        }
    });
}); 