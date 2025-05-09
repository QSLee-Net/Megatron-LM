# Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.
import argparse
import json

from .evaluate_mmmu import get_input_output_paths
from pycocoevalcap.eval import COCOEvalCap
from pycocotools.coco import COCO


def convert_to_coco_format(input_path):
    """Convert input files to COCO compatible format."""
    input_file_paths, output_file_path = get_input_output_paths(input_path, task="captioning")

    results = dict()

    for input_file_path in input_file_paths:
        with open(input_file_path, "r") as input_file:
            for line in input_file:
                res = json.loads(line)
                sample_id = res["sample_id"]

                # Ignore possible duplicates.
                if sample_id in results:
                    continue

                caption = res["caption"].rstrip(".").lower()
                results[sample_id] = {
                    "image_id": sample_id,
                    "caption": caption,
                }

    results = list(results.values())

    with open(output_file_path, "w") as output_file:
        json.dump(results, output_file, indent=4, sort_keys=True)

    return output_file_path


def coco_captioning_eval(input_path, groundtruth_file):
    """Run COCO captioning evaluation."""
    coco = COCO(groundtruth_file)
    input_file = convert_to_coco_format(input_path)
    coco_result = coco.loadRes(input_file)

    coco_eval = COCOEvalCap(coco, coco_result)

    # Evaluate on the input subset of images.
    coco_eval.params["image_id"] = coco_result.getImgIds()

    coco_eval.evaluate()

    print("========== COCO captioning scores ==========")
    for metric, score in coco_eval.eval.items():
        print(f"{metric} {score * 100:.3f}")

    return coco_eval.eval['CIDEr']

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-path", type=str, required=True, help="Path to input file(s)")
    parser.add_argument(
        "--groundtruth-path", type=str, required=True, help="Path to groundtruth file"
    )
    args = parser.parse_args()

    coco_captioning_eval(args.input_path, args.groundtruth_path)
