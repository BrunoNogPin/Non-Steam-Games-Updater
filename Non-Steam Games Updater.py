import os
import vdf
import requests
import logging
import zlib
import json
from pathlib import Path
import pythoncom
from win32com.shell import shell
import win32com.client
import re

# -------------------- LOG --------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# -------------------- CONFIG --------------------
steamgriddb_api_key = "<Insira sua chave de API do SteamGridDB Aqui>"

# Caminho onde está este script (pasta com jogos)
game_installation_path = Path(os.path.abspath(os.path.dirname(__file__))).resolve()

steam_base_path = Path("C:/Program Files (x86)/Steam")
userdata_dir = steam_base_path / "userdata"

steam_user_data_path = None
if userdata_dir.exists():
    for folder in userdata_dir.iterdir():
        if folder.is_dir():
            steam_user_data_path = folder / "config"
            break

if steam_user_data_path is None:
    logger.error("Steam userdata não encontrada")
    exit(1)

# Pasta grid do Steam (onde as imagens ficam)
grid_folder = steam_user_data_path / "grid"
grid_folder.mkdir(parents=True, exist_ok=True)

logger.info(f"Steam userdata path: {steam_user_data_path}")
logger.info(f"Game installation path: {game_installation_path}")
logger.info(f"Grid path: {grid_folder}")

# -------------------- FUNÇÕES --------------------

def normalize_appid(appid):
    if appid is None:
        return None
    return str(int(appid) & 0xFFFFFFFF)

def read_current_games():
    try:
        return {folder.name.lower(): folder.resolve() for folder in game_installation_path.iterdir() if folder.is_dir()}
    except Exception as e:
        logger.error(f"Erro lendo jogos: {e}")
        return {}

def generate_appid(game_name, exe_path, args=""):
    unique = (str(exe_path) + game_name + args).encode("utf-8")
    legacy_id = zlib.crc32(unique) & 0xFFFFFFFF
    appid = (legacy_id | 0x80000000) & 0xFFFFFFFF
    return str(appid)

def fetch_image_url(game_id, image_type):
    headers = {"Authorization": f"Bearer {steamgriddb_api_key}"}

    endpoint_map = {
        "hero": "heroes",
        "grid": "grids",
        "logo": "logos",
        "icon": "icons",
    }

    try:
        if image_type == "wide":
            for dims in ("920x430", "460x215"):
                url = f"https://www.steamgriddb.com/api/v2/grids/game/{game_id}?dimensions={dims}"
                r = requests.get(url, headers=headers)
                if r.status_code == 200:
                    data = r.json()
                    if data.get("success") and data.get("data"):
                        return data["data"][0].get("url")

            url = f"https://www.steamgriddb.com/api/v2/wideg/game/{game_id}"
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                data = r.json()
                if data.get("success") and data.get("data"):
                    return data["data"][0].get("url")
            return None

        if image_type == "grid":
            for dims in ("600x900",):
                url = f"https://www.steamgriddb.com/api/v2/grids/game/{game_id}?dimensions={dims}"
                r = requests.get(url, headers=headers)
                if r.status_code == 200:
                    data = r.json()
                    if data.get("success") and data.get("data"):
                        return data["data"][0].get("url")

        endpoint = endpoint_map.get(image_type)
        if not endpoint:
            logger.error(f"Tipo de imagem desconhecido: {image_type}")
            return None

        url = f"https://www.steamgriddb.com/api/v2/{endpoint}/game/{game_id}"
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            data = r.json()
            if data.get("success") and data.get("data"):
                return data["data"][0].get("url")

    except Exception as e:
        logger.error(f"Erro ao buscar {image_type}: {e}")

    return None

def download_image(url, path):
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "wb") as f:
                f.write(r.content)
            logger.info(f"Imagem baixada: {path}")
            return True
        else:
            logger.warning(f"Falha download {url} -> status {r.status_code}")
    except Exception as e:
        logger.error(f"Erro baixando imagem: {e}")
    return False

def save_images_if_missing(appid, game_name):
    steam_id = search_game_id(game_name)
    if not steam_id:
        logger.warning(f"Nenhum jogo encontrado no SteamGridDB para '{game_name}'")
        return

    files = {
        "grid": grid_folder / f"{appid}p.png",
        "hero": grid_folder / f"{appid}_hero.png",
        "logo": grid_folder / f"{appid}_logo.png",
        "icon": grid_folder / f"{appid}_icon.png",
        "wide": grid_folder / f"{appid}.png"
    }

    for image_type, path in files.items():
        if not path.exists():
            url = fetch_image_url(steam_id, image_type)
            if url:
                download_image(url, path)
            else:
                logger.debug(f"Nenhuma URL para {image_type} ({game_name})")

