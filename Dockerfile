# Use an official Python runtime as the base image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy the bot code and requirements file into the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port for debugging purposes (optional)
EXPOSE 5000

# The command to run the bot program
CMD ["python", "bot.py"]