#!/bin/bash

python scripts/get_config.py

python odoo/odoo-bin -c .odoorc
