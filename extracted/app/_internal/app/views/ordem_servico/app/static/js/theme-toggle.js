/* =============================================================================
   theme-toggle.js — Toggle de tema dark/light/auto (Fase 6)
   =============================================================================
   Adiciona um botao flutuante no canto inferior esquerdo que alterna entre
   DOIS estados (N0 — 29-05-2026, dark 100% opt-in):
     - light  : tema claro (DEFAULT) — ignora prefers-color-scheme: dark
     - dark   : tema escuro (somente quando o usuario escolhe)

   O estado 'auto' (seguir o SO) foi removido porque ligava o dark sozinho
   em maquinas com Windows escuro, quebrando fontes/titulos. Default = light.

   Persiste a escolha em localStorage (chave: union-theme).
   Aplica a classe no <html> antes do DOMContentLoaded para evitar FOUC.

   ATIVACAO: feature flag UI_THEME_TOGGLE=1 (default).
   FALLBACK: se UI_THEME_TOGGLE=0, este script nao e carregado e o
             comportamento prefers-color-scheme dos CSS prevalece.
   ============================================================================= */

(function () {
    'use strict';

    var STORAGE_KEY = 'union-theme';
    // N0 (29-05-2026): tema dark agora e 100% OPT-IN. Default = LIGHT.
    // O estado 'auto' foi removido do ciclo porque seguia o tema do SO
    // (Windows em dark ligava o dark sozinho e quebrava fontes/titulos).
    // O ciclo agora alterna apenas light <-> dark. Valor antigo 'auto'
    // salvo no localStorage e tratado como light (compatibilidade).
    var THEMES = ['light', 'dark'];

    // -------------------- Storage helpers --------------------------------
    function getSavedTheme() {
        try {
            var v = localStorage.getItem(STORAGE_KEY);
            if (v === 'light' || v === 'dark') {
                return v;
            }
            // Ausente ou valor legado ('auto') -> light (default opt-in).
        } catch (e) { /* localStorage indisponivel — fallback para light */ }
        return 'light';
    }

    function saveTheme(theme) {
        try {
            // Apenas 'light'/'dark' sao persistidos. A ausencia da chave
            // tambem significa light (default opt-in), entao nao removemos.
            localStorage.setItem(STORAGE_KEY, theme);
        } catch (e) { /* falha silenciosa */ }
    }

    // -------------------- DOM helpers ------------------------------------
    function applyTheme(theme) {
        var root = document.documentElement;
        root.classList.remove('theme-light', 'theme-dark');
        if (theme === 'light' || theme === 'dark') {
            root.classList.add('theme-' + theme);
        }
    }

    function nextTheme(current) {
        var idx = THEMES.indexOf(current);
        if (idx < 0) idx = 0;
        return THEMES[(idx + 1) % THEMES.length];
    }

    function getIconHtml(theme) {
        if (theme === 'light') return '<i class="bi bi-sun-fill" aria-hidden="true"></i>';
        if (theme === 'dark')  return '<i class="bi bi-moon-stars-fill" aria-hidden="true"></i>';
        return '<i class="bi bi-circle-half" aria-hidden="true"></i>';
    }

    function getModeBadge(theme) {
        if (theme === 'light') return 'L';
        if (theme === 'dark')  return 'D';
        return 'A';
    }

    function getLabel(theme) {
        if (theme === 'light') return 'Tema claro ativo';
        if (theme === 'dark')  return 'Tema escuro ativo';
        return 'Tema automatico (segue o sistema)';
    }

    function updateButtonState(btn, theme) {
        if (!btn) return;
        btn.innerHTML = getIconHtml(theme);
        btn.setAttribute('data-mode', getModeBadge(theme));
        btn.title = getLabel(theme) + ' — clique para alternar';
        btn.setAttribute('aria-label', getLabel(theme));
    }

    // -------------------- Botao flutuante --------------------------------
    function createButton() {
        if (document.getElementById('theme-toggle-btn')) return null;

        var btn = document.createElement('button');
        btn.id = 'theme-toggle-btn';
        btn.className = 'theme-toggle-btn';
        btn.type = 'button';

        btn.addEventListener('click', function (e) {
            e.preventDefault();
            var current = getSavedTheme();
            var next = nextTheme(current);
            saveTheme(next);
            applyTheme(next);
            updateButtonState(btn, next);
        });

        document.body.appendChild(btn);
        updateButtonState(btn, getSavedTheme());
        return btn;
    }

    // -------------------- Inicializacao ----------------------------------
    // Aplica imediatamente (mesmo se DOMContentLoaded ja passou) para
    // evitar FOUC. O script inline no <head> tambem ja faz isso, mas
    // este e fallback defensivo caso o inline nao tenha rodado.
    try { applyTheme(getSavedTheme()); } catch (e) {}

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            createButton();
        });
    } else {
        createButton();
    }

    // -------------------- API publica (debug/testes) ---------------------
    // Expoe como window.UnionTheme para inspecao via DevTools.
    window.UnionTheme = {
        get: getSavedTheme,
        set: function (theme) {
            if (THEMES.indexOf(theme) < 0) return false;
            saveTheme(theme);
            applyTheme(theme);
            var btn = document.getElementById('theme-toggle-btn');
            if (btn) updateButtonState(btn, theme);
            return true;
        },
        cycle: function () {
            this.set(nextTheme(getSavedTheme()));
        }
    };
})();
