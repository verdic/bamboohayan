#!/bin/bash

# Check if Git is installed
if ! [ -x "$(command -v git)" ]; then
  echo "Error: Git is not installed. Please install Git first." >&2
  exit 1
fi

# Step 1: Navigate to the repository directory
echo "Navigating to the repository directory..."
read -p "Enter the path to your Git repository (default: current directory): " repo_path
repo_path=${repo_path:-.}
cd "$repo_path" || { echo "Invalid directory! Exiting."; exit 1; }

# Step 2: Check the status of the repository
echo "Checking repository status..."
git status

# Step 3: Stage all changes
echo "Staging all changes..."
git add .

# Step 4: Commit changes with a message
echo "Committing changes..."
echo "Enter a commit message: "
read commit_message
git commit -m "$commit_message"

# Step 5: Pull the latest changes from the remote repository
echo "Pulling latest changes from the remote repository..."
git pull origin main --no-rebase

# Step 6: Push the changes to the remote repository
echo "Pushing changes to GitHub..."
git push origin main

# Step 7: Verify sync status
echo "Checking final status..."
git status

echo "Workflow complete. Your repository is now synced with GitHub!"

