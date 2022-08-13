# Copyright Niantic 2019. Patent Pending. All rights reserved.
#
# This software is licensed under the terms of the Monodepth2 licence
# which allows for non-commercial use only, the full terms of which are made
# available in the LICENSE file.

from __future__ import absolute_import, division, print_function

import os
import sys
import glob
import argparse
import numpy as np
import PIL.Image as pil
import matplotlib as mpl
import matplotlib.cm as cm
import cv2 

import torch
from torchvision import transforms, datasets

import monodepth2.networks as networks
from monodepth2.layers import disp_to_depth
from monodepth2.utils import download_model_if_doesnt_exist
from monodepth2.evaluate_depth import STEREO_SCALE_FACTOR

def run_image(images):
    
    """Function to predict for a single image or folder of images
    """
    model_name = "mono_640x192"
 
    if torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")

  
    download_model_if_doesnt_exist(model_name)
    model_path = os.path.join("models", model_name)
    print("-> Loading model from ", model_path)
    encoder_path = os.path.join(model_path, "encoder.pth")
    depth_decoder_path = os.path.join(model_path, "depth.pth")

    # LOADING PRETRAINED MODEL
    print("   Loading pretrained encoder")
    encoder = networks.ResnetEncoder(18, False)
    loaded_dict_enc = torch.load(encoder_path, map_location=device)

    # extract the height and width of image that this model was trained with
    feed_height = loaded_dict_enc['height']
    feed_width = loaded_dict_enc['width']
    filtered_dict_enc = {k: v for k, v in loaded_dict_enc.items() if k in encoder.state_dict()}
    encoder.load_state_dict(filtered_dict_enc)
    encoder.to(device)
    encoder.eval()

    print("   Loading pretrained decoder")
    depth_decoder = networks.DepthDecoder(
        num_ch_enc=encoder.num_ch_enc, scales=range(4))

    loaded_dict = torch.load(depth_decoder_path, map_location=device)
    depth_decoder.load_state_dict(loaded_dict)

    depth_decoder.to(device)
    depth_decoder.eval()

    # FINDING INPUT IMAGES
    # if os.path.isfile(image_path):
    #     # Only testing on a single image
    #     paths = [image_path]
    #     output_directory = os.path.dirname(image_path)
    # elif os.path.isdir(image_path):
    #     # Searching folder for images
    #     paths = glob.glob(os.path.join(image_path, '*.{}'.format("jpg")))
    #     output_directory = image_path
    # else:
    #     raise Exception("Can not find image_path: {}".format(image_path))

    # print("-> Predicting on {:d} test images".format(len(paths)))

    # PREDICTING ON EACH IMAGE IN TURN
    results = []
    with torch.no_grad():
        # Load image and preprocess
        for image in images: 
            img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            input_image = pil.fromarray(img)
            original_width, original_height = input_image.size
            input_image = input_image.resize((feed_width, feed_height), pil.LANCZOS)
            input_image = transforms.ToTensor()(input_image).unsqueeze(0)

            # PREDICTION
            input_image = input_image.to(device)
            features = encoder(input_image)
            outputs = depth_decoder(features)

            disp = outputs[("disp", 0)]
            disp_resized = torch.nn.functional.interpolate(
                disp, (original_height, original_width), mode="bilinear", align_corners=False)

            # # Saving numpy file
            # output_name = os.path.splitext(os.path.basename(image_path))[0]
            # scaled_disp, depth = disp_to_depth(disp, 0.1, 100)
            
            # name_dest_npy = os.path.join(output_directory, "{}_disp.npy".format(output_name))
            # np.save(name_dest_npy, scaled_disp.cpu().numpy())

            # # Saving colormapped depth image
            disp_resized_np = disp_resized.squeeze().cpu().numpy()
            # vmax = np.percentile(disp_resized_np, 95)
            # normalizer = mpl.colors.Normalize(vmin=disp_resized_np.min(), vmax=vmax)
            # mapper = cm.ScalarMappable(norm=normalizer, cmap='magma')
            # colormapped_im = (mapper.to_rgba(disp_resized_np)[:, :, :3] * 255).astype(np.uint8)
            # im = pil.fromarray(colormapped_im)

            # name_dest_im = os.path.join(output_directory, "{}_disp.jpeg".format(output_name))
            # im.save(name_dest_im)

            # print("   Processed {:d} of {:d} images - saved predictions to:".format(
            #     idx + 1, len(paths)))
            # print("   - {}".format(name_dest_im))
            # print("   - {}".format(name_dest_npy))
            results.append(disp_resized_np)
    print('-> Done!')
    
    return results


