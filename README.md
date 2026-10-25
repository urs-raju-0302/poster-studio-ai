# Poster Studio AI — Local Edition

A Streamlit-based event poster creator that runs locally on your computer. Customize event content, colors, typography, layout, and optional branding, then export posters as PNG or JPG.

> **Important:** This local edition does not call an online AI service. Event-copy suggestions use built-in templates, and backgrounds are generated with local procedural graphics. No API key or image-generation account is required.

## Features

- 10 poster design templates and multiple event categories
- Built-in event title, tagline, description, call-to-action, date, time, and venue fields
- Locally generated background artwork and decorative effects
- Quick color palettes plus individual background and accent color controls
- Typography controls, font families, text sizes, alignment, positioning, and headline effects
- Optional logo upload and QR-code content
- Three local design variations
- Four poster formats: Instagram post, Instagram story, A4 portrait, and square
- PNG and JPG exports
- Runs locally using Python and Streamlit

## Requirements

- Windows, macOS, or Linux
- Python 3.10 or newer recommended
- Internet access is only needed to install Python packages; poster generation itself does not require an API key or online image model

## Run on Windows (VS Code)

1. Download and extract this repository.
2. Open the extracted folder in VS Code.
3. Open **Terminal → New Terminal**.
4. Create a virtual environment:

   ```powershell
   python -m venv .venv
   ```

5. Activate it:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use Command Prompt and run `.venv\Scripts\activate.bat`, or consult your system's PowerShell execution policy.

6. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

7. Start the app:

   ```powershell
   python -m streamlit run app.py
   ```

8. Open the local address shown in the terminal, usually `http://localhost:8501`.

## Run on macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Basic workflow

1. Choose an event category and design template.
2. Enter or generate suggested event copy using the built-in content options.
3. Adjust the color palette and individual colors.
4. Customize fonts, text sizes, alignment, and positioning.
5. Optionally upload a logo and add QR-code content.
6. Preview a design or create three local variations.
7. Download the final poster as PNG or JPG.

## Project files

```text
Poster_Studio_AI/
├── app.py
├── requirements.txt
├── README.md
├── DEPLOYMENT_GUIDE.md
├── TESTING_CHECKLIST.md
├── .gitignore
└── generated_posters/
    └── .gitkeep
```

## Known limitations

- This version uses local procedural backgrounds and built-in copy suggestions; it does not generate diffusion-model images or call an online text-generation model.
- Text is rendered into the final image rather than stored as independently editable layers.
- Fonts and rendering can vary slightly across operating systems.
- Always review event details, contrast, QR-code readability, and exported dimensions before publishing.

## Privacy

The app does not need an API key. Avoid uploading confidential or sensitive images if you do not want them processed by your local application environment. Do not commit personal logos or generated event assets to a public repository unless you intend to share them.

## License

No license is included. Add a license only after deciding how you want others to use, modify, and redistribute the project.
