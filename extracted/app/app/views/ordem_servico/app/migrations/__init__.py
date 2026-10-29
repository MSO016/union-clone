#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Modulo de migracoes automaticas do Union OS Manager.
Contem scripts para compatibilidade de banco de dados entre versoes.
"""

from .auto_migrate import run_migration, check_and_migrate_on_startup

__all__ = ['run_migration', 'check_and_migrate_on_startup']
