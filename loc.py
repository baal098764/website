import streamlit as st
import os
from pathlib import Path
from zipfile import ZipFile
import shutil

# Allowed file extensions
IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
VIDEO_EXTENSIONS = [".mp4", ".avi", ".mov", ".wmv", ".mkv"]

# Directory to save uploaded files
UPLOAD_DIR = "uploaded_files"

# Helper: Check if a file is an image
def is_image(file_path: str) -> bool:
    return any(file_path.lower().endswith(ext) for ext in IMAGE_EXTENSIONS)

# Helper: Check if a file is a video
def is_video(file_path: str) -> bool:
    return any(file_path.lower().endswith(ext) for ext in VIDEO_EXTENSIONS)

# Helper: Save URLs to a text file
def save_to_txt(file_name: str, urls: list):
    with open(file_name, "w") as f:
        f.writelines(f"{url}\n" for url in urls)

# Ensure the upload directory exists
Path(UPLOAD_DIR).mkdir(exist_ok=True)

# Streamlit app
st.title("File Upload to Embed URLs")
st.write("Upload images, videos, or ZIP files to generate embeddable URLs.")

uploaded_files = st.file_uploader(
    "Upload Images/Videos/ZIP Files",
    type=["jpg", "jpeg", "png", "gif", "bmp", "webp", "mp4", "avi", "mov", "wmv", "zip"],
    accept_multiple_files=True
)

# Static directory to serve uploaded files
STATIC_DIR = Path("static")
STATIC_DIR.mkdir(exist_ok=True)

# Hosting URL (replace this with your actual hosting URL)
BASE_URL = "https://embedurls.streamlit.app"  # Update this to match your app's URL

if uploaded_files:
    st.info("Processing uploaded files...")
    image_urls = []
    video_urls = []

    for uploaded_file in uploaded_files:
        file_path = STATIC_DIR / uploaded_file.name

        # Save the file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        if file_path.suffix.lower() == ".zip":
            # Extract ZIP file contents
            with ZipFile(file_path, 'r') as zip_ref:
                extract_dir = STATIC_DIR / f"{file_path.stem}_extracted"
                extract_dir.mkdir(exist_ok=True)
                zip_ref.extractall(extract_dir)

                # Process extracted files
                for root, _, files in os.walk(extract_dir):
                    for file in files:
                        extracted_file_path = Path(root) / file
                        if is_image(str(extracted_file_path)):
                            image_urls.append(f"/static/{extracted_file_path.relative_to(STATIC_DIR)}")
                        elif is_video(str(extracted_file_path)):
                            video_urls.append(f"/static/{extracted_file_path.relative_to(STATIC_DIR)}")
        else:
            if is_image(str(file_path)):
                image_urls.append(f"/static/{file_path.relative_to(STATIC_DIR)}")
            elif is_video(str(file_path)):
                video_urls.append(f"/static/{file_path.relative_to(STATIC_DIR)}")

    # Save URLs to text files (full URLs with hosting base URL)
    save_to_txt(STATIC_DIR / "images.txt", [f"{BASE_URL}{url}" for url in image_urls])
    save_to_txt(STATIC_DIR / "videos.txt", [f"{BASE_URL}{url}" for url in video_urls])

    # Display image URLs
    st.success("Processing complete!")
    st.subheader("Generated Image URLs:")
    for url in image_urls:
        st.image(f"{BASE_URL}{url}", use_container_width=True)

    # Display video URLs
    st.subheader("Generated Video URLs:")
    for url in video_urls:
        st.video(f"{BASE_URL}{url}")
        st.write(f"Video URL: {BASE_URL}{url}")

    # Provide download links for text files
    st.download_button("Download Image URLs (images.txt)", data="\n".join([f"{BASE_URL}{url}" for url in image_urls]), file_name="images.txt")
    st.download_button("Download Video URLs (videos.txt)", data="\n".join([f"{BASE_URL}{url}" for url in video_urls]), file_name="videos.txt")

# Clear Uploads button
if st.button("Clear Uploads"):
    shutil.rmtree(STATIC_DIR)  # Remove the static directory and all files inside it
    STATIC_DIR.mkdir(exist_ok=True)  # Recreate the static directory
    st.info("Static files cleared.")
