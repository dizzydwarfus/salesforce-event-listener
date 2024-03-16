# Use an official Python runtime as a parent image
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Copy the app directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run listener.py when the container launches; '-u' to make sure the output is not buffered
CMD ["python", "-u", "-O", "listener.py"]