def find_largest_exe(root):
    """
    Localiza o executável principal de um jogo dentro de uma pasta.
    Usa heurísticas avançadas baseadas em nome, tamanho e estrutura de diretórios.
    Descarta executáveis genéricos, instaladores, anticheats, crash handlers, depuradores e redistribuíveis.
    """
    root = Path(root)

    # --- Pastas preferidas e ignoradas ---
    preferidas = {"binaries", "bin", "x64", "win64", "win32", "windowsnoeditor"}
    ignorar_pastas = {
        "easyanticheat", "battlEye", "redist", "prereqs", "support", "tools",
        "crashhandler", "crashreporter", "updater", "patch", "modtools", "sdk",
        "uninstall", "installers", "debug", "fpb", "_Redist", "edist"
    }

    # --- Nomes genéricos e utilitários a ignorar ---
    ignorar_nomes_exe = {
        "install", "installhelper", "setup", "setup_x64", "setup_x86",
        "uninstall", "unins000", "unins0001", "uninstaller",
        "vcredist", "dotnetfx", "directx", "dxsetup",
        "updater", "patcher", "launcher_updater",
        "easyanticheat", "eac", "eac_launcher", "battlEye",
        "beservice", "bgsvc", "aced", "unitycrashhandler64",
        "steamhelper", "steamerrorreporter", "cefclient",
        "support", "tools", "crashhandler", "crashreporter",
        "patch", "modtools", "sdk", "debug", "fpb"
    }

    # --- Padrões regex para descartar nomes compostos ou variantes ---
    ignorar_patterns = [
        r'^(setup|install|uninstal|unins|update|patch|vcredist|dxsetup)\b',
        r'unins\d{0,4}',
        r'^dotnetfx',               # dotNetFx setup etc.
        r'easy[\W_]*anticheat',
        r'battle[\W_]*eye',
        r'unity[\W_]*crashhandler',
        r'steam[\W_]*(helper|errorreporter)',
        r'cef(client|helper)',
        r'crash(report|handler)',
        r'(?:_|\b)(debug|fpb|vcredist)(?:_|\b|$)',  # captura sufixos como _debug, _fpb
        r'(?:_|\b)(setup|installer)(?:_|\b|$)'  # pega dotNetFx40_Full_setup.exe
    ]
    ignorar_regex = [re.compile(pat, re.IGNORECASE) for pat in ignorar_patterns]

    nome_jogo = root.name.lower()
    candidatos = []

    for file in root.rglob("*.exe"):
        if not file.is_file():
            continue

        exe_name = file.stem.lower()
        exe_name_full = file.name.lower()
        parts_lower = [p.lower() for p in file.parts]

        # --- Ignorar por pasta ---
        if any(bad in parts_lower for bad in ignorar_pastas):
            logger.debug(f"Ignorando {file} — pasta proibida detectada.")
            continue

        # --- Ignorar por nome literal ---
        if exe_name in ignorar_nomes_exe or exe_name_full in ignorar_nomes_exe:
            logger.debug(f"Ignorando {file} — nome genérico: {exe_name_full}")
            continue

        # --- Ignorar por padrões regex (setup, fpb, debug etc.) ---
        if any(rx.search(exe_name_full) for rx in ignorar_regex):
            logger.debug(f"Ignorando {file} — corresponde a padrão genérico.")
            continue

        # --- Heurística principal ---
        tamanho = file.stat().st_size
        similaridade = 0

        # Nome parecido com o da pasta = jogo provável
        if nome_jogo in exe_name or exe_name in nome_jogo:
            similaridade += 10

        # Dentro de pastas típicas de builds
        if any(pref in parts_lower for pref in preferidas):
            similaridade += 5

        candidatos.append({
            "path": file,
            "size": tamanho,
            "score": similaridade
        })

    if not candidatos:
        logger.debug(f"Nenhum executável válido encontrado em {root}")
        return None

    # Ordena por score e tamanho
    candidatos.sort(key=lambda c: (c["score"], c["size"]), reverse=True)
    melhor = candidatos[0]["path"]
    logger.debug(
        f"Executável selecionado para {root.name}: {melhor} "
        f"(score={candidatos[0]['score']}, size={candidatos[0]['size']})"
    )
    return melhor


