def get_elements(stream_output):
    elements ={
            "streammux": ("nvstreammux", "Stream-muxer"),
            "pgie": ("nvinfer", "primary-inference"),
            "nvtracker": ("nvtracker", "tracker"),
            "nvdsanalytics": ("nvdsanalytics", "analytics"),
            "nvvidconv_analytics": ("nvvideoconvert", "convertor1"),
            "filter_analytics": ("capsfilter", "filter_analytics"),
            "queue": ("queue", "queue")
        }


    if stream_output == "none":
        elements["sink"] = ("fakesink", "fakesink")

    if stream_output in ("file", "rtsp", "display"):
        elements["nvtiler"] = ("nvmultistreamtiler", "nvtiler")
        elements["nvvidconv"] = ("nvvideoconvert", "convertor")
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
    