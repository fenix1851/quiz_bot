# Install python
FROM python:3.8
# Set the working directory to /app
WORKDIR /app
# Copy the current directory contents into the container at /app
ADD . /app

COPY . /app
# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Start the app
RUN ls
CMD ["python3", "main.py"]

