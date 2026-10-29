'''
COMPARTILHAMENTO SEGURO DE SOLU├ç├òES
Sistema TECH UNION SOLUTIONS
'''
import pymysql
import hashlib
import json
from datetime import datetime
from typing import (Optional, Dict, Any)
from PyQt5.QtWidgets import QMessageBox
from app.utils._app_cfg import db_config
class CompartilhamentoSeguro:
    '''Classe para compartilhamento seguro de solu├º├Áes'''
    def __init__(self, user_id: int, user_email: str=None):
        self.mysql_config = db_config(ssl={'ca': None}, ssl_verify_cert=False, autocommit=True)
        if isinstance(user_id, str) and '@' in user_id:
            print(f'ÔÜá´©Å user_id recebido como email: {user_id}')
            self.user_id = self._converter_email_para_id(user_id)
            if not user_email:
                user_email = user_id
        else:
            self.user_id = user_id
        self.user_email = user_email
        self._instagram_cache = None
        self._instagram_cache_time = None
        self._cache_expiry = 300
        print(f'­ƒöº CompartilhamentoSeguro inicializado: user_id={self.user_id}, email={self.user_email}')
    def _converter_email_para_id(self, email: str) -> int:
        '''
        Converte email para ID num├®rico consultando a tabela usuarios
        Retorna: ID num├®rico do usu├írio
        '''
        try:
            print(f"­ƒöì Convertendo email '{email}' para ID num├®rico...")
            conn = pymysql.connect(**self.mysql_config)
            cursor = conn.cursor()
            sql = 'SELECT id_usuario FROM usuarios WHERE email = %s LIMIT 1'
            cursor.execute(sql, (email,))
            resultado = cursor.fetchone()
            if resultado:
                user_id = resultado[0]
                print(f"Ô£à Email '{email}' convertido para ID: {user_id}")
                if 'conn' in locals():
                    conn.close()
                    return user_id
                return
        except Exception as e:
            print(f'ÔØî Erro ao converter email para ID: {e}')
            try:
                pass
            finally:
                if 'conn' in locals():
                    conn.close()
            return 1
        try:
            print(f"ÔØî Email '{email}' n├úo encontrado na tabela usuarios")
        except Exception as e:
            print(f'ÔØî Erro ao converter email para ID: {e}')
            try:
                pass
            finally:
                if 'conn' in locals():
                    conn.close()
            return 1
        if 'conn' in locals():
            conn.close()
            return 1
        return 1
    def verificar_instagram_cadastrado(self) -> tuple[bool, Optional[str]]:
        '''
        Verifica se o usu├írio tem Instagram cadastrado no perfil (com cache de seguran├ºa)
        Retorna: (tem_instagram, instagram_username)
        '''
        try:
            import time
            current_time = time.time()
            if self._instagram_cache is not None and self._instagram_cache_time is not None and current_time - self._instagram_cache_time < self._cache_expiry:
                print(f'­ƒöä Instagram: usando cache local - resultado: {self._instagram_cache}')
                if 'conn' in locals():
                    conn.close()
                    return self._instagram_cache
                return
        except Exception as e:
            print(f'ÔØî Erro cr├¡tico ao verificar Instagram: {e}')
            self._instagram_cache = (True, 'erro_dev')
            self._instagram_cache_time = current_time
            try:
                pass
            finally:
                if 'conn' in locals():
                    conn.close()
            return (True, 'erro_dev')
        try:
            print(f'­ƒöì Verificando Instagram para usu├írio ID: {self.user_id}')
        except Exception as e:
            print(f'ÔØî Erro cr├¡tico ao verificar Instagram: {e}')
            self._instagram_cache = (True, 'erro_dev')
            self._instagram_cache_time = current_time
            try:
                pass
            finally:
                if 'conn' in locals():
                    conn.close()
            return (True, 'erro_dev')
        try:
            conn = pymysql.connect(**self.mysql_config)
            cursor = conn.cursor()
            sql = '\n                    SELECT instagram, nome_completo \n                    FROM perfil \n                    WHERE usuario_id = %s \n                    LIMIT 1\n                '
            cursor.execute(sql, (self.user_id,))
            resultado = cursor.fetchone()
            print(f'­ƒöì Resultado da consulta: {resultado}')
            if resultado:
                instagram, nome = resultado
                print(f"­ƒöì Instagram encontrado: '{instagram}', Nome: '{nome}'")
                if instagram and instagram.strip():
                    cache_result = True, instagram.strip()
                    print(f'Ô£à Instagram v├ílido: @{instagram.strip()}')
                else:
                    cache_result = False, nome
                    print(f'ÔØî Instagram vazio ou nulo para usu├írio: {nome}')
            else:
                cache_result = (False, None)
                print(f'ÔØî Usu├írio ID {self.user_id} n├úo encontrado na tabela perfil')
            self._instagram_cache = cache_result
            self._instagram_cache_time = current_time
            print(f'­ƒöä Instagram: resultado salvo no cache: {cache_result}')
        except pymysql.OperationalError as e:
            error_code = e.args[0] if e.args else 0
            if error_code in (1045, 2003, 2005):
                print('ÔÜá´©Å Servidor offline ou acesso negado. Assumindo desenvolvimento local.')
                cache_result = (True, 'teste_dev')
                self._instagram_cache = cache_result
                self._instagram_cache_time = current_time
                try:
                    pass
                except Exception as e:
                    print(f'ÔØî Erro cr├¡tico ao verificar Instagram: {e}')
                    self._instagram_cache = (True, 'erro_dev')
                    self._instagram_cache_time = current_time
                    try:
                        pass
                    finally:
                        if 'conn' in locals():
                            conn.close()
                    return (True, 'erro_dev')
                if 'conn' in locals():
                    conn.close()
                    return cache_result
                return
            raise e
        if 'conn' in locals():
            conn.close()
            return cache_result
    def limpar_cache_instagram(self):
        '''Limpa o cache de Instagram quando o usu├írio atualizou o perfil'''
        self._instagram_cache = None
        self._instagram_cache_time = None
        print('­ƒöä Cache de Instagram limpo - pr├│xima consulta ser├í no servidor')
    def validar_dados_solucao(self, solucao_data: Dict[str, Any]) -> tuple[bool, str]:
        '''
        Valida os dados da solu├º├úo antes do compartilhamento
        Retorna: (├®_v├ílido, mensagem_erro)
        '''
        try:
            campos_obrigatorios = ['marca', 'modelo', 'descricao']
            for campo in campos_obrigatorios:
                if solucao_data.get(campo, '').strip():
                    continue
                return False, f"Campo '{campo}' ├® obrigat├│rio"
            if len(solucao_data['marca']) > 50:
                return (False, 'Marca deve ter no m├íximo 50 caracteres')
            if len(solucao_data['modelo']) > 100:
                return (False, 'Modelo deve ter no m├íximo 100 caracteres')
            if len(solucao_data['descricao']) > 2000:
                return (False, 'Descri├º├úo deve ter no m├íximo 2000 caracteres')
            suspicious_chars = ['<', '>', '&', '"', "'", '\\', '/', '|', '*', '?', ':', ';']
            for field in ('marca', 'modelo', 'descricao'):
                if any((char in solucao_data[field] for char in suspicious_chars)):
                    return False, f"Campo '{field}' cont├®m caracteres n├úo permitidos"
            max_size = 73400320
            for campo_img in ('imagem_blob', 'imagem_1_blob', 'imagem_2_blob', 'diagrama_blob', 'diagrama_2_blob'):
                if not solucao_data.get(campo_img):
                    continue
                if not len(solucao_data[campo_img]) > max_size:
                    continue
                return (False, 'Arquivo muito grande (m├íximo 70MB)')
            return (True, 'Dados v├ílidos')
        except Exception as e:
            return False, f'Erro na valida├º├úo: {str(e)}'
    def gerar_hash_solucao(self, solucao_data: Dict[str, Any]) -> str:
        '''Gera hash ├║nico para a solu├º├úo (evita duplicatas)'''
        try:
            dados_unicos = f'{self.user_id}_{solucao_data['marca']}_{solucao_data['modelo']}_{solucao_data['descricao']}'
            hash_obj = hashlib.md5(dados_unicos.encode('utf-8'))
            return hash_obj.hexdigest()
        except Exception as e:
            print(f'Erro ao gerar hash: {e}')
            return ''
    def verificar_limite_compartilhamentos(self) -> tuple[bool, int]:
        '''
        Verifica se o usu├írio ainda pode compartilhar solu├º├Áes hoje
        Limite: 2 compartilhamentos por dia
        Retorna: (pode_compartilhar, compartilhamentos_hoje)
        '''
        try:
            conn = pymysql.connect(**self.mysql_config)
            cursor = conn.cursor()
            hoje = datetime.now().strftime('%Y-%m-%d')
            sql = '\n                SELECT COUNT(*) FROM minhas_solucoes \n                WHERE id_usuario = %s \n                AND DATE(data_criacao) = %s\n            '
            cursor.execute(sql, (self.user_id, hoje))
            compartilhamentos_hoje = cursor.fetchone()[0]
            limite_diario = 2
            pode_compartilhar = compartilhamentos_hoje < limite_diario
        except Exception as e:
            print(f'Erro ao verificar limite: {e}')
            try:
                pass
            finally:
                if 'conn' in locals():
                    conn.close()
            return (True, 0)
        if 'conn' in locals():
            conn.close()
            return pode_compartilhar, compartilhamentos_hoje
    def compartilhar_solucao(self, solucao_data: Dict[str, Any]) -> tuple[bool, str, int]:
        '''
        Compartilha a solu├º├úo com o servidor de forma segura
        Retorna: (sucesso, mensagem, solution_id)
        '''
        try:
            valido, msg_erro = self.validar_dados_solucao(solucao_data)
            if not valido:
                if 'conn' in locals():
                    conn.close()
                    return False, f'Dados inv├ílidos: {msg_erro}', 0
                return
        except pymysql.Error as e:
            try:
                return False, f'Erro no servidor: {str(e)[:100]}', 0
            finally:
                if 'conn' in locals():
                    conn.close()
            return 'conn'
        except Exception as e:
            try:
                return False, f'Erro inesperado: {str(e)[:100]}', 0
            finally:
                if 'conn' in locals():
                    conn.close()
            return 'conn'
        try:
            print('­ƒöÉ Validando arquivos com seguran├ºa...')
            campos_blob = {'imagem_blob': 'imagem', 'imagem_1_blob': 'imagem', 'imagem_2_blob': 'imagem', 'imagem_3_blob': 'imagem', 'diagrama_blob': 'diagrama', 'diagrama_2_blob': 'diagrama'}
            arquivos_validados = 0
            for campo_nome, tipo_arquivo in campos_blob.items():
                arquivo_data = solucao_data.get(campo_nome)
                if arquivo_data:
                    seguro, msg_seguranca = self.validar_arquivo_seguro(arquivo_data, tipo_arquivo)
                    if not seguro:
                        False, f'Arquivo n├úo seguro: {msg_seguranca}', 0
                        if 'conn' in locals():
                            conn.close()
                            return
                        return
                    arquivos_validados += 1
                    print(f'Ô£à {campo_nome}: {len(arquivo_data):,} bytes - SEGURO')
                else:
                    print(f'ÔÜ¬ {campo_nome}: vazio')
        except pymysql.Error as e:
            try:
                return False, f'Erro no servidor: {str(e)[:100]}', 0
            finally:
                if 'conn' in locals():
                    conn.close()
            return 'conn'
        except Exception as e:
            try:
                return False, f'Erro inesperado: {str(e)[:100]}', 0
            finally:
                if 'conn' in locals():
                    conn.close()
            return 'conn'
        print(f'­ƒöÉ Valida├º├úo conclu├¡da: {arquivos_validados} arquivos aprovados')
        campos_texto = ['marca', 'modelo', 'descricao', 'observacoes']
        for campo in campos_texto:
            if campo not in solucao_data:
                continue
            if solucao_data[campo]:
                import re
                texto_limpo = re.sub('[<>"\\\'\\\\\\|;]', '', str(solucao_data[campo]))
                if campo == 'descricao':
                    texto_limpo = texto_limpo[:2000]
                elif campo == 'observacoes':
                    texto_limpo = texto_limpo[:2000]
                else:
                    texto_limpo = texto_limpo[:255]
                solucao_data[campo] = texto_limpo.strip()
                print(f'­ƒº╣ {campo}: sanitizado ({len(texto_limpo)} chars)')
        try:
            pode_compartilhar, compartilhamentos_hoje = self.verificar_limite_compartilhamentos()
            if not pode_compartilhar:
                if 'conn' in locals():
                    conn.close()
                    return False, f'Limite di├írio atingido ({compartilhamentos_hoje}/2). Tente novamente amanh├ú.', 0
                return
        except:
            print('ÔÜá´©Å N├úo foi poss├¡vel verificar limite. Continuando...')
            compartilhamentos_hoje = 0
        try:
            tem_instagram, instagram_info = self.verificar_instagram_cadastrado()
            if not tem_instagram:
                if 'conn' in locals():
                    conn.close()
                    return (False, 'INSTAGRAM_NECESSARIO', 0)
                return (False, 'INSTAGRAM_NECESSARIO', 0)
        except pymysql.Error as e:
            try:
                return False, f'Erro no servidor: {str(e)[:100]}', 0
            finally:
                if 'conn' in locals():
                    conn.close()
            return 'conn'
        except Exception as e:
            try:
                return False, f'Erro inesperado: {str(e)[:100]}', 0
            finally:
                if 'conn' in locals():
                    conn.close()
            return 'conn'
        try:
            hash_solucao = self.gerar_hash_solucao({'marca': solucao_data['marca'], 'modelo': solucao_data['modelo'], 'descricao': solucao_data['descricao']})
            print('­ƒöù Conectando ao MySQL...')
        except pymysql.Error as e:
            try:
                return False, f'Erro no servidor: {str(e)[:100]}', 0
            finally:
                if 'conn' in locals():
                    conn.close()
            return 'conn'
        except Exception as e:
            try:
                return False, f'Erro inesperado: {str(e)[:100]}', 0
            finally:
                if 'conn' in locals():
                    conn.close()
            return 'conn'
        try:
            conn = pymysql.connect(**self.mysql_config)
            cursor = conn.cursor()
            print('Ô£à Conex├úo MySQL estabelecida!')
            sql_check = '\n                    SELECT COUNT(*) FROM minhas_solucoes \n                    WHERE id_usuario = %s \n                    AND marca = %s \n                    AND modelo = %s \n                    AND descricao = %s\n                '
            cursor.execute(sql_check, (self.user_id, solucao_data['marca'], solucao_data['modelo'], solucao_data['descricao']))
            if cursor.fetchone()[0] > 0:
                if 'conn' in locals():
                    conn.close()
                    return (False, 'Solu├º├úo similar j├í foi compartilhada', 0)
                return (False, 'Solu├º├úo similar j├í foi compartilhada', 0)
        except pymysql.OperationalError as e:
            error_code = e.args[0] if e.args else 0
            if error_code in (1045, 2003, 2005):
                print('ÔÜá´©Å Servidor offline. Simulando compartilhamento para desenvolvimento...')
                try:
                    pass
                except pymysql.Error as e:
                    try:
                        return False, f'Erro no servidor: {str(e)[:100]}', 0
                    finally:
                        if 'conn' in locals():
                            conn.close()
                    return 'conn'
                except Exception as e:
                    try:
                        return False, f'Erro inesperado: {str(e)[:100]}', 0
                    finally:
                        if 'conn' in locals():
                            conn.close()
                    return 'conn'
                if 'conn' in locals():
                    conn.close()
                    return (True, 'Solu├º├úo salva localmente (servidor offline)', 999)
                return (True, 'Solu├º├úo salva localmente (servidor offline)', 999)
            try:
                pass
            except pymysql.Error as e:
                try:
                    return False, f'Erro no servidor: {str(e)[:100]}', 0
                finally:
                    if 'conn' in locals():
                        conn.close()
                return 'conn'
            except Exception as e:
                try:
                    return False, f'Erro inesperado: {str(e)[:100]}', 0
                finally:
                    if 'conn' in locals():
                        conn.close()
                return 'conn'
            if 'conn' in locals():
                conn.close()
                return False, f'Erro de conex├úo: {str(e)[:100]}', 0
            return
        try:
            print('­ƒÆ¥ Inserindo no MySQL...')
            sql_insert = '\n                    INSERT INTO minhas_solucoes (\n                        id_usuario, marca, modelo, descricao, observacoes, \n                        imagem_blob, imagem_1_blob, imagem_2_blob, imagem_3_blob,\n                        diagrama_blob, diagrama_2_blob,\n                        data_criacao, status_aprovacao, publico,\n                        permitir_compartilhamento\n                    ) VALUES (\n                        %s, %s, %s, %s, %s,\n                        %s, %s, %s, %s,\n                        %s, %s,\n                        %s, %s, %s,\n                        %s\n                    )\n                '
            cursor.execute(sql_insert, (self.user_id, solucao_data['marca'], solucao_data['modelo'], solucao_data['descricao'], solucao_data.get('observacoes', ''), solucao_data.get('imagem_blob'), solucao_data.get('imagem_1_blob'), solucao_data.get('imagem_2_blob'), solucao_data.get('imagem_3_blob'), solucao_data.get('diagrama_blob'), solucao_data.get('diagrama_2_blob'), datetime.now(), 'pendente', 1, 1))
            solution_id = cursor.lastrowid
            conn.commit()
            print(f'­ƒÄë Solu├º├úo salva no MySQL com ID: {solution_id}')
            print(f'­ƒôè Imagens enviadas: {sum((1 for campo in campos_blob.keys() if solucao_data.get(campo)))}')
        except pymysql.OperationalError as e:
            error_code = e.args[0] if e.args else 0
            if error_code in (1045, 2003, 2005):
                print('ÔÜá´©Å Servidor offline. Simulando compartilhamento para desenvolvimento...')
                try:
                    pass
                except pymysql.Error as e:
                    try:
                        return False, f'Erro no servidor: {str(e)[:100]}', 0
                    finally:
                        if 'conn' in locals():
                            conn.close()
                    return 'conn'
                except Exception as e:
                    try:
                        return False, f'Erro inesperado: {str(e)[:100]}', 0
                    finally:
                        if 'conn' in locals():
                            conn.close()
                    return 'conn'
                if 'conn' in locals():
                    conn.close()
                    return (True, 'Solu├º├úo salva localmente (servidor offline)', 999)
                return (True, 'Solu├º├úo salva localmente (servidor offline)', 999)
            try:
                pass
            except pymysql.Error as e:
                try:
                    return False, f'Erro no servidor: {str(e)[:100]}', 0
                finally:
                    if 'conn' in locals():
                        conn.close()
                return 'conn'
            except Exception as e:
                try:
                    return False, f'Erro inesperado: {str(e)[:100]}', 0
                finally:
                    if 'conn' in locals():
                        conn.close()
                return 'conn'
            if 'conn' in locals():
                conn.close()
                return False, f'Erro de conex├úo: {str(e)[:100]}', 0
            return
        if 'conn' in locals():
            conn.close()
            return True, f'Solu├º├úo compartilhada com sucesso! ID: {solution_id}', solution_id
    def mostrar_dialogo_instagram(self, parent_widget, nome_usuario: str=None) -> tuple[bool, bool]:
        '''
        Mostra di├ílogo amig├ível para cadastro de Instagram
        Retorna: (abrir_perfil, cancelar_compartilhamento)
        '''
        try:
            msgBox = QMessageBox(parent_widget)
            msgBox.setWindowTitle('­ƒô▒ Instagram Necess├írio - TECH UNION')
            if nome_usuario:
                texto = f'\nOl├í {nome_usuario}!\n\nPara compartilhar suas solu├º├Áes com a comunidade TECH UNION, \nvoc├¬ precisa cadastrar seu Instagram no perfil.\n\nÔ£à Seu reconhecimento ser├í vinculado ao seu Instagram\nÔ£à Outros t├®cnicos poder├úo te encontrar\nÔ£à Suas solu├º├Áes ter├úo mais credibilidade\n\nDeseja abrir o perfil agora para cadastrar?\n                '.strip()
            else:
                texto = '\nPara compartilhar suas solu├º├Áes com a comunidade TECH UNION, \nvoc├¬ precisa cadastrar seu Instagram no perfil.\n\nÔ£à Seu reconhecimento ser├í vinculado ao seu Instagram\nÔ£à Outros t├®cnicos poder├úo te encontrar\nÔ£à Suas solu├º├Áes ter├úo mais credibilidade\n\nDeseja abrir o perfil agora para cadastrar?\n                '.strip()
            msgBox.setText(texto)
            msgBox.setIcon(QMessageBox.Information)
            btn_abrir_perfil = msgBox.addButton('Abrir Perfil', QMessageBox.YesRole)
            btn_cancelar = msgBox.addButton('Cancelar', QMessageBox.NoRole)
            msgBox.setDefaultButton(btn_abrir_perfil)
            msgBox.exec_()
            clicked_button = msgBox.clickedButton()
            if clicked_button == btn_abrir_perfil:
                return (True, False)
        except Exception as e:
            print(f'Erro ao mostrar di├ílogo Instagram: {e}')
        return (False, True)
    def contar_solucoes_aprovadas(self) -> int:
        '''
        Conta quantas solu├º├Áes do usu├írio foram aprovadas no servidor
        Retorna: n├║mero de solu├º├Áes aprovadas
        '''
        try:
            conn = pymysql.connect(**self.mysql_config)
            cursor = conn.cursor()
            sql = "\n                SELECT COUNT(*) FROM minhas_solucoes \n                WHERE id_usuario = %s \n                AND status_aprovacao = 'aprovado'\n            "
            cursor.execute(sql, (self.user_id,))
            total_aprovadas = cursor.fetchone()[0]
        except Exception as e:
            print(f'Erro ao contar solu├º├Áes aprovadas: {e}')
            try:
                pass
            finally:
                if 'conn' in locals():
                    conn.close()
            return 0
        if 'conn' in locals():
            conn.close()
            return total_aprovadas
    def validar_arquivo_seguro(self, arquivo_data: bytes, tipo_arquivo: str) -> tuple[bool, str]:
        '''
        Valida se o arquivo ├® seguro (n├úo cont├®m malware ou execut├íveis)
        Retorna: (├®_seguro, mensagem_erro)
        '''
        try:
            if not arquivo_data:
                return (True, 'Arquivo vazio')
            if len(arquivo_data) > 73400320:
                return (False, 'Arquivo muito grande (m├íximo 70MB)')
            if 'imagem' in tipo_arquivo:
                if arquivo_data.startswith(b'\xff\xd8\xff') or arquivo_data.startswith(b'\x89PNG') or arquivo_data.startswith(b'GIF8') or arquivo_data.startswith(b'RIFF'):
                    pass
                else:
                    return (False, 'Formato de imagem inv├ílido')
            if 'diagrama' in tipo_arquivo and not arquivo_data.startswith(b'%PDF'):
                return (False, 'Formato de PDF inv├ílido')
            executable_signatures = [b'MZ', b'\x7fELF', b'\xfe\xed\xfa\xce', b'\xfe\xed\xfa\xcf']
            if any((arquivo_data.startswith(sig) for sig in executable_signatures)):
                return (False, 'Arquivo execut├ível n├úo permitido')
            script_patterns = [b'<script', b'<?php', b'#!/bin/bash', b'#!/bin/sh', b'javascript:']
            arquivo_lower = arquivo_data.lower()
            if any((pattern in arquivo_lower for pattern in script_patterns)):
                return (False, 'Script embarcado n├úo permitido')
        except Exception as e:
            return False, f'Erro na valida├º├úo: {str(e)}'
        return (True, 'Arquivo seguro')
# WARNING: Decompyle incomplete
