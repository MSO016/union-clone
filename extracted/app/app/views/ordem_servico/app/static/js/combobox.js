/* =============================================================================
   combobox.js — Combobox visivel para inputs com <datalist>. (B17 / F6a)
   29-05-2026
   =============================================================================
   PROBLEMA: o <datalist> nativo nao mostra uma seta/lista clicavel na maioria
   dos navegadores. O usuario "so consegue escrever" e nao ve as opcoes
   (ex.: tipo de equipamento na OS, fornecedor no produto).

   SOLUCAO (nao destrutiva): para cada <input data-combobox> que tenha um
   <datalist> associado, adiciona:
     - uma seta (caret) clicavel;
     - uma lista suspensa com as opcoes (filtra conforme o usuario digita);
     - selecao por clique preenche o input e dispara input/change.

   GARANTIAS DE SEGURANCA:
     - NAO move o <input> no DOM (preserva validacao/sibling CSS e o contrato
       do formulario: name/required/value intactos).
     - Tudo dentro de try/catch: se algo falhar, o <input> + <datalist> nativo
       continuam funcionando exatamente como antes (degradacao graciosa).
     - Escopo isolado: so atua em inputs marcados com data-combobox.
   ============================================================================= */
(function () {
    'use strict';

    function lerOpcoes(input) {
        var opcoes = [];
        try {
            var listId = input.getAttribute('list');
            var dl = listId ? document.getElementById(listId) : null;
            if (!dl) return opcoes;
            var nodes = dl.querySelectorAll('option');
            for (var i = 0; i < nodes.length; i++) {
                var v = nodes[i].value || nodes[i].textContent || '';
                v = (v || '').trim();
                if (v) opcoes.push(v);
            }
        } catch (e) { /* fallback silencioso */ }
        return opcoes;
    }

    function aprimorar(input) {
        try {
            if (!input || input.__comboPronto) return;
            var opcoes = lerOpcoes(input);
            if (!opcoes.length) return;          // sem opcoes -> mantem input puro
            input.__comboPronto = true;

            var host = input.parentNode;
            if (!host) return;
            host.classList.add('union-combo-host');

            // --- Seta (caret) ---
            var caret = document.createElement('button');
            caret.type = 'button';
            caret.className = 'union-combo-caret';
            caret.tabIndex = -1;
            caret.setAttribute('aria-label', 'Mostrar opcoes');
            caret.innerHTML = '<i class="bi bi-chevron-down"></i>';
            input.insertAdjacentElement('afterend', caret);

            // --- Lista suspensa ---
            var lista = document.createElement('div');
            lista.className = 'union-combo-list';
            lista.style.display = 'none';
            caret.insertAdjacentElement('afterend', lista);

            function posicionar() {
                caret.style.top = input.offsetTop + 'px';
                caret.style.height = input.offsetHeight + 'px';
                caret.style.left = (input.offsetLeft + input.offsetWidth - caret.offsetWidth) + 'px';
                lista.style.top = (input.offsetTop + input.offsetHeight + 2) + 'px';
                lista.style.left = input.offsetLeft + 'px';
                lista.style.width = input.offsetWidth + 'px';
            }

            function selecionar(valor) {
                input.value = valor;
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
                fechar();
                input.focus();
            }

            function renderizar(filtro) {
                lista.innerHTML = '';
                var f = (filtro || '').toLowerCase();
                var mostradas = 0;
                for (var i = 0; i < opcoes.length; i++) {
                    var v = opcoes[i];
                    if (f && v.toLowerCase().indexOf(f) === -1) continue;
                    var item = document.createElement('div');
                    item.className = 'union-combo-item';
                    item.textContent = v;
                    // mousedown (nao click) para nao perder o foco antes de aplicar
                    item.addEventListener('mousedown', (function (valor) {
                        return function (ev) { ev.preventDefault(); selecionar(valor); };
                    })(v));
                    lista.appendChild(item);
                    mostradas++;
                }
                lista.style.display = mostradas ? 'block' : 'none';
            }

            function abrir() {
                posicionar();
                renderizar(input.value);
                lista.style.display = 'block';
            }
            function fechar() {
                lista.style.display = 'none';
            }
            function aberta() { return lista.style.display !== 'none'; }

            caret.addEventListener('click', function (ev) {
                ev.preventDefault();
                if (aberta()) { fechar(); } else { abrir(); }
            });

            input.addEventListener('input', function () {
                if (aberta()) renderizar(input.value);
            });

            input.addEventListener('keydown', function (ev) {
                if (ev.key === 'Escape') fechar();
            });

            document.addEventListener('click', function (ev) {
                if (ev.target !== caret && ev.target !== input &&
                    !caret.contains(ev.target) && !lista.contains(ev.target)) {
                    fechar();
                }
            });

            window.addEventListener('resize', function () {
                if (aberta()) posicionar();
            });

            posicionar();
        } catch (e) {
            // Qualquer falha: o input + datalist nativo seguem funcionais.
            try { console.error('combobox: falha ao aprimorar input, mantendo datalist nativo.', e); } catch (_) {}
        }
    }

    function iniciar() {
        try {
            var inputs = document.querySelectorAll('input[data-combobox]');
            for (var i = 0; i < inputs.length; i++) aprimorar(inputs[i]);
        } catch (e) { /* fallback silencioso */ }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', iniciar);
    } else {
        iniciar();
    }
})();
