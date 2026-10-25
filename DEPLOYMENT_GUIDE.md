# Deployment Guide

## Option A — Keep running locally (recommended first)

Use the setup steps in `README.md`. This requires no hosting account and keeps the app running on your computer.

## Option B — Publish the code on GitHub

1. Create a new repository on GitHub.
2. Give it a clear name such as `poster-studio-ai`.
3. Do not add a README or `.gitignore` during repository creation if you are uploading this complete project bundle.
4. Open the extracted project folder in VS Code.
5. Review the files and ensure that `.venv`, private assets, and generated posters are not included.
6. Use Source Control in VS Code to initialize Git, commit the files, and publish/push to your repository. Alternatively, use Git commands if Git is installed.
7. Check the repository page and confirm that `app.py`, `requirements.txt`, and `README.md` are present.

Do not publish private event details, personal images, access tokens, or other sensitive files.

## Option C — Host as a Streamlit app

A hosted Streamlit app requires the source code to be available in a GitHub repository and the hosting provider to install the packages listed in `requirements.txt`.

1. Push this project to a GitHub repository.
2. Sign in to Streamlit Community Cloud and create a new app from that repository.
3. Select the repository, branch, and `app.py` as the main file.
4. Deploy and review the application logs if installation or startup fails.
5. Test the hosted app on desktop and mobile widths.

Hosting availability, account requirements, and resource limits may change. This local-only project does not require secrets or API-key configuration. Do not add secrets unless you later introduce a service that needs them.

## Before sharing publicly

- Test all controls and downloads.
- Confirm no personal files or credentials are committed.
- Verify the README accurately describes local procedural backgrounds and built-in copy suggestions.
- Add a license only if you have decided on reuse permissions.
