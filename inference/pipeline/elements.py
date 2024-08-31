


def get_elements():
    return {
            "streammux": ("nvstreammux", "Stream-muxer"),
            "nvmultiurisrcbin": ("nvmultiurisrcbin", "multi-source-bin"),
            "nvdspreprocess": ("nvdspreprocess", "preprocess-plugin"),
            "pgie": ("nvinfer", "primary-inference"),
            "nvvidconv": ("nvvideoconvert", "convertor"),
            "filter1": ("capsfilter", "filter1"),
            "nvtracker": ("nvtracker", "tracker"),
            "nvdsanalytics": ("nvdsanalytics", "analytics"),
            "nvtiler": ("nvmultistreamtiler", "nvtiler"),
            "nvvidconv2": ("nvvideoconvert", "convertor2"),
            "nvosd": ("nvdsosd", "onscreendisplay")
        }