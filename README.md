# Non-Steam Games Updater

## English

This script automatically scans your local game folders, detects the
main executable of each game, generates consistent Steam app IDs,
creates Steam shortcuts, and downloads artwork (grid, hero, logo, icon,
wide images) from the **SteamGridDB API**.

It works with both normal game folders and `.lnk` shortcuts.

------------------------------------------------------------------------

## 🚀 Features

-   Auto-detects the main EXE inside each game folder\
-   Auto-generates Steam app IDs (compatible with non-Steam shortcuts)\
-   Downloads all artwork types from **SteamGridDB**\
-   Cleans orphaned images\
-   Imports `.lnk` shortcuts\
-   Updates `shortcuts.vdf` and exports a preview (`shortcuts.json`)

------------------------------------------------------------------------

## 📦 Requirements

Install dependencies using:

``` bash
pip install -r requirements.txt
```

Recommended Python version: **Python 3.9+**

------------------------------------------------------------------------

## 🔑 SteamGridDB API Key

To download artwork, you must create an API key at:

➡️ https://www.steamgriddb.com/profile/api

Copy your key and insert it in the script:

``` python
steamgriddb_api_key = "<your API key>"
```

------------------------------------------------------------------------

## 📁 Folder Setup

Place the script inside the folder where your games are located.\
Example:

    C:/Games
     ├─ Game1/
     │   └─ game.exe
     ├─ Game2/
     │   └─ bin/game.exe
     ├─ script.py

Optionally, create a folder:

    C:/Games/Atalhos

Place `.lnk` files inside it for the script to import them.

------------------------------------------------------------------------

## ▶️ How to Use

### 1. Install dependencies

    pip install -r requirements.txt

### 2. Insert your SteamGridDB API key

Edit the script and set:

``` python
steamgriddb_api_key = "YOUR_KEY"
```

### 3. Run the script

    python script.py

### 4. Confirm writing the shortcuts

When prompted:

    Gravar no shortcuts.vdf? (sim/não)

Type `sim` to save changes.

------------------------------------------------------------------------

## ⚠️ Important Notes

-   Steam **must be closed** before writing `shortcuts.vdf`.\
-   Artwork downloads depend on SteamGridDB availability.\
-   Some games may require manual renaming for better search accuracy.\
-   The script automatically locates Steam's userdata folder.

------------------------------------------------------------------------

------------------------------------------------------------------------

# 🇧🇷 Português

Este script escaneia automaticamente suas pastas de jogos, detecta o
executável principal de cada jogo, gera IDs de app do Steam, cria
atalhos e baixa imagens (grid, hero, logo, ícone, wide) pela **API do
SteamGridDB**.

Funciona tanto com pastas de jogos quanto com atalhos `.lnk`.

------------------------------------------------------------------------

## 🚀 Funcionalidades

-   Detecta o arquivo EXE principal de cada jogo\
-   Gera IDs compatíveis com jogos não-Steam\
-   Baixa todas as imagens do SteamGridDB\
-   Remove imagens órfãs\
-   Importa atalhos `.lnk` automaticamente\
-   Atualiza `shortcuts.vdf` e cria `shortcuts.json`

------------------------------------------------------------------------

## 📦 Requisitos

Instale as dependências:

``` bash
pip install -r requirements.txt
```

Python recomendado: **3.9+**

------------------------------------------------------------------------

## 🔑 Chave da API SteamGridDB

Você precisa criar uma chave em:

➡️ https://www.steamgriddb.com/profile/api

Depois, coloque no script:

``` python
steamgriddb_api_key = "<Insira sua chave>"
```

------------------------------------------------------------------------

## 📁 Estrutura de Pastas

Coloque o script na mesma pasta onde ficam seus jogos.\
Exemplo:

    C:/Jogos
     ├─ Jogo1/
     ├─ Jogo2/
     ├─ script.py

Opcional: crie a pasta:

    C:/Jogos/Atalhos

E coloque `.lnk` lá dentro.

------------------------------------------------------------------------

## ▶️ Como Usar

### 1. Instalar dependências

    pip install -r requirements.txt

### 2. Colocar sua chave de API

Edite no script:

``` python
steamgriddb_api_key = "<SUA CHAVE>"
```

### 3. Rodar o script

    python script.py

### 4. Confirmar escrita do arquivo

Digite `sim` quando aparecer:

    Gravar no shortcuts.vdf? (sim/não)

------------------------------------------------------------------------

## ⚠️ Observações Importantes

-   O Steam **deve estar fechado** antes de atualizar o arquivo.\
-   Dependemos da disponibilidade da SteamGridDB.\
-   Alguns jogos podem precisar renomear a pasta para melhor
    reconhecimento.\
-   O script encontra o caminho do Steam automaticamente.
