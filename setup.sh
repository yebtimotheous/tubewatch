   #!/bin/bash

   # Create virtual environment if it doesn't exist
   if [ ! -d "venv" ]; then
       echo "Creating virtual environment..."
       python3 -m venv venv
   else
       echo "Virtual environment already exists."
   fi

   # Activate the virtual environment
   source venv/bin/activate

   # Upgrade pip
   pip install --upgrade pip

   # Install dependencies
   if [ -f "requirements.txt" ]; then
       echo "Installing dependencies from requirements.txt..."
       pip install -r requirements.txt
   else
       echo "requirements.txt not found. Installing default packages..."
       pip install selenium webdriver-manager
   fi

   echo "Setup complete. To activate the virtual environment, run 'source venv/bin/activate'"