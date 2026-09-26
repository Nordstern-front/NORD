# Konfiguracja: Claude → Higgsfield → Twój Blender

Dzięki tej konfiguracji Claude (uruchomiony **na Twoim komputerze**) generuje modele w Higgsfield
i od razu wstawia je do otwartego Blendera. Sesja Claude w chmurze (claude.ai/code) **nie ma dostępu**
do Twojego komputera, dlatego do tego potrzebny jest lokalny Claude Code albo Claude Desktop.

Całą konfigurację robisz jednorazowo.

## 1. Zainstaluj `uv`
Windows (PowerShell):
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```
macOS: `brew install uv`, Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`.
Potem zamknij terminal i otwórz nowy.

## 2. Zainstaluj dodatek do Blendera
```bash
uvx mcp-for-blender install-addon
```
Potem w Blenderze: **Edit → Preferences → Add-ons** i włącz **Interface: MCP for Blender**.

## 3. Uruchom Claude Code w tym repo
```bash
npm install -g @anthropic-ai/claude-code   # jeśli jeszcze go nie masz
git clone https://github.com/Nordstern-front/NORD && cd NORD
git checkout claude/barber-simulator-vehicle-nl98co
claude
```
Zaloguj się tym samym kontem claude.ai, na którym masz podłączony **Higgsfield**. Konektory
z claude.ai są wtedy dostępne w Claude Code (sprawdzisz to komendą `/mcp`).
Serwer `blender` wczyta się sam z pliku `.mcp.json`. Przy pierwszym uruchomieniu zatwierdź go.

## 4. Połącz z Blenderem
W Blenderze najedź na widok 3D, naciśnij **N**, otwórz zakładkę **MCP for Blender** i kliknij **Start MCP Server**.

## 5. Używaj
Napisz w Claude Code, np.:
> wygeneruj w Higgsfield model fotela fryzjerskiego i wstaw go do Blendera

Instrukcje dla Claude (jak generować, skalować i zapisywać modele) są w `CLAUDE.md`.

## Problemy
- **`spawn uvx ENOENT` / serwer blender się nie łączy**: na Windowsie podmień w `.mcp.json`
  wpis `"command": "uvx", "args": ["mcp-for-blender"]` na
  `"command": "cmd", "args": ["/c", "uvx", "mcp-for-blender"]`.
- **Brak Higgsfield w `/mcp`**: dodaj konektor Higgsfield na claude.ai (Settings → Connectors)
  i uruchom `claude` ponownie.
- **Claude Desktop zamiast Claude Code**: Settings → Developer → Edit Config i wklej zawartość `.mcp.json`.
