from sentence_transformers import SentenceTransformer

# This script is run during the Docker build process.
# It downloads the model, so it's cached in the image layer.
print("Downloading BAAI/bge-m3 model...")
SentenceTransformer("BAAI/bge-m3")
print("Model download complete.")
