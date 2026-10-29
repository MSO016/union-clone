// Função para salvar o checklist
function saveChecklist(event) {
    event.preventDefault();
    
    const form = event.target;
    const items = [];
    
    // Coleta todos os itens do checklist
    document.querySelectorAll('.checklist-item').forEach(itemElement => {
        const description = itemElement.querySelector('[name="description"]')?.value || '';
        const status = itemElement.querySelector('[name="status"]')?.value || 'ok';
        const observations = itemElement.querySelector('[name="observacoes"]')?.value || '';
        
        // Coleta as imagens do item
        const images = [];
        itemElement.querySelectorAll('.image-preview img').forEach(img => {
            if (img.src.startsWith('data:image')) {
                images.push(img.src);
            }
        });
        
        items.push({
            description: description,
            status: status,
            observations: observations,
            images: images
        });
    });
    
    // Adiciona os itens ao formulário
    const itemsInput = document.createElement('input');
    itemsInput.type = 'hidden';
    itemsInput.name = 'items';
    itemsInput.value = JSON.stringify(items);
    form.appendChild(itemsInput);
    
    // Envia o formulário
    form.submit();
}

// Função para adicionar novo item
function addChecklistItem() {
    const template = document.getElementById('item-template');
    const container = document.getElementById('items-container');
    
    if (template && container) {
        const newItem = template.content.cloneNode(true);
        container.appendChild(newItem);
        
        // Inicializa os handlers de imagem para o novo item
        initializeImageHandlers(container.lastElementChild);
    }
}

// Função para remover item
function removeChecklistItem(button) {
    const item = button.closest('.checklist-item');
    if (item) {
        item.remove();
    }
}

// Inicializa handlers de imagem
function initializeImageHandlers(itemElement) {
    const fileInput = itemElement.querySelector('input[type="file"]');
    const preview = itemElement.querySelector('.image-preview');
    
    if (fileInput && preview) {
        fileInput.addEventListener('change', function(e) {
            const files = e.target.files;
            
            for (let file of files) {
                if (file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        const img = document.createElement('img');
                        img.src = e.target.result;
                        img.className = 'img-thumbnail mr-2 mb-2';
                        img.style.maxHeight = '100px';
                        
                        const container = document.createElement('div');
                        container.className = 'position-relative d-inline-block';
                        container.appendChild(img);
                        
                        const removeBtn = document.createElement('button');
                        removeBtn.type = 'button';
                        removeBtn.className = 'btn btn-danger btn-sm position-absolute';
                        removeBtn.style.top = '0';
                        removeBtn.style.right = '0';
                        removeBtn.innerHTML = '&times;';
                        removeBtn.onclick = function() {
                            container.remove();
                        };
                        
                        container.appendChild(removeBtn);
                        preview.appendChild(container);
                    };
                    reader.readAsDataURL(file);
                }
            }
        });
    }
}

// Inicialização quando o documento carrega
document.addEventListener('DOMContentLoaded', function() {
    // Inicializa handlers para itens existentes
    document.querySelectorAll('.checklist-item').forEach(initializeImageHandlers);
    
    // Handler para o formulário
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', saveChecklist);
    }
    
    // Handler para adicionar novo item
    const addButton = document.querySelector('#add-item');
    if (addButton) {
        addButton.addEventListener('click', addChecklistItem);
    }
}); 