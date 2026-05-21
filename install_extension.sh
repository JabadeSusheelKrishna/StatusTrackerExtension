#!/bin/bash

# ==============================================================================
# STATUS TRACKER - EXTENSION INSTALLER FOR LINUX
# ==============================================================================
# Description: Installs the local unpacked Status Tracker Chrome/Brave extension
#              into a permanent user folder, dynamically updates backend APIs, 
#              and auto-injects the path into the system clipboard.
# Supports:    Google Chrome, Brave, Chromium (Ubuntu, Fedora, Arch, Debian, etc.)
# ==============================================================================

# Styling tokens (Neo-Brutalist high contrast styling)
NC='\033[0m'
BOLD='\033[1m'
CYAN='\033[36m'
GREEN='\033[32m'
YELLOW='\033[33m'
RED='\033[31m'
MAGENTA='\033[35m'
WHITE='\033[37m'
BG_BLACK='\033[40m'

# Get script execution directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
SRC_DIR="$SCRIPT_DIR/extension"
TARGET_DIR="$HOME/.local/share/status-tracker-extension"

# Helper for drawing double horizontal lines
draw_line() {
    echo -e "${CYAN}${BOLD}================================================================${NC}"
}

clear

# Welcome Screen (Neo-Brutalist ASCII Header)
draw_line
echo -e "${CYAN}${BOLD} ██████╗████████╗ █████╗ ████████╗██╗   ██╗███████╗     ${NC}"
echo -e "${CYAN}${BOLD}██╔════╝╚══██╔══╝██╔══██╗╚══██╔══╝██║   ██║██╔════╝     ${NC}"
echo -e "${CYAN}${BOLD}╚█████╗    ██║   ███████║   ██║   ██║   ██║███████╗     ${NC}"
echo -e "${CYAN}${BOLD} ╚═══██╗   ██║   ██╔══██║   ██║   ██║   ██║╚════██║     ${NC}"
echo -e "${CYAN}${BOLD}██████╔╝   ██║   ██║  ██║   ██║   ╚██████╔╝███████║     ${NC}"
echo -e "${CYAN}${BOLD}╚═════╝    ╚═╝   ╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚══════╝     ${NC}"
echo -e "${YELLOW}${BOLD}     [>>>] CHROME & BRAVE EXTENSION INSTALLER [<<<]     ${NC}"
draw_line

# 1. System Compatibility Audits
echo -e "\n${BOLD}[1/5] RUNNING SYSTEM AUDITS...${NC}"

# Ensure source extension folder exists
if [ ! -d "$SRC_DIR" ] || [ ! -f "$SRC_DIR/manifest.json" ]; then
    echo -e "${RED}${BOLD}[ERR]: Source extension files not found at $SRC_DIR/!${NC}"
    echo -e "${YELLOW}Please run this script from the root of the project directory.${NC}"
    exit 1
fi
echo -e "  ${GREEN}✔${NC} Found source extension files."

# Detect browsers
BROWSERS=()
if command -v brave-browser &>/dev/null; then BROWSERS+=("Brave"); fi
if command -v google-chrome &>/dev/null; then BROWSERS+=("Google Chrome"); fi
if command -v google-chrome-stable &>/dev/null; then BROWSERS+=("Google Chrome"); fi
if command -v chromium &>/dev/null; then BROWSERS+=("Chromium"); fi
if command -v chromium-browser &>/dev/null; then BROWSERS+=("Chromium"); fi

