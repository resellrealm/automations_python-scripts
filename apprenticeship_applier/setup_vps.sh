#!/bin/bash
# ============================================================
# VPS Setup Script — Apprenticeship Applier
# Run this ONCE on your VPS after cloning the repo
# Usage: bash setup_vps.sh
# ============================================================

set -e
echo "=========================================="
echo "  Apprenticeship Applier — VPS Setup"
echo "=========================================="

# ── 1. System packages ────────────────────────────────────────
echo ""
echo "[1/7] Installing system packages..."
apt-get update -qq
apt-get install -y -qq \
    python3 python3-pip python3-venv \
    xvfb x11vnc \
    novnc websockify \
    git curl wget unzip

# ── 2. Python venv ────────────────────────────────────────────
echo ""
echo "[2/7] Creating Python virtual environment..."
cd "$(dirname "$0")"
python3 -m venv venv
source venv/bin/activate

# ── 3. Python dependencies ────────────────────────────────────
echo ""
echo "[3/7] Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# Also install shared/ deps
pip install --quiet -r ../shared/../email_autoreplier/requirements.txt 2>/dev/null || true

# ── 4. Playwright / Camoufox browsers ─────────────────────────
echo ""
echo "[4/7] Installing browsers..."
playwright install chromium --with-deps
python -m camoufox fetch 2>/dev/null || echo "  (Camoufox fetch skipped — will use Chromium fallback)"

# ── 5. noVNC setup ────────────────────────────────────────────
echo ""
echo "[5/7] Setting up noVNC virtual display..."

# Create systemd service for Xvfb (virtual screen)
cat > /etc/systemd/system/xvfb.service << 'EOF'
[Unit]
Description=Virtual Framebuffer X Server
After=network.target

[Service]
ExecStart=/usr/bin/Xvfb :99 -screen 0 1366x768x24
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for x11vnc (VNC server on top of Xvfb)
cat > /etc/systemd/system/x11vnc.service << 'EOF'
[Unit]
Description=VNC Server for virtual display
After=xvfb.service

[Service]
ExecStart=/usr/bin/x11vnc -display :99 -nopw -listen localhost -xkb -forever -shared
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for noVNC (browser-accessible VNC)
cat > /etc/systemd/system/novnc.service << 'EOF'
[Unit]
Description=noVNC Web Interface
After=x11vnc.service

[Service]
ExecStart=/usr/bin/websockify --web /usr/share/novnc 6080 localhost:5900
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable xvfb x11vnc novnc
systemctl start xvfb x11vnc novnc

echo "  noVNC running at http://YOUR_VPS_IP:6080"

# ── 6. .env file ──────────────────────────────────────────────
echo ""
echo "[6/7] Creating .env file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "  ⚠️  .env created from template."
    echo "  Edit it now: nano .env"
    echo "  Fill in: GOVUK_EMAIL, GOVUK_PASSWORD, TELEGRAM_BOT_TOKEN,"
    echo "           TELEGRAM_CHAT_ID, AI_API_KEY, VPS_IP"
else
    echo "  .env already exists — skipping."
fi

# ── 7. user_profile.json ──────────────────────────────────────
echo ""
echo "[7/7] Checking user profile..."
if [ ! -f user_profile.json ]; then
    echo "  ⚠️  user_profile.json not found — copying template."
    cat > user_profile.json << 'PROFILE'
{
  "personal": {
    "first_name": "George",
    "last_name": "Bailey",
    "email": "georgeb9@protonmail.com",
    "phone": "07304454654",
    "date_of_birth": "01/01/2007",
    "address_line_1": "Your Address Line 1",
    "address_line_2": "",
    "city": "Brighton",
    "postcode": "BN1 1AA",
    "nationality": "British",
    "national_insurance": "",
    "gender": "Male",
    "ethnicity": "Prefer not to say",
    "disability_or_health_condition": false,
    "cv_path": "/root/automation/cv/George_Bailey_CV.pdf"
  },
  "education": [
    {
      "institution": "BHASVIC",
      "dates": "Sept 2024 - Present",
      "qualifications": [
        {"subject": "Mathematics", "grade": "In progress"},
        {"subject": "Business & Law BTEC", "grade": "In progress"}
      ]
    },
    {
      "institution": "Lewes Old Grammar School",
      "dates": "2019 - 2024",
      "qualifications": [
        {"subject": "Mathematics", "grade": "A"},
        {"subject": "English Language", "grade": "B"},
        {"subject": "English Literature", "grade": "B"}
      ]
    }
  ],
  "work_experience": [
    {
      "employer": "Self-employed",
      "job_title": "Private Maths Tutor",
      "dates": "Nov 2023 - Jun 2024",
      "description": "Tutored 3 GCSE students in Mathematics. Developed tailored lesson plans, monitored progress, and delivered consistent results."
    },
    {
      "employer": "Wolfox",
      "job_title": "General Labourer",
      "dates": "Oct 2024 - Present",
      "description": "Assisted with painting, site clean-ups, and materials. Demonstrated reliability and followed safety procedures."
    }
  ],
  "skills": [
    "Strong numerical and analytical skills",
    "Problem-solving and logical thinking",
    "Reliable, organised, detail-oriented",
    "Clear written and verbal communication",
    "Self-motivated, works well independently",
    "Experience with AI tools and app development",
    "Microsoft Office and Google Workspace"
  ],
  "interests": [
    "App development and technology",
    "AI and digital products",
    "Business systems and finance",
    "Gym and fitness"
  ],
  "cv_path": "/root/automation/cv/George_Bailey_CV.pdf"
}
PROFILE
    echo "  user_profile.json created — update date_of_birth, postcode, and cv_path."
else
    echo "  user_profile.json already exists."
fi

# ── Done ──────────────────────────────────────────────────────
echo ""
echo "=========================================="
echo "  Setup complete!"
echo ""
echo "  Next steps:"
echo "  1. nano .env                    ← fill in your credentials"
echo "  2. nano user_profile.json       ← update DOB, postcode"
echo "  3. Upload CV to /root/automation/cv/"
echo ""
echo "  Test run (no real submissions):"
echo "  source venv/bin/activate"
echo "  python main.py --dry-run"
echo ""
echo "  Live run:"
echo "  python main.py --apply"
echo ""
echo "  If CAPTCHA appears, open:"
echo "  http://YOUR_VPS_IP:6080/vnc.html?autoconnect=true"
echo "=========================================="
