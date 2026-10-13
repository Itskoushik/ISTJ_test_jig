from datetime import datetime
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

# ============================================================================
# LOGGER UTILITY
# ============================================================================

class Logger:
    def __init__(self, log_file=None):
        self.log_file = log_file
        self.logs = []

    def log(self, message, error=False):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append({"text": log_entry, "error": error})
        
        if self.log_file:
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(log_entry + "\n")
            except Exception:
                pass


    def get_logs(self):
        return self.logs

    def clear(self):
        self.logs = []
        
def export_logs_to_pdf(log_entries, pdf_path: Path):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
    story = []

    story.append(Paragraph("<b>HAL Connection Logs</b>", styles["Title"]))
    story.append(Spacer(1, 12))
    
    if not log_entries:
        story.append(Paragraph("No logs available.", styles["Normal"]))

    

    for entry in log_entries:
        color = "red" if entry["error"] else "black"
        story.append(
            Paragraph(
                f"<font color='{color}'>{entry['text']}</font>",
                styles["Normal"]
            )
        )
        story.append(Spacer(1, 6))

    doc.build(story)