import folder_paths
import os
import requests
from PIL import Image
import numpy as np

class ImageCreationNotifier(Notifier):
    """
    Image Creation Notifier sends an HTTP request to a specified endpoint
    once an image is created by Comfyui.
    """
    
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
                "webhook_url": {
                    "STRING",
                    {
                        "default": "",
                        "placeholder": "distinct identifier to organize into output directory",
                    },
                },
            },
            "optional": {
                "owner": id_field,
                "email": id_field,
            },
            # "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }
    
    CATEGORY = "image_notifier/created"
    FUNCTION = "send_notification_webhook"
    
    def send_notification_webhook(
        self,
        images,
        webhook_url,
        owner="",
        email="",
    ):
        
        """
        Sends a notification with the specified parameters to the webhook URL.

        Parameters:
            webhook_url (str): The URL of the webhook.
            single_file_path (str): The path of the image file to be sent.
            owner (str): The owner parameter to be included in the request body.
            email (str): The email parameter to be included in the request body.
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
        
        response = requests.post(
            webhook_url,
            files={"file": open(single_file_path, "rb")},
            data={"owner":owner, "email":email}
        )
        
        if response.status_code == 204:
            print("Successfully uploaded video to Discord.")
        else:
            print(f"Failed to upload video. Status code: {response.status_code} - {response.text}")
            
        return {"ui": {"images": len(images)}}