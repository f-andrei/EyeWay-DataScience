


def get_elements():
    return {
            "streammux": ("nvstreammux", "Stream-muxer"),
            "pgie": ("nvinfer", "primary-inference"),
            "nvvidconv": ("nvvideoconvert", "convertor"),
            "filter1": ("capsfilter", "filter1"),
            "nvtracker": ("nvtracker", "tracker"),
            "nvdsanalytics": ("nvdsanalytics", "analytics"),
            "nvtiler": ("nvmultistreamtiler", "nvtiler"),
            "nvvidconv2": ("nvvideoconvert", "convertor2"),
            "nvosd": ("nvdsosd", "onscreendisplay")
        }