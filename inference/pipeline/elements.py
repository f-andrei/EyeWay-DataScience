


def get_elements(stream_output):
    elements ={
            "streammux": ("nvstreammux", "Stream-muxer"),
            "pgie": ("nvinfer", "primary-inference"),
            "nvvidconv": ("nvvideoconvert", "convertor"),
            "filter1": ("capsfilter", "filter1"),
            "nvtracker": ("nvtracker", "tracker"),
            "nvdsanalytics": ("nvdsanalytics", "analytics"),
            "nvvidconv2": ("nvvideoconvert", "convertor2"),
        }


    if stream_output == "none":
        elements["sink"] = ("fakesink", "fakesink")

    if stream_output in ("file", "rtsp", "display"):
        elements["nvvidconv_tiler"] = ("nvvideoconvert", "nvvidconv_tiler")
        elements["filter_tiler"] = ("capsfilter", "filter_tiler")
        elements["nvtiler"] = ("nvmultistreamtiler", "nvtiler")
        elements["nvosd"] = ("nvdsosd", "onscreendisplay")
        if stream_output in ("file","rtsp"):
            elements["nvvidconv_encoder"] = ("nvvideoconvert", "nvvidconv_encoder")
            elements["filter_encoder"] = ("capsfilter", "filter_encoder")
            elements["encoder"] = ("nvv4l2h264enc", "encoder")
            elements["codeparser"] = ("h264parse", "h264-parser2")
            if stream_output  == "file":
                elements["container"] = ("matroskamux", "muxer")
                elements["sink"] = ("filesink", "file-sink")
            if stream_output  == "rtsp":
                elements["rtppay"] = ("rtph264pay", "rtppay")
                elements["sink"] = ("udpsink", "udpsink")
        else:
            elements["sink"] = ("nveglglessink", "nvvideo-renderer")

    return elements
    