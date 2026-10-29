from flask import Flask, render_template, abort, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_bootstrap import Bootstrap
from flask_migrate import Migrate
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import config  
import logging
import logging.handlers
from datetime import datetime
import os

# Inicializa as extensões
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bootstrap = Bootstrap()
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})
limiter = Limiter(key_func=get_remote_address)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'

def setup_logging(app):
    # Cria o diretório de logs se não existir
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Configura o handler com o caminho completo do arquivo de log
    log_file = os.path.join(log_dir, 'app.log')
    handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10000000,
        backupCount=5
    )
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [%(module)s:%(lineno)d]'
    )
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

def create_app(config_class=config['default']):  
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Inicializa extensões
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bootstrap.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    
    # Adiciona filtro escapejs
    def escapejs(val):
        if not isinstance(val, str):
            val = str(val)
        val = val.replace('"', '\\"').replace("'", "\\'")
        val = val.replace('\n', '\\n').replace('\r', '\\r')
        return val
    
    app.jinja_env.filters['escapejs'] = escapejs
    
    # Adiciona contexto global para templates
    # Feature flags da modernizacao da UI:
    #   - UI_MODERN_NAVBAR : navbar moderna + dropdowns escopados (Fase 5).
    #     Default '1' (ativado). Fallback: set UI_MODERN_NAVBAR=0 e reiniciar.
    #   - UI_THEME_TOGGLE  : botao flutuante de toggle de tema light/dark/auto (Fase 6).
    #     Default '1' (ativado). Fallback: set UI_THEME_TOGGLE=0 e reiniciar
    #     (volta ao comportamento prefers-color-scheme automatico).
    # Locale + PIX QR Code - 100% defensivo. Se locale_config falhar
    # por qualquer motivo, injeta defaults seguros (BR) e segue funcionando.
    # Fallback: deletar app/locale_config.py NAO quebra o sistema.
    _LOCALE_FALLBACK = {
        'code': 'BR', 'name': 'Brasil',
        'currency_symbol': 'R$', 'currency_code': 'BRL',
        'currency_position': 'before',
        'decimal_separator': ',', 'thousand_separator': '.',
        'tax_id_pf': 'CPF', 'tax_id_pj': 'CNPJ', 'tax_id_label': 'CPF/CNPJ',
        'phone_mask': '(00) 00000-0000', 'zip_label': 'CEP',
    }

    def _format_money_fallback(value, locale=None):
        try:
            return f"R$ {float(value or 0):.2f}".replace('.', ',')
        except Exception:
            return 'R$ 0,00'

    @app.context_processor
    def utility_processor():
        # Tenta importar locale_config; se falhar usa fallback embutido
        try:
            from app.locale_config import (
                get_locale as _get_locale,
                format_money as _format_money,
                get_pix_qrcode_url as _get_pix,
            )
            locale_data = _get_locale()
            format_money_fn = _format_money
            pix_url = _get_pix()
        except Exception:
            locale_data = _LOCALE_FALLBACK
            format_money_fn = _format_money_fallback
            pix_url = None

        return {
            'datetime': datetime,
            'str': str,
            'len': len,
            'enumerate': enumerate,
            'peliculas_enabled': app.config.get('PELICULAS_ENABLED', False),
            'ui_modern_navbar': os.environ.get('UI_MODERN_NAVBAR', '1') == '1',
            'ui_theme_toggle': os.environ.get('UI_THEME_TOGGLE', '1') == '1',
            # Novos (Fase Locale + PIX) - fallback garante BR + None
            'locale': locale_data,
            'format_money': format_money_fn,
            'pix_qrcode_url': pix_url,
        }
    
    # Registra blueprints
    from app.routes import main, auth, users, clients, orders, settings, reports, api, checklists, technicians, finance, inventory, license, calendar
    
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(users.bp)
    app.register_blueprint(clients.bp)
    app.register_blueprint(orders.bp)
    app.register_blueprint(settings.bp)
    app.register_blueprint(reports.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(checklists.bp)
    app.register_blueprint(technicians.bp)
    app.register_blueprint(finance.bp)
    app.register_blueprint(inventory.bp)
    app.register_blueprint(license.bp)
    app.register_blueprint(calendar.bp)
    
    # Películas compatíveis (módulo opcional)
    if app.config.get('PELICULAS_ENABLED'):
        try:
            from app.routes import peliculas
            app.register_blueprint(peliculas.bp)
            app.logger.info('Módulo de películas habilitado')
        except Exception:
            app.config['PELICULAS_ENABLED'] = False
    
    setup_logging(app)
    
    # =========================================================================
    # MIGRACAO AUTOMATICA - Corrige estrutura do banco de dados
    # =========================================================================
    # Executa silenciosamente antes de qualquer operacao para garantir 
    # compatibilidade com bancos de dados de versoes anteriores.
    # O usuario NAO ve nenhuma mensagem - processo 100% transparente.
    try:
        from app.migrations.auto_migrate import check_and_migrate_on_startup
        check_and_migrate_on_startup(app)
    except Exception:
        pass  # Silencia completamente - nao impacta o usuario
    
    # Inicializa o gerenciador de backup
    from app.utils.backup_manager import init_backup_manager
    init_backup_manager(app)
    
    @app.before_request
    def check_license():
        # =====================================================================
        # 🔧 MODO INTEGRADO - TECH UNION SOLUTIONS
        # =====================================================================
        # Quando o Union OS Manager roda como módulo interno do Tech Union
        # Solutions, o licenciamento é controlado pelo app principal (Keygen.sh).
        # 
        # MODIFICADO EM: 2025-12-25
        # MOTIVO: Integração com Tech Union Solutions
        # ORIGINAL: Linhas 130-135 verificavam licença local e bloqueavam acesso
        # AGORA: Apenas verifica autenticação (login), licença desativada
        # 
        # PARA RESTAURAR: Descomentar linhas marcadas com [LICENCIAMENTO]
        # =====================================================================
        
        # Ignora verificação para arquivos estáticos
        if request.endpoint and 'static' in request.endpoint:
            return
            
        # Permite acesso à tela de login
        if not current_user.is_authenticated:
            allowed_endpoints = ['auth.login', 'static']
            if request.endpoint not in allowed_endpoints:
                return redirect(url_for('auth.login'))
            return
            
        # Desenvolvedores têm acesso total
        if current_user.role == 'developer':
            return
            
        # Rotas que sempre devem ser acessíveis
        allowed_endpoints = [
            'license.status',
            'license.welcome',
            'license.expired',
            'auth.logout',
            'static'
        ]
        
        if request.endpoint in allowed_endpoints:
            return
            
        # =====================================================================
        # [LICENCIAMENTO DESATIVADO] - Código original comentado abaixo
        # =====================================================================
        # Usuário autenticado tem acesso total (licença controlada pelo Tech Union)
        return  # <-- BYPASS: Acesso liberado após login
        
        # [LICENCIAMENTO] Código original - descomente para restaurar:
        # from app.utils.system import check_license
        # license = check_license()
        # if not license or not license.is_active or license.is_expired:
        #     if request.endpoint != 'license.welcome':
        #         return redirect(url_for('license.welcome'))
    
    # Configura logs financeiros
    app.financial_logger = logging.getLogger('financial')
    if not app.financial_logger.handlers:
        fh = logging.FileHandler('logs/financial.log')
        fh.setFormatter(logging.Formatter('%(asctime)s - %(message)s [by %(user)s]'))
        app.financial_logger.addHandler(fh)
        app.financial_logger.setLevel(logging.INFO)
    
    return app