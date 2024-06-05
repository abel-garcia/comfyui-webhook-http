
import folder_paths
import os
import requests
import json
import base64
from PIL import Image
import numpy as np
from comfy.cli_args import args
from nodes import PngInfo

class ImageSaveNotifier():
    """
    Image Creation Notifier sends an HTTP request to a specified endpoint
    once an image is created by Comfyui.
    """
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""
        self.compress_level = 4
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "filename_prefix": ("STRING", {"default": "ComfyUI"}),
                "webhook_url": ("STRING", {"default": "", "placeholder": "enter webhook URL"}),
            },
            "optional": {
                "metadata": ("STRING", {"default": "", "placeholder": "enter metadata for webhook"}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }
    
    CATEGORY = "image/Save Image & Notify"
    FUNCTION = "save_images_and_notify"
    RETURN_TYPES = ()
    OUTPUT_NODE = True
    
    def save_images_and_notify(
        self, 
        images, 
        filename_prefix="ComfyUI", 
        webhook_url="", 
        metadata="", 
        prompt=None, 
        extra_pnginfo=None,
        ):
        
        metadataFrominput = metadata
        
        # Save Images 
        filename_prefix += self.prefix_append
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0])
        results = list()
        for (batch_number, image) in enumerate(images):
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            metadata = None
            if not args.disable_metadata:
                metadata = PngInfo()
                if prompt is not None:
                    metadata.add_text("prompt", json.dumps(prompt))
                if extra_pnginfo is not None:
                    for x in extra_pnginfo:
                        metadata.add_text(x, json.dumps(extra_pnginfo[x]))

            filename_with_batch_num = filename.replace("%batch_num%", str(batch_number))
            file = f"{filename_with_batch_num}_{counter:05}_.png"
            img.save(os.path.join(full_output_folder, file), pnginfo=metadata, compress_level=self.compress_level)
            results.append({
                "filename": file,
                "subfolder": subfolder,
                "type": self.type
            })
            counter += 1
            
        print(f"Logging result images: {results}")
        
        # Send Notification Via Webhook
        data = {
           "metadata": json.dumps(metadataFrominput),
           "images": json.dumps(results),
        }
        
        response = requests.post(webhook_url, data=data)
        if response.status_code > 300:
            print(f"Failed to send image. Status code: {response.status_code} - {response.text}")
        
        
        return { "ui": { "images": results } }
    

class SDXLRefinerSteps:
    """Convenience node to provide end_at_step and start_at_step to multi-stage diffusion as used by SDXL Base + Refiner"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "steps": ("INT", {"default": 20, "min": 1, "max": 200}),
                "base_ratio": (
                    "FLOAT",
                    {"default": 0.8, "min": 0.0, "max": 1.0, "step": 0.01},
                ),
            }
        }

    RETURN_TYPES: tuple[str, str] = ("INT", "INT")
    RETURN_NAMES: tuple[str, str] = ("steps", "refiner_start")

    FUNCTION: str = "calc_steps"

    CATEGORY: str = "utils"

    def calc_steps(self, steps: int, base_ratio: float) -> tuple[int, int]:
        base_end: int = int(float(steps) * base_ratio)
        return (steps, base_end)
    
NODE_CLASS_MAPPINGS = {
    "SDXLRefinerSteps": SDXLRefinerSteps,
    "ImageSaveNotifier": ImageSaveNotifier,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SDXLRefinerSteps": "Refiner Sampling Steps",
    "ImageSaveNotifier": "Image Save Notifier",
}

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "ImageSaveNotifier",
    "SDXLRefinerSteps",
]