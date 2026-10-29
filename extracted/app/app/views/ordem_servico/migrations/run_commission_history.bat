@echo off
cd ..
python -m flask db upgrade add_commission_history
pause 