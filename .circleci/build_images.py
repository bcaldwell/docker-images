#!/usr/bin/env python3

import yaml
import os
import sys
import subprocess


def main():
    images_file = "./images.yaml"

    try:
        images = yaml.load(open(images_file).read(), Loader=yaml.FullLoader)
    except Exception as e:
        print("failed to laod and parse yaml file", e)
        return

    run_type = sys.argv[1]
    print("running in {} mode".format(run_type))

    for k, v in images.items():
        image = {
            "name": k
        }

        if isinstance(v, dict):
            if "path" not in v:
                print("not path property found for image ", k)
            image["path"] = v["path"]
            image["version"] = v["version"] if "version" in v else "latest"
        elif isinstance(v, str):
            image["path"] = v
            image["version"] = "latest"
        else:
            print(v, "is an unsupported type")

        if run_type == "build":
            build_image(image)
        elif run_type == "combine":
            combine_image(image)
        else:
            print("invalid run_type")


def combine_image(image):
    changed = any_changed(image["path"])
    if not changed:
        print("no changes in", image["name"], image["path"])
        return

    commit_sha = sha()

    e = os_run("ci-scripts docker/combine_and_push_image --docker.images.dockerRepo {} --docker.tags \"{}, _sha, latest\" --docker.combine.amend_tags \"{}-arm64,{}-amd64\"".format(
        image["name"], image["version"], commit_sha, commit_sha))
    if e != 0:
        exit(1)

    print()

def build_image(image):
    changed = any_changed(image["path"])
    if not changed:
        print("no changes in", image["name"], image["path"])
        return
    
    arch = sys.argv[2]

    e = os_run("ci-scripts docker/build_and_push_image --docker.images.dockerRepo {} --docker.images.folder {} --docker.tags \"{}-{}\" --docker.image.platform \"linux/{}\"".format(
        image["name"], image["path"], sha(), arch, arch))
    if e != 0:
        exit(1)
    print()

def any_changed(path):
    changed = os_run(
        "ci-scripts git/files_changed --git.files_changed.prefix {}".format(path))       

    return changed == 0

def sha():
    sha = subprocess.run(["git", "rev-parse", "HEAD"], stdout=subprocess.PIPE).stdout.decode('utf-8')

    if sha == "":
        print("unable to detect sha")
        exit(1)

    return sha.strip()

def os_run(cmd):
    print(cmd)
    return os.system(cmd)


main()
