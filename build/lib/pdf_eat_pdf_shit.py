"""
This module provides functions to process PDF files for archival purposes.
It includes functionality to check PDF file sizes, convert PDFs to PNG format,
run image processing scripts, and manage file directories for optimized archival.

Functions:
- check_pdf_size: Ensures the PDF file size is under the specified limit.
- setup_directories: Prepares the directory structure for processing.
- convert_pdf_to_png: Converts PDF files to PNG format using pdftoppm.
- run_noteshrink: Applies noteshrink to reduce image file sizes.
- process_pdf: Orchestrates the processing of a single PDF file.
- move_files_and_prepare_download: Moves processed files to their final directories.
- process_archival_directory: Processes each subdirectory in the archival directory.
- pdf_in_upload_to_processes: Manages the processing of all PDFs in an upload directory.
"""
import subprocess
import os
import shutil
import argparse
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from preprocess import process_image


def check_pdf_size(pdf_path):
    """Verify that the PDF file size is less than 2 GB."""
    max_size = 2 * 1024 * 1024 * 1024  # 2 GB in bytes
    if pdf_path.stat().st_size > max_size:
        print(f"PDF larger than 2 GBs: {pdf_path}")
        return False
    return True


def setup_directories(pdf_path, root_archival):
    """Create necessary directories for the archival process."""
    pdf_name = pdf_path.stem
    base_dir = root_archival / pdf_name
    base_dir.mkdir(parents=True, exist_ok=True)
    (base_dir / "original_images").mkdir(exist_ok=True)
    (base_dir / "preprocessed_images").mkdir(exist_ok=True)
    (base_dir / "noteshrinked_images").mkdir(exist_ok=True)
    (base_dir / "noteshrinked_post_processed_images").mkdir(exist_ok=True)
    return base_dir


def convert_pdf_to_png(pdf_path, output_dir, dpi=300):
    """Convert PDF to PNG using pdftoppm."""
    output_prefix = output_dir / pdf_path.stem
    print("Converting PDF to PNG")
    command = ' '.join(["pdftoppm",
                        "-png",
                        "-progress",
                        "-r", str(dpi),
                        str(pdf_path),
                        str(output_prefix)])
    subprocess.run(command, shell=True)


def run_noteshrink(preprocessed_images_dir,conversion_mode,num_colors):
    """Run the noteshrink command on processed images."""
    files = [f for f in os.listdir(preprocessed_images_dir) if f.endswith(
        '.png') and 'ns_page' not in f]
    print(files)
    cmd = ' '.join(['noteshrink',
                    '-w', f'-n {str(num_colors)}', '-b ns_page', '-C', f'--{conversion_mode}', '-o noteshrinked.pdf',
                    '-c "img2pdf --verbose %i --output %o"', ' '.join(files)
                    ])
    subprocess.run(cmd, shell=True, cwd=preprocessed_images_dir)


def process_pdf(pdf_path, root_archival,conversion_mode,num_colors):
    """Process a single PDF file."""
    pdf_path = Path(pdf_path)  # Ensure pdf_path is a Path object
    if not check_pdf_size(pdf_path):
        return
    base_dir = setup_directories(pdf_path, root_archival)
    shutil.move(str(pdf_path), str(base_dir))
    convert_pdf_to_png(base_dir / pdf_path.name, base_dir / "original_images")
    # Process each image in the original_images directory
    original_images_dir = base_dir / "original_images"
    preprocessed_images_dir = base_dir / "preprocessed_images"
    for image_file in original_images_dir.iterdir():
        if image_file.suffix.lower() == '.png':
            process_image(image_file.name, original_images_dir,
                          preprocessed_images_dir)
    run_noteshrink(base_dir / "preprocessed_images",conversion_mode,num_colors)

def move_files_and_prepare_download(subdir):
    """
    Move specific image files to designated directories and
    prepare the download folder using glob for pattern matching.
    """
    # Define the target directories for image files
    noteshrink_post_processed_dir = subdir / "noteshrinked_post_processed_images"
    noteshrinked_images_dir = subdir / "noteshrinked_images"
    noteshrink_post_processed_dir.mkdir(exist_ok=True)
    noteshrinked_images_dir.mkdir(exist_ok=True)

    # Process files in the preprocessed_images directory
    preprocessed_dir = subdir / "preprocessed_images"
    # Using glob to find matching files directly
    for file_path in preprocessed_dir.glob("ns_page*_post.png"):
        shutil.move(str(file_path), str(
            noteshrink_post_processed_dir / file_path.name))
    for file_path in preprocessed_dir.glob("ns_page*.png"):
        shutil.move(str(file_path), str(
            noteshrinked_images_dir / file_path.name))

    # Handle the PDF file moving to a new download directory
    download_dir = subdir.parent.parent / "download"
    download_dir.mkdir(exist_ok=True)
    pdf_target_dir = download_dir / subdir.name
    pdf_target_dir.mkdir(exist_ok=True)

    # Move noteshrinked.pdf if exists
    pdf_file = subdir / "preprocessed_images" / "noteshrinked.pdf"
    if pdf_file.exists():
        shutil.move(str(pdf_file), str(pdf_target_dir / pdf_file.name))

def process_archival_directory(archival_dir_path):
    """
    Process each subdirectory in archival concurrently using multithreading.
    """
    archival_dir = Path(archival_dir_path)
    subdirs = [d for d in archival_dir.iterdir() if d.is_dir()]

    with ThreadPoolExecutor() as executor:
        executor.map(move_files_and_prepare_download, subdirs)

def pdf_in_upload_to_processes(upload_dir, archival_dir,conversion_mode,num_colors):
    """Main function to process all PDFs in the upload directory."""
    root_archival = Path(archival_dir)
    upload_path = Path(upload_dir)
    pdfs = [f for f in upload_path.iterdir() if f.suffix.lower() == '.pdf']

    with ProcessPoolExecutor() as executor:
        results = [executor.submit(
            process_pdf, pdf, root_archival, conversion_mode,num_colors) for pdf in pdfs]
        for future in results:
            future.result()  # This will wait for the process to complete and handle exceptions
    return True

def main():
    '''Currently uses the default behaviour of processing all PDFs in the upload directory.'''
    upload_directory = './upload'
    archival_directory = './archival'
    parser = argparse.ArgumentParser(description='Process and shrink PDF images.')
    parser.add_argument('--conversion_mode', type=str, default='dracula', help='Mode of conversion to be used: dracula (default), dark_mode, invert_hsl, invert_rgb')
    parser.add_argument('--num_colors', type=int, default=8, help='Number of output colors')
    args = parser.parse_args()
    pdf_in_upload_to_processes(upload_directory, archival_directory,args.conversion_mode,args.num_colors)
    process_archival_directory(archival_directory)

if __name__ == '__main__':
    main()
