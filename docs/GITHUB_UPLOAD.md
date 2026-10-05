# Manual GitHub upload

The largest repository file is `artifacts/paired_items.csv` at approximately 56 MB. It is below GitHub's 100 MB per-file limit, but it is too large for GitHub's normal browser uploader. Push the repository with Git from Terminal.

## One-time setup on macOS

Open Terminal and confirm Git is available:

```bash
git --version
```

If Git is missing, macOS will offer to install the Command Line Tools.

## Push this repository

After downloading and extracting `CCD_GitHub_Repository_Ready.zip`:

```bash
cd ~/Downloads/Compliance-Correctness-Decomposition-for-Post-Training-Evaluation
git init
git branch -M main
git add .
git commit -m "Initial release: paper and CCD artifacts"
git remote add origin https://github.com/KingaTshering10/Compliance-Correctness-Decomposition-for-Post-Training-Evaluation.git
git push -u origin main
```

GitHub may open a browser authorization window. If it asks for a password in Terminal, use a GitHub personal access token rather than the account password, or authenticate with the GitHub CLI:

```bash
brew install gh
gh auth login
git push -u origin main
```

## If the GitHub repository is not empty

If the remote repository was created with a README, license, or `.gitignore`, run:

```bash
git pull --rebase origin main
git push -u origin main
```

Resolve any reported conflict before pushing. Do not use a force push unless you intentionally want to overwrite the remote history.

## Before making it public

- Keep the repository private while checking licensing and double-blind anonymity.
- Do not add the identifying GitHub URL to an anonymous manuscript.
- Confirm that benchmark content and venue style files may be redistributed.
- Choose a software/data license only after confirming ownership and redistribution rights.
