# Directory sorgente
SRC_DIR := .

# Controllo del sistema operativo
HOSTNAME := $(shell hostname)

# Definizione della directory di destinazione in base al sistema operativo
ifeq ($(HOSTNAME), DESKTOP-HFQA6RH) # debian su lenovo
    DEST_DIR := /mnt/c/Users/gianluca/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/FitLoader/
else ifeq ($(HOSTNAME), dell16)
    DEST_DIR := /home/gianluca/.local/share/QGIS/QGIS3/profiles/default/python/plugins/FitLoader  
else
    DEST_DIR := 
endif

# Lista dei file da copiare
FILES := __init__.py  metadata.txt  main.py  README.md  icons fit_files attribute_table.jpg

# Regola predefinita per copiare i file
all: copy_files

# Regola per copiare i file
copy_files:
	cp -r $(addprefix $(SRC_DIR)/, $(FILES)) $(DEST_DIR)
