import os
import numpy as np
from PIL import Image, ImageEnhance

def calc_contrast_and_enhance(input_image, lum_std_dev_lim=30):
    """
    Function to calculate the contrast metrics of an image and enhance the contrast if necessary.

    Parameters:
    - input_image: PIL.Image object - The input image to process.
    - lum_std_dev_lim: int - The threshold for the standard deviation of luminance.
    If the standard deviation is below this threshold, contrast enhancement will be applied.

    Returns:
    - dict: A dictionary containing the processed image object and a flag indicating
    whether enhancement was applied.
    """

    # Load image and convert to grayscale
    original_image_grayscale = input_image.convert("L")
    np_image = np.array(original_image_grayscale, dtype=np.float32)

    # Standard Deviation of Luminance
    std_dev = np.std(np_image)

    # Michelson Contrast
    michelson_contrast = (np.max(np_image) - np.min(np_image)) / (np.max(np_image) + np.min(np_image))

    # RMS Contrast
    rms_contrast = np.sqrt(((np_image - np_image.mean())**2).mean())

    print(f"""Image Metrics are as follows:
          Luminosity Standard Deviation: {std_dev}
          Michelson Contrast: {michelson_contrast}
          RMS Contrast: {rms_contrast}""")

    # Check if the contrast adjustment is needed
    if std_dev < lum_std_dev_lim:
        print(f"""The standard deviation of the image is {std_dev}
              which is less than the Threshold of {lum_std_dev_lim}.""")

        # Create an enhancer object for the image
        enhancer = ImageEnhance.Contrast(input_image)

        # Define the enhancement factor
        # This is a simple heuristic; you might need to adjust the factor
        # based on your specific requirements
        # A factor of 1.0 gives the original image's contrast
        # A factor greater than 1.0 increases the contrast
        # Even though the factor is not aggressive and doesn't meet the targets in one go,
        # I observed that values close to the target seemed to achieve my goal, hence I did not feel
        # like spending multiple iterations for marginal benefits.
        # Adjust the factor as per your requirement
        factor = 1 + (lum_std_dev_lim - std_dev) / lum_std_dev_lim

        # Increase the contrast.
        enhanced_img_output = enhancer.enhance(factor)
        enhanced_img_output_greyscale = enhanced_img_output.convert("L")
        enhanced_img_output_np = np.array(enhanced_img_output_greyscale, dtype=np.float32)

        # Standard Deviation of Luminance
        enhanced_img_output_np_std_dev = np.std(enhanced_img_output_np)

        if enhanced_img_output_np_std_dev >= lum_std_dev_lim:
            print("Enhancement Successful.")
            print(f"New Luminosity Standard Deviation is {enhanced_img_output_np_std_dev}")
        else:
            print("Enhancement Failed!")
            print(f"New Luminosity Standard Deviation is {enhanced_img_output_np_std_dev}")

        return {'img_obj': enhanced_img_output, 'isEnhanced': True}
    return {'img_obj': input_image, 'isEnhanced': False}

def process_image(filename, input_images_directory, output_images_directory):
    """
    Process an image by calculating and enhancing its contrast.

    Parameters:
    - filename: str - The name of the image file.
    - input_images_directory: str - The directory path where the input images are located.
    - output_images_directory: str - The directory path where the processed images will be saved.

    Returns:
    - None
    """

    if filename.endswith('.png'):
        input_image_path = os.path.join(input_images_directory, filename)
        filename_without_extension = os.path.splitext(os.path.basename(input_image_path))[0]
        print(f"Processing image {input_image_path}")

        with Image.open(input_image_path) as input_image:
            return_dict = calc_contrast_and_enhance(input_image, lum_std_dev_lim=30)

            if return_dict['isEnhanced']:
                print(f"Saving Enhanced Image to {output_images_directory}")
                output_filename = f"{filename_without_extension}_enhanced.png"
                output_image_path = os.path.join(output_images_directory, output_filename)
                return_dict['img_obj'].save(output_image_path)
            else:
                print(f"Saving Original Image to {output_images_directory}")
                output_filename = f"{filename_without_extension}_original.png"
                output_image_path = os.path.join(output_images_directory, output_filename)
                return_dict['img_obj'].save(output_image_path)