if [ ${#BROWSERS[@]} -eq 0 ]; then
    echo -e "  ${YELLOW}⚠ Warning: No installed Chromium-based browsers detected.${NC}"
    echo -e "    (You can still load it manually into any browser of your choice.)"
else
    echo -e "  ${GREEN}✔${NC} Detected installed browsers: ${CYAN}${BROWSERS[*]}${NC}"
fi

# Detect clipboard tool
CLIPBOARD_TOOL=""
if command -v wl-copy &>/dev/null; then
    CLIPBOARD_TOOL="wl-copy (Wayland)"
elif command -v xclip &>/dev/null; then
    CLIPBOARD_TOOL="xclip (X11)"
elif command -v xsel &>/dev/null; then
    CLIPBOARD_TOOL="xsel (X11)"
fi

if [ -n "$CLIPBOARD_TOOL" ]; then
    echo -e "  ${GREEN}✔${NC} Clipboard manager detected: ${CYAN}$CLIPBOARD_TOOL${NC}"
else
    echo -e "  ${YELLOW}⚠ Clipboard manager not found. (Install 'xclip' or 'wl-copy' for auto-copying)${NC}"
fi

# 2. Dynamic Backend Configuration
echo -e "\n${BOLD}[2/5] BACKEND API CONFIGURATION${NC}"
draw_line
echo -e "${WHITE}Where is your FastAPI backend hosted?${NC}"
echo -e "  - If hosted on Render, enter the full URL (e.g. ${CYAN}https://your-app.onrender.com${WHITE})"
echo -e "  - Press ${GREEN}ENTER${WHITE} to default to local server (${CYAN}http://localhost:8000${WHITE})${NC}"
draw_line
read -p "Enter Backend URL: " BACKEND_URL

# Default if empty
if [ -z "$BACKEND_URL" ]; then
    BACKEND_URL="http://localhost:8000"
fi

# Sanitize backend URL
# Ensure scheme exists
if [[ ! "$BACKEND_URL" =~ ^https?:// ]]; then
    BACKEND_URL="https://$BACKEND_URL"
fi
# Strip trailing slash
BACKEND_URL="${BACKEND_URL%/}"

echo -e "\n  👉 Extension will connect to: ${GREEN}${BOLD}$BACKEND_URL${NC}"

# 3. File Deployment
echo -e "\n${BOLD}[3/5] DEPLOYING FILES TO PERMANENT PATH...${NC}"
echo -e "  Destination: ${CYAN}$TARGET_DIR${NC}"

# Safely copy files
mkdir -p "$TARGET_DIR"
cp -rf "$SRC_DIR"/* "$TARGET_DIR/"
echo -e "  ${GREEN}✔${NC} Extension source code cloned to permanent folder."

# 4. Patching Configs with Python3
echo -e "\n${BOLD}[4/5] PATCHING EXTENSION CONFIGURATIONS...${NC}"

# 4a. Patch popup.js Base URL
python3 -c "
import sys, re
try:
    with open('$TARGET_DIR/popup.js', 'r') as f:
        content = f.read()
    new_content = re.sub(
        r'const\s+BASE_URL\s*=\s*[\"\'].*?[\"\']\s*;',
        'const BASE_URL = \"$BACKEND_URL\";',
        content,
        count=1
    )
    with open('$TARGET_DIR/popup.js', 'w') as f:
        f.write(new_content)
    print('  ${GREEN}✔${NC} Patched popup.js with new BASE_URL.')
except Exception as e:
    print(f'  ${RED}✘ Failed to patch popup.js: {e}${NC}', file=sys.stderr)
    sys.exit(1)
"

# 4b. Patch manifest.json Host Permissions
python3 -c "
import sys, json
try:
    with open('$TARGET_DIR/manifest.json', 'r') as f:
        data = json.load(f)
    
    url = '$BACKEND_URL'.rstrip('/')
    permission = f'{url}/*'
    
    if 'host_permissions' not in data:
        data['host_permissions'] = []
    
    if permission not in data['host_permissions']:
        data['host_permissions'].append(permission)
        
    with open('$TARGET_DIR/manifest.json', 'w') as f:
        json.dump(data, f, indent=2)
    print('  ${GREEN}✔${NC} Updated manifest.json permissions for CORS matching.')
except Exception as e:
    print(f'  ${RED}✘ Failed to patch manifest.json: {e}${NC}', file=sys.stderr)
    sys.exit(1)
"

# 5. Clipboard Integration
echo -e "\n${BOLD}[5/5] INJECTING PATH TO SYSTEM CLIPBOARD...${NC}"
COPIED=false
if command -v wl-copy &>/dev/null; then
    echo -n "$TARGET_DIR" | wl-copy &>/dev/null
    COPIED=true
elif command -v xclip &>/dev/null; then
    echo -n "$TARGET_DIR" | xclip -selection clipboard &>/dev/null
    COPIED=true
elif command -v xsel &>/dev/null; then
    echo -n "$TARGET_DIR" | xsel --clipboard --input &>/dev/null
    COPIED=true
fi

if [ "$COPIED" = true ]; then
    echo -e "  ${GREEN}✔ SUCCESS:${NC} Clipboard loaded! Path is ready to paste."
else
    echo -e "  ${YELLOW}⚠ COULD NOT AUTO-COPY:${NC} Please copy the path below manually:"
fi
echo -e "  👉 ${MAGENTA}${BOLD}$TARGET_DIR${NC}"

# Final Neo-Brutalist Setup Guide
echo -e "\n"
draw_line
echo -e "${GREEN}${BOLD}┌────────────────────────────────────────────────────────┐${NC}"
echo -e "${GREEN}${BOLD}│          ★ EXTENSION CONFIGURED & DEPLOYED ★           │${NC}"
echo -e "${GREEN}${BOLD}└────────────────────────────────────────────────────────┘${NC}"
draw_line
echo -e "\n${BOLD}Follow these steps to activate the extension in your browser:${NC}"
echo -e "  1. Open your browser and go to:"
echo -e "     - Chrome / Chromium:  ${CYAN}chrome://extensions${NC}"
echo -e "     - Brave:              ${CYAN}brave://extensions${NC}"
echo -e "  2. Toggle ${YELLOW}${BOLD}Developer mode${NC} ${GREEN}${BOLD}ON${NC} (top-right corner switch)."
echo -e "  3. Click ${CYAN}${BOLD}Load unpacked${NC} (top-left button)."
echo -e "  4. In the folder picker, press ${GREEN}${BOLD}Ctrl+V${NC} (or paste) and select ${CYAN}Open/OK${NC}."
echo -e "     ${WHITE}(The path is already copied to your clipboard!)${NC}\n"
draw_line

# Launch browser if requested
if [ ${#BROWSERS[@]} -gt 0 ]; then
    echo -e "${WHITE}Would you like me to open your browser to the extensions page?${NC}"
    echo -e "  1. Open Brave"
    echo -e "  2. Open Google Chrome"
    echo -e "  3. Open Chromium"
    echo -e "  4. No, I will open it manually"
    read -p "Select option (1-4): " BROWSER_CHOICE
    
    case $BROWSER_CHOICE in
        1)
            echo -e "\nLaunching Brave..."
            brave-browser &>/dev/null &
            ;;
        2)
            echo -e "\nLaunching Google Chrome..."
            google-chrome &>/dev/null &
            ;;
        3)
            echo -e "\nLaunching Chromium..."
            chromium &>/dev/null &
            ;;
        *)
            echo -e "\nExiting installer. Have fun tracking!"
            ;;
    esac
fi

echo -e "\n${GREEN}${BOLD}[SYS]: INSTALLER_EXECUTION_COMPLETE_-_GOOD_LUCK_WITH_TRACKING!${NC}\n"
