# Formula 1 Telemetry Dashboard

An upload-ready Python dashboard for exploring Formula 1 telemetry with
[FastF1](https://docs.fastf1.dev/), Streamlit, and Plotly.

The app lets you load a race weekend, select a session, compare one or two
drivers, inspect fastest or selected laps, and view speed, throttle, brake,
gear, track map, and lap table data.

> This is an unofficial fan project and is not associated with Formula 1,
> Formula One Management, the FIA, or any team.

## Features

- Season, Grand Prix, and session selector
- Driver-to-driver telemetry comparison
- Fastest lap or selected lap mode
- Speed, throttle, brake, and gear charts
- Track map overlay
- Lap summary and full lap table
- Local FastF1 cache for faster reloads

## Project Structure

```text
.
|-- app.py
|-- requirements.txt
|-- runtime.txt
|-- README.md
|-- .gitignore
`-- LICENSE
```

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

The first session load may take a little while because FastF1 downloads timing
data. After that, data is cached in the local `cache/` folder.

## Deploy

This project can be deployed on Streamlit Community Cloud:

1. Push these files to a GitHub repository.
2. Open Streamlit Community Cloud.
3. Select your repository.
4. Set the main file path to `app.py`.
5. Deploy.

## Notes

- Live internet access is required the first time a session is loaded.
- Some historical sessions may not include complete telemetry for every driver.
- The dashboard defaults to the 2024 season, but the sidebar supports 2018-2026.