def read_lnk_folder(folder):
    lnk_games = {}
    if not folder.exists():
        return lnk_games

    def find_exe_paths_in_bytes(bdata):
        candidates = []
        try:
            s = bdata.decode('utf-16le', errors='ignore')
            matches = re.findall(r'([A-Za-z]:\\\\[^"\r\n]{1,400}\.exe)', s, flags=re.IGNORECASE)
            candidates.extend(matches)
        except Exception:
            pass
        try:
            s2 = bdata.decode('latin-1', errors='ignore')
            matches2 = re.findall(r'([A-Za-z]:\\\\[^"\s]{1,400}\.exe)', s2, flags=re.IGNORECASE)
            candidates.extend(matches2)
        except Exception:
            pass
        try:
            byte_matches = re.findall(rb'([A-Za-z]:\\[^"\x00\r\n]{1,400}\.exe)', bdata, flags=re.IGNORECASE)
            for bm in byte_matches:
                try:
                    candidates.append(bm.decode('utf-8', errors='ignore'))
                except Exception:
                    candidates.append(bm.decode('latin-1', errors='ignore'))
        except Exception:
            pass

        seen = set()
        out = []
        for c in candidates:
            c_norm = c.strip().strip('"').strip()
            if c_norm and c_norm not in seen:
                seen.add(c_norm)
                out.append(c_norm)
        return out

    for entry in folder.glob("*.lnk"):
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(str(entry))
            target = shortcut.Targetpath.strip() if getattr(shortcut, "Targetpath", None) else ""

            found = None
            if target:
                found = target

            if not found:
                with open(entry, "rb") as f:
                    data = f.read()
                for cand in find_exe_paths_in_bytes(data):
                    if Path(cand).exists():
                        found = cand
                        break

            if not found or not Path(found).exists():
                logger.warning(f"Atalho inválido ignorado: {entry}")
                continue

            exe = Path(found).resolve()
            args = (getattr(shortcut, "Arguments", "") or "").strip()
            name = entry.stem
            key = f"{exe}|{args}".lower()

            lnk_games[key] = {"name": name, "exe": exe, "args": args}
        except Exception as e:
            logger.error(f"Erro lendo .lnk {entry}: {e}")
    return lnk_games

def shortcut_exists(shortcuts, exe, args="", startdir=None):
    exe = str(Path(exe).resolve()).lower() if exe else None
    startdir = str(Path(startdir).resolve()).lower() if startdir else None
    args = args.strip().lower()

    for s in shortcuts.get("shortcuts", {}).values():
        try:
            s_exe = Path(s.get("exe", "").strip('"')).resolve()
            s_startdir = Path(s.get("StartDir", "").strip('"')).resolve()
            s_args = s.get("LaunchOptions", "").strip().lower()

            if startdir and str(s_startdir).lower() == startdir:
                return True
            if exe and str(s_exe).lower() == exe and s_args == args:
                return True
        except Exception:
            continue

    return False

def clean_orphan_images(shortcuts):
    valid = set()
    for s in shortcuts.get("shortcuts", {}).values():
        appid = normalize_appid(s.get("appid"))
        if appid:
            valid.add(appid)

    for img in grid_folder.iterdir():
        name = img.stem
        appid = None

        if name.endswith("p"):
            appid = name[:-1]
        elif name.endswith("_hero"):
            appid = name.replace("_hero", "")
        elif name.endswith("_logo"):
            appid = name.replace("_logo", "")
        elif name.endswith("_icon"):
            appid = name.replace("_icon", "")
        elif name.isdigit():
            appid = name

        if appid and appid not in valid:
            logger.info(f"Removendo imagem órfã: {img}")
            try:
                img.unlink()
            except Exception as e:
                logger.error(f"Falha ao remover {img}: {e}")

def search_game_id(game_name):
    headers = {"Authorization": f"Bearer {steamgriddb_api_key}"}
    url = f"https://www.steamgriddb.com/api/v2/search/autocomplete/{game_name}"

    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            data = r.json()
            if data.get("success") and data.get("data"):
                return data["data"][0].get("id")
    except Exception as e:
        logger.error(f"Erro buscando id para '{game_name}': {e}")

    return None

# -------------------- ATUALIZAR SHORTCUTS --------------------

