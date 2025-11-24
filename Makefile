# Makefile for Windows Environments (cmd.exe / PowerShell)

# Use 'python' as the default interpreter.
# Ensure Python is in your PATH.
PYTHON = python

# The name of the virtual environment directory.
VENV_DIR = .venv

# Define the virtual environment's Python and Pip executables for Windows.
VENV_PYTHON = $(VENV_DIR)/Scripts/python.exe
VENV_PIP = $(VENV_DIR)/Scripts/pip.exe

# Use .PHONY to declare targets that are not actual files.
.PHONY: all help install venv clean run

# The default command, executed when you just run 'make'.
all: help

help:
	@echo "Available commands:"
	@echo.
	@echo  make venv      Creates a Python virtual environment.
	@echo  make install   Installs dependencies from requirements.txt.
	@echo  make run       Runs the main python script.
	@echo  make clean     Removes the virtual environment and cache files.

# This target creates the virtual environment.
# NOTE: All command lines below MUST start with a TAB character, not spaces.
$(VENV_DIR)/Scripts/activate:
	@echo "Creating virtual environment in $(VENV_DIR)..."
	$(PYTHON) -m venv $(VENV_DIR)

# The 'venv' target is a user-friendly alias for creating the environment.
venv: $(VENV_DIR)/Scripts/activate

# The 'install' target depends on 'venv', so the environment will be created automatically.
install: venv
	@echo "Installing packages from requirements.txt..."
	@echo "NOTE: Ensure you have a 'requirements.txt' file."
	$(VENV_PIP) install -r requirements.txt
	@echo "Installation complete."

# A target to run the main script using the virtual environment's Python.
run: venv
	@echo "Running the script..."
	$(VENV_PYTHON) ui.py

# The 'clean' target removes the virtual environment and other temporary files.
# NOTE: We use '%%d' because '%' must be escaped in a Makefile recipe.
clean:
	@echo "Cleaning up project..."
	@if exist $(VENV_DIR) ( rmdir /s /q $(VENV_DIR) )
	@for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
	@echo "Cleanup complete."