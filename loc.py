import streamlit as st
import zipfile
import os
import filestack
import asyncio
import aiohttp
from aiohttp import ClientSession

# Initialize Filestack client with your API key
api_key = 'AtZbM0JMeTIip2ONkRgqVz'  # Replace with your actual Filestack API key
client = filestack.Client(api_key)

# Function to extract files from ZIP
def extract_zip(zip_file):
    extracted_files = []
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall("extracted_files")
        extracted_files = zip_ref.namelist()
        print(f"Debug: Extracted files from ZIP: {extracted_files}")
    return extracted_files

# Function to upload files to Filestack (asynchronous)
async def upload_to_filestack(session, file_path):
    print(f"Debug: Uploading file: {file_path}")
    file = {'fileUpload': open(file_path, 'rb')}
    url = 'https://www.filestackapi.com/api/store/S3?key=' + api_key  # Filestack S3 store endpoint

    async with session.post(url, data=file) as response:
        result = await response.json()
        print(f"Debug: File uploaded. URL: {result['url']}")
        return result['url']

# Function to run asynchronous tasks
async def process_uploads(files):
    async with ClientSession() as session:
        tasks = []
        for file_path in files:
            tasks.append(upload_to_filestack(session, file_path))
        image_urls = await asyncio.gather(*tasks)
        return image_urls

# Function to delete all files from Filestack storage
async def delete_all_files():
    url = f'https://www.filestackapi.com/api/async/file?key={api_key}'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            result = await response.json()
            file_ids = [file['handle'] for file in result['files']]  # Extract file handles
            delete_tasks = [session.delete(f'https://www.filestackapi.com/api/file/{file_id}?key={api_key}') for file_id in file_ids]
            await asyncio.gather(*delete_tasks)
            return len(file_ids)

# Streamlit UI
st.title("ZIP File Upload and Media URL Generator")

# Upload ZIP file
zip_file = st.file_uploader("Upload a ZIP file", type=["zip"])

if zip_file is not None:
    print("Debug: ZIP file uploaded.")
    
    # Save the uploaded ZIP file temporarily
    with open("temp.zip", "wb") as temp_file:
        temp_file.write(zip_file.getbuffer())
    print("Debug: ZIP file saved as temp.zip.")

    # Extract the ZIP file
    extracted_files = extract_zip("temp.zip")
    
    # Lists to store image and video URLs
    image_urls = []
    video_urls = []

    # Prepare file paths for upload
    files_to_upload = []

    # Process extracted files and prepare file paths
    for file_name in extracted_files:
        file_path = os.path.join("extracted_files", file_name)
        print(f"Debug: Processing file: {file_name}")
        
        # Check if file is an image or video
        if file_name.lower().endswith(('jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff')):
            print(f"Debug: File is an image: {file_name}")
            files_to_upload.append(file_path)
        elif file_name.lower().endswith(('mp4', 'avi', 'mov', 'mkv', 'webm')):
            print(f"Debug: File is a video: {file_name}")
            video_urls.append(file_path)  # Video URLs will be handled separately or uploaded in future
        else:
            print(f"Debug: Skipping unsupported file type: {file_name}")

    # If there are images, upload them asynchronously
    if files_to_upload:
        print(f"Debug: Uploading {len(files_to_upload)} images asynchronously...")
        image_urls = asyncio.run(process_uploads(files_to_upload))

    # Display image URLs in the Streamlit UI
    if image_urls:
        st.subheader("Image URLs")
        # Display image URLs in a scrollable text box
        st.text_area("Image URLs", "\n".join(image_urls), height=300)

    # Prepare image URL text file
    if image_urls:
        with open("images.txt", "w") as img_file:
            for url in image_urls:
                img_file.write(url + "\n")
        print("Debug: Image URLs saved to images.txt.")

        # Provide download button for the text file
        with open("images.txt", "rb") as img_file:
            st.download_button("Download images.txt", img_file, "images.txt")
            print("Debug: Ready to download images.txt.")

    # Display video URLs (if needed, you can upload videos similarly)
    if video_urls:
        st.subheader("Video URLs")
        # Display video URLs in a scrollable text box
        st.text_area("Video URLs", "\n".join(video_urls), height=300)

    # Prepare video URL text file (if needed)
    if video_urls:
        with open("videos.txt", "w") as vid_file:
            for url in video_urls:
                vid_file.write(url + "\n")
        print("Debug: Video URLs saved to videos.txt.")

        # Provide download button for the text file
        with open("videos.txt", "rb") as vid_file:
            st.download_button("Download videos.txt", vid_file, "videos.txt")
            print("Debug: Ready to download videos.txt.")

# Add a button to delete all media files in Filestack
if st.button("Delete All Media in Filestack"):
    st.write("Deleting all media files from Filestack...")
    deleted_count = asyncio.run(delete_all_files())  # Run the deletion task asynchronously
    st.write(f"Successfully deleted {deleted_count} media files.")
