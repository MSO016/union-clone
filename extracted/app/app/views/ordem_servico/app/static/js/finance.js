// Configuração do Datepicker para o módulo financeiro
$(document).ready(function() {
    console.log('[finance.js] Iniciando configuração do datepicker');
    
    // Função para converter data do formato brasileiro para o formato do banco
    function convertDateToDB(date) {
        if (!date) return '';
        var parts = date.split('/');
        if (parts.length !== 3) return date;
        // Garante que os números tenham dois dígitos
        parts[0] = parts[0].padStart(2, '0');
        parts[1] = parts[1].padStart(2, '0');
        return parts[2] + '-' + parts[1] + '-' + parts[0];
    }

    // Função para converter data do formato do banco para o formato brasileiro
    function convertDateToBR(date) {
        if (!date) return '';
        if (date.includes('/')) return date;
        var parts = date.split('-');
        if (parts.length !== 3) return date;
        // Garante que os números tenham dois dígitos
        parts[1] = parts[1].padStart(2, '0');
        parts[2] = parts[2].padStart(2, '0');
        return parts[2] + '/' + parts[1] + '/' + parts[0];
    }

    // Configuração padrão do datepicker
    const datepickerConfig = {
        format: 'dd/mm/yyyy',
        language: 'pt-BR',
        autoclose: true,
        todayHighlight: true,
        clearBtn: true,
        orientation: 'bottom auto',
        container: 'body',
        startDate: new Date(1900, 0, 1),
        endDate: new Date(2100, 11, 31)
    };

    // Função para inicializar datepicker em um elemento
    function initDatepicker($element) {
        // Remove instância anterior se existir
        if ($element.data('datepicker')) {
            $element.datepicker('destroy');
        }
        
        // Converte data do banco para formato BR ao carregar
        const currentValue = $element.val();
        if (currentValue) {
            $element.val(convertDateToBR(currentValue));
        }
        
        // Inicializa o datepicker
        $element.datepicker(datepickerConfig)
        .on('changeDate', function(e) {
            // Força o formato brasileiro quando a data é selecionada
            if (e.date) {
                const day = String(e.date.getDate()).padStart(2, '0');
                const month = String(e.date.getMonth() + 1).padStart(2, '0');
                const year = e.date.getFullYear();
                $(this).val(`${day}/${month}/${year}`);
            }
        });
        
        // Adiciona máscara de data
        $element.mask('00/00/0000');
        
        // Limpa autocomplete
        $element.attr('autocomplete', 'off');
    }

    // Inicializa todos os datepickers na página
    $('.datepicker').each(function() {
        initDatepicker($(this));
    });

    // Ao submeter qualquer formulário que tenha datepicker
    $('form:has(.datepicker)').on('submit', function(e) {
        let hasError = false;
        
        $('.datepicker', this).each(function() {
            const $input = $(this);
            const brDate = $input.val();
            
            // Valida o formato da data
            if (brDate) {
                const dateRegex = /^(\d{2})\/(\d{2})\/(\d{4})$/;
                if (!dateRegex.test(brDate)) {
                    hasError = true;
                    alert('Data inválida. Use o formato DD/MM/AAAA');
                    $input.focus();
                    return false;
                }
                
                // Converte para formato do banco apenas se não for um formulário de filtro
                if (!$(this).closest('form').attr('id') === 'filterForm') {
                    const dbDate = convertDateToDB(brDate);
                    $input.val(dbDate);
                }
            }
        });
        
        if (hasError) {
            e.preventDefault();
            return false;
        }
    });

    // Correção para posicionamento do calendário
    $('.datepicker').on('show', function(e) {
        const $input = $(this);
        const $picker = $input.data('datepicker').picker;
        const offset = $input.offset();
        const height = $input.outerHeight();
        
        setTimeout(function() {
            $picker.css({
                top: offset.top + height + 2,
                left: offset.left
            });
        }, 0);
    });
}); 