def run_single_image(image):
    
    """Function to predict for a single image or folder of images
    """
    model_name = "mono_640x192"
 
    if torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")

  
    download_model_if_doesnt_exist(model_name)
    model_path = os.path.join("models", model_name)
    print("-> Loading model from ", model_path)
    encoder_path = os.path.join(model_path, "encoder.pth")
    depth_decoder_path = os.path.join(model_path, "depth.pth")

    # LOADING PRETRAINED MODEL
    print("   Loading pretrained encoder")
    encoder = networks.ResnetEncoder(18, False)
    loaded_dict_enc = torch.load(encoder_path, map_location=device)

    # extract the height and width of image that this model was trained with
    feed_height = loaded_dict_enc['height']
    feed_width = loaded_dict_enc['width']
    filtered_dict_enc = {k: v for k, v in loaded_dict_enc.items() if k in encoder.state_dict()}
    encoder.load_state_dict(filtered_dict_enc)
    encoder.to(device)
    encoder.eval()

    print("   Loading pretrained decoder")
    depth_decoder = networks.DepthDecoder(
        num_ch_enc=encoder.num_ch_enc, scales=range(4))

    loaded_dict = torch.load(depth_decoder_path, map_location=device)
    depth_decoder.load_state_dict(loaded_dict)

    depth_decoder.to(device)
    depth_decoder.eval()

    # FINDING INPUT IMAGES
    # if os.path.isfile(image_path):
    #     # Only testing on a single image
    #     paths = [image_path]
    #     output_directory = os.path.dirname(image_path)
    # elif os.path.isdir(image_path):
    #     # Searching folder for images
    #     paths = glob.glob(os.path.join(image_path, '*.{}'.format("jpg")))
    #     output_directory = image_path
    # else:
    #     raise Exception("Can not find image_path: {}".format(image_path))

    # print("-> Predicting on {:d} test images".format(len(paths)))

    # PREDICTING ON EACH IMAGE IN TURN
    with torch.no_grad():
        # Load image and preprocess

        img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        input_image = pil.fromarray(img)
        original_width, original_height = input_image.size
        input_image = input_image.resize((feed_width, feed_height), pil.LANCZOS)
        input_image = transforms.ToTensor()(input_image).unsqueeze(0)

        # PREDICTION
        input_image = input_image.to(device)
        features = encoder(input_image)
        outputs = depth_decoder(features)

        disp = outputs[("disp", 0)]
        disp_resized = torch.nn.functional.interpolate(
            disp, (original_height, original_width), mode="bilinear", align_corners=False)

        # # Saving numpy file
        # output_name = os.path.splitext(os.path.basename(image_path))[0]
        # scaled_disp, depth = disp_to_depth(disp, 0.1, 100)
        
        # name_dest_npy = os.path.join(output_directory, "{}_disp.npy".format(output_name))
        # np.save(name_dest_npy, scaled_disp.cpu().numpy())

        # # Saving colormapped depth image
        disp_resized_np = disp_resized.squeeze().cpu().numpy()
        # vmax = np.percentile(disp_resized_np, 95)
        # normalizer = mpl.colors.Normalize(vmin=disp_resized_np.min(), vmax=vmax)
        # mapper = cm.ScalarMappable(norm=normalizer, cmap='magma')
        # colormapped_im = (mapper.to_rgba(disp_resized_np)[:, :, :3] * 255).astype(np.uint8)
        # im = pil.fromarray(colormapped_im)

        # name_dest_im = os.path.join(output_directory, "{}_disp.jpeg".format(output_name))
        # im.save(name_dest_im)

        # print("   Processed {:d} of {:d} images - saved predictions to:".format(
        #     idx + 1, len(paths)))
        # print("   - {}".format(name_dest_im))
        # print("   - {}".format(name_dest_npy))
        print('-> Done!')
        
    return disp_resized_np