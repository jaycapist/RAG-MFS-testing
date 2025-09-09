# RAG-workshop

## Running with Docker

This workshop is containerized using Docker, which simplifies setup and ensures a consistent environment for all participants.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed on your machine.

### Build and Run the Docker Container

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/UH-CI/RAG-workshop.git
    cd RAG-workshop
    ```

2.  **Build the Docker image:**

    ```bash
    docker build -t rag-workshop .
    ```

3.  **Run the Docker container:**

    ```bash
    docker run -p 8888:8888 rag-workshop
    ```

4.  **Access Jupyter Notebook:**

    Open your web browser and navigate to the URL provided in the terminal output. It will look something like this:

    ```
    http://127.0.0.1:8888/?token=...
    ```

    You can then open and run the `main.ipynb` notebook.