def update_shortcuts(current_games):
    shortcuts_file = steam_user_data_path / "shortcuts.vdf"

    if shortcuts_file.exists():
        with open(shortcuts_file, "rb") as f:
            shortcuts = vdf.binary_load(f)
    else:
        shortcuts = {"shortcuts": {}}

    # --- [NOVO] Remover atalhos com executáveis inexistentes ---
    removed = []
    valid_shortcuts = {}

    for idx, s in shortcuts.get("shortcuts", {}).items():
        exe_path = Path(s.get("exe", "").strip('"'))
        if exe_path.exists():
            valid_shortcuts[str(len(valid_shortcuts))] = s
        else:
            logger.warning(f"Removendo atalho inválido: {s.get('appname')} ({exe_path})")
            removed.append(s.get("appname"))

    shortcuts["shortcuts"] = valid_shortcuts  # reindexar

    if removed:
        logger.info(f"Foram removidos {len(removed)} atalhos inválidos: {', '.join(removed)}")

    # --- [AGORA] Rodar limpeza de imagens órfãs ---
    clean_orphan_images(shortcuts)


    logger.info("Verificando jogos já existentes no Steam...")
    for idx, s in list(shortcuts.get("shortcuts", {}).items()):
        appid = normalize_appid(s.get("appid"))
        s["appid"] = appid
        name = s.get("appname")

        if not appid or not name:
            continue

        imgs = [
            grid_folder / f"{appid}p.png",
            grid_folder / f"{appid}_hero.png",
            grid_folder / f"{appid}_logo.png",
            grid_folder / f"{appid}_icon.png",
            grid_folder / f"{appid}.png"
        ]

        if not all(p.exists() for p in imgs):
            steam_id = search_game_id(name)
            if steam_id:
                save_images_if_missing(appid, name)

        icon_path = grid_folder / f"{appid}_icon.png"
        if icon_path.exists():
            s["icon"] = str(icon_path)

    # --- Continua com a parte de adicionar novos jogos e atalhos ---
    for name, folder in current_games.items():
        exe = find_largest_exe(folder)
        if not exe:
            continue

        if shortcut_exists(shortcuts, exe, startdir=str(folder)):
            logger.debug(f"{name} já existe — ignorando")
            continue

        appid = normalize_appid(generate_appid(name, exe))
        steam_id = search_game_id(name)
        if steam_id:
            save_images_if_missing(appid, name)

        icon_path = grid_folder / f"{appid}_icon.png"
        icon_field = str(icon_path) if icon_path.exists() else ""

        entry = {
            "appid": appid,
            "appname": name,
            "exe": f"\"{exe}\"",
            "StartDir": f"\"{folder}\"",
            "LaunchOptions": "",
            "IsHidden": 0,
            "AllowDesktopConfig": 1,
            "OpenVR": 0,
            "Devkit": 0,
            "DevkitGameID": "",
            "tags": {}
        }

        if icon_field:
            entry["icon"] = icon_field

        shortcuts["shortcuts"][str(len(shortcuts["shortcuts"]))] = entry
        logger.info(f"Adicionado: {name}")

    lnk_folder = game_installation_path / "Atalhos"
    lnk_games = read_lnk_folder(lnk_folder)

    for key, g in lnk_games.items():
        if shortcut_exists(shortcuts, g["exe"], g["args"]):
            logger.debug(f"Atalho já existe — ignorando: {g['name']} {g['args']}")
            continue

        appid = normalize_appid(generate_appid(g["name"], g["exe"], g["args"]))
        steam_id = search_game_id(g["name"])
        if steam_id:
            save_images_if_missing(appid, g["name"])

        icon_path = grid_folder / f"{appid}_icon.png"
        icon_field = str(icon_path) if icon_path.exists() else ""

        entry = {
            "appid": appid,
            "appname": g["name"],
            "exe": f"\"{g['exe']}\"",
            "StartDir": f"\"{g['exe'].parent}\"",
            "LaunchOptions": g["args"],
            "IsHidden": 0,
            "AllowDesktopConfig": 1,
            "OpenVR": 0,
            "Devkit": 0,
            "DevkitGameID": "",
            "tags": {}
        }
        if icon_field:
            entry["icon"] = icon_field

        shortcuts["shortcuts"][str(len(shortcuts["shortcuts"]))] = entry
        logger.info(f"Atalho .lnk adicionado: {g['name']} {g['args']}")

    preview_json = steam_user_data_path / "shortcuts.json"
    with open(preview_json, "w", encoding="utf-8") as f:
        json.dump(shortcuts, f, indent=4, ensure_ascii=False)
    logger.info(f"Preview gerado: {preview_json.resolve()}")

    if input("Gravar no shortcuts.vdf? (sim/não) ").strip().lower() == "sim":
        with open(shortcuts_file, "wb") as f:
            vdf.binary_dump(shortcuts, f)
        logger.info("shortcuts.vdf atualizado")

# -------------------- MAIN --------------------

def main():
    logger.info("Lendo jogos...")
    games = read_current_games()
    update_shortcuts(games)

if __name__ == "__main__":
    main()
