$files = @(
    "README.md",
    ".gitignore",
    "HUONGDAN.md",

    "SETUP/README.md",
    "SETUP/environment/lab_config.md",
    "SETUP/installation/install_guide.md",
    "SETUP/checklist/setup_checklist.md",

    "SOURCE/simulator/README.md",
    "SOURCE/tests/README.md",
    "SOURCE/tests/test_checklist.md",

    "SOURCE/config/lab_config.example",
    "SOURCE/config/backup_config.example",

    "THESIS/templates/report_outline.md",
    "THESIS/templates/slide_outline.md",
    "THESIS/runbook/Runbook_template.md",

    "SOFT/README.md",

    "docs/CHECKLIST_YEU_CAU.md",
    "docs/PHAN_CONG_CONG_VIEC.md",
    "docs/KICH_BAN_DEMO.md",
    "docs/NHAT_KY_THUC_NGHIEM.md"
)

foreach ($file in $files) {
    if (!(Test-Path $file)) {
        New-Item -ItemType File -Path $file -Force
    }
}