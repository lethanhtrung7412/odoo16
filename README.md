Gigarion Management System

# Installation

Clone the repo and init all submodules

```
git submodule update --init --recursive
```

Setup

```
python -m venv .venv

.venv\Scripts\activate # activate python on windows

pip install -r odoo/requirements.txt
```

Config

```
cp odoo.conf .odoorc
# Add database configuration and other configuration to the .odoorc file.
```

Run

```
python odoo/odoo-bin -c .odoorc
```


### Docker
```
docker build -t baogiga/gms:10 .
```
