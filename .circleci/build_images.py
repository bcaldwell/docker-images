#!/usr/bin/env python3

import yaml
import os

def main():
    images_file = "./images.yaml"

    try:
        images = yaml.load(open(images_file).read(), Loader=yaml.FullLoader)
    except Exception as e:
        print("failed to laod and parse yaml file", e)
        return

    for k, v in images.items():
        image = {
            "name": k
        }

        if isinstance(v,dict):
            if "path" not in v:
                print("not path property found for image ", k)
            image["path"] = v["path"]
            image["version"] = v["version"] if "version" in v else "latest"
        elif isinstance(v, str):
            image["path"] = v
            image["version"] = "latest"
        else:
            print(v, "is an unsupported type")

        build_image(image)

def build_image(image):
    changed = os_run("ci-scripts git/files_changed --git.files_changed.prefix {}".format(image["path"]))
    if changed != 0:
        print("no changes in", image["name"], image["path"])
        return

    os_run("ci-scripts docker/build_and_push_image --docker.images.dockerRepo {} --docker.images.folder {} --docker.tags \"{}, _sha, latest\"".format(image["name"], image["path"], image["version"]))
    print()

def os_run(cmd):
    print(cmd)
    return os.system(cmd)

main()
