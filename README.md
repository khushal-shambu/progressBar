
# ProgressBar

Personal progress tracker. Inverted health bars per project (boss HP), meta-bar for yearly growth, resets on May 28.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate    # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python main.py

#Project Structure
progressbar/
├── main.py
├── config.py
├── db.py
├── growth.py
├── dialogs.py
├── project_widget.py
├── main_window.py
├── requirements.txt
└── README.md