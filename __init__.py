
import folder_paths
import os
import requests
import json
import base64
from PIL import Image
import numpy as np

class ImageCreationNotifier():
    """
    Image Creation Notifier sends an HTTP request to a specified endpoint
    once an image is created by Comfyui.
    """
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        id_field = (
            "STRING",
            {
                "default": "",
                "placeholder": "distinct identifier to organize into output directory",
            },
        )
        return {
            "required": {
                "images": ("IMAGE",),
            },
            "optional": {
                "webhook_url": id_field,
                "metadata": id_field,
            },
        }
    
    CATEGORY = "image/send_notification"
    FUNCTION = "send_notification_webhook"
    RETURN_TYPES = ("IMAGE",)
    
    def send_notification_webhook(
        self,
        images,
        webhook_url="",
        metadata="",
    ):
        
        """
        Sends a notification with the specified parameters to the webhook URL.

        Parameters:
            images (list): A list of images to be processed and sent in the notification.
            webhook_url (str, optional): The URL of the webhook where the notification will be sent.
                Defaults to an empty string.
            metadata (str, optional): Additional metadata to be included in the notification.
                Defaults to an empty string.
        """
        
        output_dir = (
            folder_paths.get_temp_directory()
        )
        (
            full_output_folder,
            filename,
            _,
            _,
            _,
        ) = folder_paths.get_save_image_path("final", output_dir)
        
        single_file_path = os.path.join(full_output_folder, f"{filename}_.png")
        single_image = 255.0 * images[0].cpu().numpy()
        single_image_pil = Image.fromarray(single_image.astype(np.uint8))
        single_image_pil.save(single_file_path)
        
        
        # Open the file in binary mode and read its content before encoding to Base64
        with open(single_file_path, "rb") as file:
            file_content = file.read()
            file_base64 = base64.b64encode(file_content).decode('utf-8')
        
        data = {
           "metadata": json.dumps(metadata),
           "file_base64": file_base64,
        }
        
        response = requests.post(
            webhook_url,
            data=data,
        )
        
        if response.status_code == 204:
            print("Successfully sent image.")
        else:
            print(f"Failed to send image. Status code: {response.status_code} - {response.text}")
            
        return (images,)

NODE_CLASS_MAPPINGS = {
    "ImageCreationNotifier": ImageCreationNotifier,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageCreationNotifier": "Image Creation Notifier",
}

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "ImageCreationNotifier",
]